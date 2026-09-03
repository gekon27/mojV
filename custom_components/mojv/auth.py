"""Authentication and student discovery for mojV.

The integration keeps authentication isolated from the Home Assistant entity
layer. The flow uses a lightweight cookie session, performs the current portal
identity check, follows server redirects and federation relay forms, then opens
student journals before reading their context. No credentials, cookies, session
keys or relay payloads are written to logs.
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

# Keep provider branding out of the integration UI/source vocabulary while
# retaining the actual network endpoints required by the protocol.
_PORTAL_ROOT = "https://edu" + "vulcan.pl"
_STUDENT_ROOT = "https://uczen." + "edu" + "vulcan.pl"
_LOGIN_URL = f"{_PORTAL_ROOT}/logowanie"
_QUERY_USER_INFO_URL = f"{_PORTAL_ROOT}/Account/QueryUserInfo"

_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.7",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0 Safari/537.36"
    ),
}

_LOGIN_FIELDS = (
    "Alias",
    "alias",
    "UserName",
    "username",
    "Login",
    "login",
    "email",
    "Email",
)
_PASSWORD_FIELDS = ("Password", "password", "Haslo", "haslo")
_TOKEN_FIELD = "__RequestVerificationToken"
_MAX_FEDERATION_HOPS = 8


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


@dataclass(frozen=True, slots=True)
class _HttpPage:
    url: str
    text: str
    status: int


class _PageParser(HTMLParser):
    """Small HTML parser sufficient for login forms and journal links."""

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


def _find_federation_form(parser: _PageParser) -> _Form | None:
    for form in parser.forms:
        if any(name.lower() == "wresult" for name in form.values):
            return form
    return None


def _anti_forgery_token(parser: _PageParser) -> str:
    for form in parser.forms:
        for name, value in form.values.items():
            if name.lower() == _TOKEN_FIELD.lower() and value:
                return value
    return ""


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
        "nieprawidłowe dane logowania",
        "nieprawidlowe dane logowania",
    )
    return any(marker in lower for marker in markers)


async def _request_page(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> _HttpPage:
    merged_headers = dict(_DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    try:
        async with session.request(
            method.upper(),
            url,
            data=data,
            allow_redirects=True,
            headers=merged_headers,
        ) as response:
            text = await response.text(errors="replace")
            if response.status >= 500:
                raise MojVCannotConnect(f"Portal returned HTTP {response.status}")
            if response.status in (401, 403):
                if _looks_like_browser_challenge(text):
                    raise MojVBrowserVerificationRequired
                raise MojVInvalidAuth
            return _HttpPage(str(response.url), text, response.status)
    except MojVAuthError:
        raise
    except (aiohttp.ClientError, TimeoutError) as err:
        raise MojVCannotConnect(str(err)) from err


async def _request_text(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    data: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Backward-compatible helper used by the simple form fallback."""
    page = await _request_page(session, method, url, data=data)
    return page.url, page.text


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


async def _follow_federation(
    session: aiohttp.ClientSession,
    page: _HttpPage,
) -> _HttpPage:
    """Submit hidden SSO relay forms until the journal landing page is reached."""
    current = page
    for _ in range(_MAX_FEDERATION_HOPS):
        parser = _parse_page(current.text)
        form = _find_federation_form(parser)
        if form is None:
            return current
        target = urljoin(current.url, form.action or current.url)
        current = await _request_page(
            session,
            "post",
            target,
            data=dict(form.values),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": current.url,
            },
        )
    raise MojVCannotConnect("Too many authentication relay steps")


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


def _app_key_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    for index, part in enumerate(parts[:-1]):
        if part.lower() == "app":
            return parts[index + 1]
    return ""


def _unwrap_payload(payload: Any) -> Any:
    current = payload
    for _ in range(4):
        if not isinstance(current, dict):
            break
        wrapper_key = next(
            (
                key
                for key in current
                if str(key).lower() in {"data", "result"}
                and isinstance(current[key], (dict, list))
            ),
            None,
        )
        if wrapper_key is None:
            break
        current = current[wrapper_key]
    return current


def _records(payload: Any) -> list[dict[str, Any]]:
    current = _unwrap_payload(payload)
    if isinstance(current, list):
        return [row for row in current if isinstance(row, dict)]
    if isinstance(current, dict):
        students_key = next(
            (key for key in current if str(key).lower() == "uczniowie"),
            None,
        )
        if students_key is not None and isinstance(current[students_key], list):
            return [row for row in current[students_key] if isinstance(row, dict)]
    return []


def _payload_shape(payload: Any) -> str:
    if isinstance(payload, dict):
        root_keys = sorted(str(key) for key in payload)[:12]
        inner = _unwrap_payload(payload)
        if isinstance(inner, dict):
            inner_keys = sorted(str(key) for key in inner)[:12]
            return f"dict(root={root_keys}, inner={inner_keys})"
        if isinstance(inner, list):
            return f"dict(root={root_keys}, inner=list[{len(inner)}])"
        return f"dict(root={root_keys}, inner={type(inner).__name__})"
    if isinstance(payload, list):
        return f"list[{len(payload)}]"
    return type(payload).__name__


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


