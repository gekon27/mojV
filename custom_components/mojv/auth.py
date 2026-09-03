"""Authentication and student discovery for mojV.

This module intentionally keeps browser-dependent concerns outside the Home
Assistant entity layer. It first attempts a lightweight two-step HTML login
using a dedicated cookie session. If the portal requires browser-side robot
verification, a dedicated exception is raised so the UI can report that
cleanly instead of treating it as invalid credentials.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import json
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp

_LOGGER = logging.getLogger(__name__)

_PORTAL_ROOT = "https://edu" + "vulcan.pl"
_STUDENT_ROOT = "https://uczen." + "edu" + "vulcan.pl"
_LOGIN_URL = f"{_PORTAL_ROOT}/logowanie"

_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.7",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0 Safari/537.36"
    ),
}

_LOGIN_FIELDS = ("UserName", "username", "Login", "login", "email", "Email")
_PASSWORD_FIELDS = ("Password", "password", "Haslo", "haslo")


class MojVAuthError(Exception):
    """Base authentication error."""


class MojVCannotConnect(MojVAuthError):
    """The portal could not be reached or returned an invalid response."""


class MojVInvalidAuth(MojVAuthError):
    """Credentials were rejected."""


class MojVBrowserVerificationRequired(MojVAuthError):
    """Browser-side verification is required before login can complete."""


class MojVNoStudents(MojVAuthError):
    """Login succeeded but no student context was discovered."""


@dataclass(frozen=True, slots=True)
class StudentTarget:
    """Connection information for one student diary."""

    student_id: str
    name: str
    class_name: str
    base_url: str
    key: str
    diary_id: str = ""


@dataclass(slots=True)
class _Form:
    action: str
    method: str
    values: dict[str, str]
    types: dict[str, str]


class _PageParser(HTMLParser):
    """Small HTML parser sufficient for login forms and diary links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[_Form] = []
        self.links: list[str] = []
        self._form: _Form | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: (value or "") for key, value in attrs}
        if tag == "form":
            self._form = _Form(
                action=values.get("action", ""),
                method=values.get("method", "post").lower(),
                values={},
                types={},
            )
            self.forms.append(self._form)
            return
        if tag == "input" and self._form is not None:
            name = values.get("name", "")
            if name:
                self._form.values[name] = values.get("value", "")
                self._form.types[name] = values.get("type", "text").lower()
            return
        if tag == "a":
            href = values.get("href", "").strip()
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._form = None


def _parse_page(html: str) -> _PageParser:
    parser = _PageParser()
    parser.feed(html)
    return parser


def _find_form(parser: _PageParser, fields: tuple[str, ...]) -> tuple[_Form, str] | None:
    for form in parser.forms:
        for field in fields:
            if field in form.values:
                return form, field
    return None


def _looks_like_browser_challenge(html: str) -> bool:
    lower = html.lower()
    markers = (
        "zabezpieczenie przed robotami",
        "robot verification",
        "captcha",
        "turnstile",
        "cf-chl-",
    )
    return any(marker in lower for marker in markers)


def _looks_like_invalid_auth(html: str) -> bool:
    lower = html.lower()
    markers = (
        "nieprawidłowe hasło",
        "nieprawidlowe haslo",
        "błędne hasło",
        "bledne haslo",
        "nieprawidłowy login",
        "nieprawidlowy login",
    )
    return any(marker in lower for marker in markers)


async def _request_text(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    data: dict[str, str] | None = None,
) -> tuple[str, str]:
    try:
        async with session.request(
            method.upper(),
            url,
            data=data,
            allow_redirects=True,
            headers=_DEFAULT_HEADERS,
        ) as response:
            text = await response.text(errors="replace")
            if response.status >= 500:
                raise MojVCannotConnect(f"Portal returned HTTP {response.status}")
            if response.status in (401, 403):
                if _looks_like_browser_challenge(text):
                    raise MojVBrowserVerificationRequired
                raise MojVInvalidAuth
            return str(response.url), text
    except MojVAuthError:
        raise
    except (aiohttp.ClientError, TimeoutError) as err:
        raise MojVCannotConnect(str(err)) from err


