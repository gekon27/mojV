"""Gateway from Home Assistant Core to the local mojV auth helper."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

import aiohttp

try:
    from .helper_protocol import select_helper_slug, unwrap_supervisor, validate_snapshot
except ImportError:  # pragma: no cover - supports dependency-light unit loading
    _path = Path(__file__).with_name("helper_protocol.py")
    _spec = importlib.util.spec_from_file_location("mojv_helper_protocol_runtime", _path)
    assert _spec is not None and _spec.loader is not None
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    select_helper_slug = _module.select_helper_slug
    unwrap_supervisor = _module.unwrap_supervisor
    validate_snapshot = _module.validate_snapshot


class HelperError(Exception):
    """Base helper communication error."""


class HelperUnavailable(HelperError):
    """The local browser helper is not installed, running or reachable."""


class HelperInvalidAuth(HelperError):
    """Credentials were rejected by the browser helper."""


class HelperRequestError(HelperError):
    """The helper returned an invalid or failed request."""


class HelperGateway:
    """Discover the helper through Supervisor and call its private HTTP API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        supervisor_token: str | None = None,
        supervisor_host: str | None = None,
    ) -> None:
        self._session = session
        self._supervisor_token = (
            supervisor_token
            if supervisor_token is not None
            else os.getenv("SUPERVISOR_TOKEN", "")
        )
        host = (
            supervisor_host
            if supervisor_host is not None
            else os.getenv("SUPERVISOR", "supervisor")
        )
        if host.startswith("http://") or host.startswith("https://"):
            self._supervisor_url = host.rstrip("/")
        else:
            self._supervisor_url = f"http://{host.rstrip('/')}"
        self._helper_url: str | None = None

    @property
    def helper_url(self) -> str | None:
        """Resolved internal helper URL, if discovery already succeeded."""
        return self._helper_url

    def _supervisor_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._supervisor_token}",
            "Accept": "application/json",
        }

    async def _supervisor_get(self, path: str) -> Any:
        if not self._supervisor_token:
            raise HelperUnavailable("Supervisor access is not available")
        url = f"{self._supervisor_url}{path}"
        try:
            async with self._session.get(url, headers=self._supervisor_headers()) as response:
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    raise HelperUnavailable(f"Supervisor returned HTTP {response.status}")
                return payload
        except HelperError:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise HelperUnavailable(str(err)) from err

    async def _discover(self) -> str:
        if self._helper_url:
            return self._helper_url

        addons_payload = await self._supervisor_get("/addons")
        slug = select_helper_slug(addons_payload)
        if not slug:
            raise HelperUnavailable("mojV Auth Helper is not installed")

        info_payload = await self._supervisor_get(f"/addons/{slug}/info")
        info = unwrap_supervisor(info_payload)
        if not isinstance(info, dict):
            raise HelperUnavailable("Invalid helper info returned by Supervisor")
        state = str(info.get("state") or "").lower()
        if state not in {"started", "running"}:
            raise HelperUnavailable("mojV Auth Helper is not running")
        hostname = str(info.get("hostname") or "").strip()
        ip_address = str(info.get("ip_address") or "").strip()
        host = hostname or ip_address
        if not host:
            raise HelperUnavailable("Supervisor did not provide helper network address")
        self._helper_url = f"http://{host}:8099"
        return self._helper_url

    async def _helper_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        base = await self._discover()
        url = f"{base}{path}"
        try:
            requester = self._session.get if method == "GET" else self._session.post
            kwargs: dict[str, Any] = {"headers": {"Accept": "application/json"}}
            if payload is not None:
                kwargs["json"] = payload
            async with requester(url, **kwargs) as response:
                body = await response.json(content_type=None)
                error_code = (
                    str(body.get("error") or "") if isinstance(body, dict) else ""
                )
                if response.status == 401:
                    raise HelperInvalidAuth("Invalid credentials")
                if error_code in {
                    "browser_verification_failed",
                    "browser_error",
                    "no_students",
                }:
                    raise HelperRequestError(error_code)
                if response.status in {404, 503}:
                    raise HelperUnavailable(str(body))
                if response.status >= 400:
                    raise HelperRequestError(
                        error_code or f"Helper returned HTTP {response.status}"
                    )
                return body
        except HelperError:
            raise
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            self._helper_url = None
            raise HelperUnavailable(str(err)) from err

    async def async_health(self) -> dict[str, Any]:
        """Check that the helper is installed and serving requests."""
        payload = await self._helper_json("GET", "/health")
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            raise HelperUnavailable("Helper health check failed")
        return payload

    async def async_account(self, username: str, password: str) -> tuple[dict[str, Any], ...]:
        """Use the browser helper to validate credentials and discover students."""
        payload = await self._helper_json(
            "POST",
            "/v1/account",
            payload={"username": username, "password": password},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("students"), list):
            raise HelperRequestError("Helper returned an invalid account payload")
        students: list[dict[str, Any]] = []
        for row in payload["students"]:
            if not isinstance(row, dict):
                continue
            if not str(row.get("student_id") or "") or not str(row.get("name") or ""):
                continue
            public_row = {
                "student_id": str(row["student_id"]),
                "name": str(row["name"]),
                "class_name": str(row.get("class_name") or ""),
            }
            students.append(public_row)
        if not students:
            raise HelperRequestError("Helper did not discover any students")
        return tuple(students)

    async def async_snapshot(self, username: str, password: str) -> dict[str, Any]:
        """Fetch plan and attendance through the browser-backed helper."""
        payload = await self._helper_json(
            "POST",
            "/v1/snapshot",
            payload={"username": username, "password": password},
        )
        if not validate_snapshot(payload):
            raise HelperRequestError("Helper returned an invalid snapshot")
        return payload