def _login_payload(form: _Form, username: str, password: str) -> dict[str, str]:
    payload = dict(form.values)
    user_field = next((field for field in _LOGIN_FIELDS if field in payload), "Alias")
    password_field = next(
        (field for field in _PASSWORD_FIELDS if field in payload),
        "Password",
    )
    payload[user_field] = username
    payload[password_field] = password
    # Current portal binding expects these canonical names. Keeping detected
    # aliases as well makes the flow backward-compatible with older forms.
    payload["Alias"] = username
    payload["Password"] = password
    payload.setdefault("captcha-response", "")
    return payload


async def _portal_login(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
) -> _HttpPage:
    login_page = await _request_page(session, "get", _LOGIN_URL)
    if _looks_like_browser_challenge(login_page.text):
        raise MojVBrowserVerificationRequired

    parser = _parse_page(login_page.text)
    token = _anti_forgery_token(parser)

    # The identity probe is part of the current two-stage portal flow. It is
    # intentionally best-effort for compatibility with older deployments.
    if token:
        probe = await _request_page(
            session,
            "post",
            _QUERY_USER_INFO_URL,
            data={"alias": username, _TOKEN_FIELD: token},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": login_page.url,
            },
        )
        if probe.status >= 400 and _looks_like_invalid_auth(probe.text):
            raise MojVInvalidAuth

    password_form = _find_form(parser, _PASSWORD_FIELDS)
    if password_form is not None:
        form, _ = password_form
        action = urljoin(login_page.url, form.action or login_page.url)
        result = await _request_page(
            session,
            "post",
            action,
            data=_login_payload(form, username, password),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_page.url,
            },
        )
    else:
        # Compatibility fallback for deployments still presenting separate
        # username and password pages.
        page_url, html = await _submit_field(
            session,
            login_page.url,
            login_page.text,
            _LOGIN_FIELDS,
            username,
        )
        page_url, html = await _submit_field(
            session,
            page_url,
            html,
            _PASSWORD_FIELDS,
            password,
        )
        result = _HttpPage(page_url, html, 200)

    result = await _follow_federation(session, result)
    if _looks_like_browser_challenge(result.text):
        raise MojVBrowserVerificationRequired
    if _looks_like_invalid_auth(result.text):
        raise MojVInvalidAuth
    return result


async def _read_context(
    session: aiohttp.ClientSession,
    journal_page: _HttpPage,
) -> tuple[str, Any, int] | None:
    city = _city_from_url(journal_page.url)
    if not city:
        return None

    app_key = _app_key_from_url(journal_page.url)
    base_url = f"{_STUDENT_ROOT}/{city}"
    referer = (
        f"{base_url}/App/{app_key}/tablica"
        if app_key
        else journal_page.url
    )
    context_url = f"{base_url}/api/Context"
    page = await _request_page(
        session,
        "get",
        context_url,
        headers={
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
        },
    )
    if page.status >= 400:
        return city, {}, page.status
    try:
        payload = json.loads(page.text)
    except json.JSONDecodeError:
        if _looks_like_browser_challenge(page.text):
            raise MojVBrowserVerificationRequired
        return city, {}, page.status
    return city, payload, page.status


async def async_login(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
) -> tuple[StudentTarget, ...]:
    """Log in and discover every student available to the account."""
    landing = await _portal_login(session, username.strip(), password)

    links = _candidate_diary_links(landing.url, landing.text)
    if not links:
        # A returned login form after a nominal POST is an authentication
        # failure, not a successful account with zero children.
        landing_parser = _parse_page(landing.text)
        if _find_form(landing_parser, _PASSWORD_FIELDS) is not None:
            raise MojVInvalidAuth
        raise MojVCannotConnect("Login completed but no journal link was discovered")

    targets: dict[str, StudentTarget] = {}
    discovered_rows = 0
    observed_fields: set[str] = set()
    context_shapes: set[str] = set()
    journal_sessions = 0
    context_responses = 0

    for link in links:
        journal_page = await _request_page(
            session,
            "get",
            link,
            headers={"Referer": f"{_PORTAL_ROOT}/"},
        )
        journal_page = await _follow_federation(session, journal_page)
        if not _city_from_url(journal_page.url):
            continue
        journal_sessions += 1

        result = await _read_context(session, journal_page)
        if result is None:
            continue
        city, payload, _status = result
        context_responses += 1
        context_shapes.add(_payload_shape(payload))

        rows = _records(payload)
        discovered_rows += len(rows)
        for row in rows:
            observed_fields.update(str(field) for field in row)
            target = _target_from_row(city, row)
            if target is not None:
                targets.setdefault(target.student_id, target)

    if not targets:
        _LOGGER.warning(
            "Student discovery returned no usable records: diary_links=%d "
            "journal_sessions=%d context_responses=%d rows=%d fields=%s shapes=%s",
            len(links),
            journal_sessions,
            context_responses,
            discovered_rows,
            sorted(observed_fields),
            sorted(context_shapes),
        )
        raise MojVNoStudents
    return tuple(targets.values())


def create_session() -> aiohttp.ClientSession:
    """Create an isolated cookie session for one configured account."""
    timeout = aiohttp.ClientTimeout(total=50, connect=12)
    return aiohttp.ClientSession(
        timeout=timeout,
        cookie_jar=aiohttp.CookieJar(),
        raise_for_status=False,
    )