async def _submit_field(
    session: aiohttp.ClientSession,
    page_url: str,
    html: str,
    fields: tuple[str, ...],
    value: str,
) -> tuple[str, str]:
    parser = _parse_page(html)
    found = _find_form(parser, fields)
    if found is None:
        if _looks_like_browser_challenge(html):
            raise MojVBrowserVerificationRequired
        raise MojVCannotConnect("Expected login form was not found")

    form, field = found
    payload = dict(form.values)
    payload[field] = value
    action = urljoin(page_url, form.action or page_url)
    method = "get" if form.method == "get" else "post"

    if method == "get":
        try:
            async with session.get(
                action,
                params=payload,
                allow_redirects=True,
                headers=_DEFAULT_HEADERS,
            ) as response:
                return str(response.url), await response.text(errors="replace")
        except aiohttp.ClientError as err:
            raise MojVCannotConnect(str(err)) from err

    return await _request_text(session, "post", action, data=payload)


def _candidate_diary_links(page_url: str, html: str) -> list[str]:
    parser = _parse_page(html)
    result: list[str] = []
    for href in parser.links:
        absolute = urljoin(page_url, href)
        lower = absolute.lower()
        if "dziennik" in lower or "uczen." in lower:
            if absolute not in result:
                result.append(absolute)
    if "uczen." in page_url.lower() and page_url not in result:
        result.append(page_url)
    return result


def _city_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.netloc.lower().startswith("uczen."):
        return None
    parts = [part for part in parsed.path.split("/") if part]
    return parts[0] if parts else None


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        value = payload.get("uczniowie")
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _target_from_row(city: str, row: dict[str, Any]) -> StudentTarget | None:
    key = str(row.get("key") or "").strip()
    diary_id = str(row.get("idDziennik") or "").strip()
    name = str(row.get("uczen") or row.get("nazwa") or "").strip()
    if not key or not name:
        return None

    class_name = str(row.get("oddzial") or row.get("klasa") or "").strip()
    raw_id = row.get("idUczen") or row.get("idUcznia") or row.get("id")
    fallback = f"{city}:{diary_id or class_name}:{name}"
    student_id = str(raw_id or fallback)
    return StudentTarget(
        student_id=student_id,
        name=name,
        class_name=class_name,
        base_url=f"{_STUDENT_ROOT}/{city}",
        key=key,
        diary_id=diary_id,
    )


async def async_login(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
) -> tuple[StudentTarget, ...]:
    """Log in and discover every student available to the account."""
    page_url, html = await _request_text(session, "get", _LOGIN_URL)

    page_url, html = await _submit_field(
        session,
        page_url,
        html,
        _LOGIN_FIELDS,
        username.strip(),
    )
    page_url, html = await _submit_field(
        session,
        page_url,
        html,
        _PASSWORD_FIELDS,
        password,
    )

    if _looks_like_invalid_auth(html):
        raise MojVInvalidAuth

    links = _candidate_diary_links(page_url, html)
    if not links:
        if _looks_like_browser_challenge(html):
            raise MojVBrowserVerificationRequired
        raise MojVCannotConnect("Login completed but no diary link was discovered")

    targets: dict[str, StudentTarget] = {}
    discovered_rows = 0
    observed_fields: set[str] = set()

    for link in links:
        final_url, _ = await _request_text(session, "get", link)
        city = _city_from_url(final_url)
        if not city:
            continue
        context_url = f"{_STUDENT_ROOT}/{city}/api/Context"
        try:
            async with session.get(
                context_url,
                headers={**_DEFAULT_HEADERS, "Accept": "application/json"},
            ) as response:
                raw = await response.text(errors="replace")
                if response.status in (401, 403):
                    raise MojVInvalidAuth
                if response.status >= 400:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    if _looks_like_browser_challenge(raw):
                        raise MojVBrowserVerificationRequired
                    continue
        except MojVAuthError:
            raise
        except aiohttp.ClientError as err:
            raise MojVCannotConnect(str(err)) from err

        rows = _records(payload)
        discovered_rows += len(rows)
        for row in rows:
            observed_fields.update(str(field) for field in row)
            target = _target_from_row(city, row)
            if target is not None:
                targets.setdefault(target.student_id, target)

    if not targets:
        _LOGGER.warning(
            "Student discovery returned no usable records: rows=%d fields=%s",
            discovered_rows,
            sorted(observed_fields),
        )
        raise MojVNoStudents
    return tuple(targets.values())


def create_session() -> aiohttp.ClientSession:
    """Create an isolated cookie session for one configured account."""
    timeout = aiohttp.ClientTimeout(total=40, connect=12)
    return aiohttp.ClientSession(
        timeout=timeout,
        cookie_jar=aiohttp.CookieJar(),
        raise_for_status=False,
    )
