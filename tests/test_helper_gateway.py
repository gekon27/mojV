from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "helper_gateway.py"


def _load():
    assert MODULE.exists(), "helper_gateway.py must implement Supervisor discovery"
    spec = importlib.util.spec_from_file_location("mojv_helper_gateway_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, status: int, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def json(self, content_type=None):
        return self._payload

    async def text(self):
        return str(self._payload)


class _Session:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/addons"):
            return _Response(
                200,
                {"data": {"addons": [{"slug": "abc_mojv_auth_helper", "installed": "0.1.0"}]}},
            )
        if url.endswith("/addons/abc_mojv_auth_helper/info"):
            return _Response(
                200,
                {"data": {"hostname": "abc-mojv-auth-helper", "state": "started"}},
            )
        if url.endswith("/health"):
            return _Response(200, {"status": "ok", "version": "0.1.0"})
        raise AssertionError(url)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if url.endswith("/v1/account"):
            return _Response(
                200,
                {"students": [{"student_id": "1", "name": "Jan", "class_name": "5A"}]},
            )
        if url.endswith("/v1/snapshot"):
            return _Response(
                200,
                {
                    "students": [
                        {
                            "student_id": "1",
                            "name": "Jan",
                            "class_name": "5A",
                            "timetable": [],
                            "attendance": [],
                            "errors": {},
                        }
                    ]
                },
            )
        raise AssertionError(url)


class _VerificationFailureSession(_Session):
    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return _Response(503, {"error": "browser_verification_failed"})


def test_gateway_discovers_running_helper_and_reads_account() -> None:
    helper = _load()

    async def run():
        session = _Session()
        gateway = helper.HelperGateway(session, supervisor_token="token")
        students = await gateway.async_account("alias", "secret")
        assert students == ({"student_id": "1", "name": "Jan", "class_name": "5A"},)
        assert any(call[1].endswith("/addons/abc_mojv_auth_helper/info") for call in session.calls)

    asyncio.run(run())


def test_gateway_validates_snapshot_contract() -> None:
    helper = _load()

    async def run():
        gateway = helper.HelperGateway(_Session(), supervisor_token="token")
        snapshot = await gateway.async_snapshot("alias", "secret")
        assert snapshot["students"][0]["name"] == "Jan"

    asyncio.run(run())


def test_gateway_requires_supervisor_token() -> None:
    helper = _load()

    async def run():
        gateway = helper.HelperGateway(_Session(), supervisor_token="")
        with pytest.raises(helper.HelperUnavailable):
            await gateway.async_health()

    asyncio.run(run())


def test_browser_verification_failure_is_not_reported_as_missing_helper() -> None:
    helper = _load()

    async def run():
        gateway = helper.HelperGateway(_VerificationFailureSession(), supervisor_token="token")
        with pytest.raises(helper.HelperRequestError):
            await gateway.async_account("alias", "secret")

    asyncio.run(run())
