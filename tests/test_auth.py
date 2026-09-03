from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "auth.py"

spec = importlib.util.spec_from_file_location("mojv_auth_test", MODULE)
assert spec is not None and spec.loader is not None
auth = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = auth
spec.loader.exec_module(auth)


def test_login_form_keeps_hidden_fields() -> None:
    page = auth._parse_page(
        '<form action="/step" method="post">'
        '<input type="hidden" name="csrf" value="abc">'
        '<input id="UserName" name="UserName">'
        '</form>'
    )
    found = auth._find_form(page, auth._LOGIN_FIELDS)
    assert found is not None
    form, field = found
    assert field == "UserName"
    assert form.values["csrf"] == "abc"
    assert form.action == "/step"


def test_password_form_is_detected() -> None:
    page = auth._parse_page(
        '<form><input name="Password" type="password"><input name="token" value="x"></form>'
    )
    found = auth._find_form(page, auth._PASSWORD_FIELDS)
    assert found is not None
    form, field = found
    assert field == "Password"
    assert form.types[field] == "password"


def test_diary_links_are_normalized_and_deduplicated() -> None:
    links = auth._candidate_diary_links(
        "https://example.invalid/start",
        '<a href="/dziennik/a">A</a><a href="/dziennik/a">A2</a>'
        '<a href="https://uczen.example.invalid/city/App/x">B</a>',
    )
    assert links == [
        "https://example.invalid/dziennik/a",
        "https://uczen.example.invalid/city/App/x",
    ]


def test_city_is_read_from_student_url() -> None:
    assert auth._city_from_url("https://uczen.example.invalid/gryfino/App/x") == "gryfino"
    assert auth._city_from_url("https://example.invalid/gryfino/App/x") is None


def test_student_target_requires_core_fields() -> None:
    target = auth._target_from_row(
        "gryfino",
        {
            "idUczen": 123,
            "uczen": "Jan Kowalski",
            "oddzial": "5A",
            "key": "session-key",
            "idDziennik": 456,
        },
    )
    assert target is not None
    assert target.student_id == "123"
    assert target.name == "Jan Kowalski"
    assert target.class_name == "5A"
    assert target.diary_id == "456"
    assert target.base_url.endswith("/gryfino")


def test_student_target_does_not_require_journal_id_for_live_plan() -> None:
    target = auth._target_from_row(
        "gryfino",
        {
            "idUczen": 123,
            "uczen": "Jan Kowalski",
            "oddzial": "5A",
            "key": "session-key",
        },
    )
    assert target is not None
    assert target.student_id == "123"
    assert target.diary_id == ""


def test_browser_verification_marker_is_detected() -> None:
    marker = "Zabezpieczenie przed robotami"
    assert auth._looks_like_browser_challenge(marker)
