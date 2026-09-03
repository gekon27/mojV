"""Pure helpers for the local mojV authentication helper protocol."""
from __future__ import annotations

from typing import Any

HELPER_SLUG_SUFFIX = "mojv_auth_helper"
_FORBIDDEN_SECRET_FIELDS = {
    "cookie",
    "cookies",
    "diary_id",
    "journal_id",
    "password",
    "session_key",
    "token",
    "xhr_token",
}


def unwrap_supervisor(payload: Any) -> Any:
    """Return Supervisor's useful data regardless of envelope shape."""
    if not isinstance(payload, dict):
        return payload
    if "data" in payload:
        return payload["data"]
    return payload


def select_helper_slug(payload: Any) -> str | None:
    """Find the installed mojV auth helper in Supervisor's app list."""
    data = unwrap_supervisor(payload)
    if not isinstance(data, dict):
        return None
    addons = data.get("addons")
    if not isinstance(addons, list):
        return None
    for item in addons:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "")
        if not slug.endswith(HELPER_SLUG_SUFFIX):
            continue
        installed = item.get("installed")
        if installed not in (None, False, "") or item.get("state") in {"started", "running"}:
            return slug
    return None


def _contains_secret_field(value: Any) -> bool:
    """Detect forbidden authentication fields anywhere in a helper payload."""
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_SECRET_FIELDS:
                return True
            if _contains_secret_field(child):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_secret_field(item) for item in value)
    return False


def validate_snapshot(payload: Any) -> bool:
    """Validate that helper output contains only public school data."""
    if not isinstance(payload, dict):
        return False
    students = payload.get("students")
    if not isinstance(students, list) or not students:
        return False
    for student in students:
        if not isinstance(student, dict):
            return False
        if _contains_secret_field(student):
            return False
        if not str(student.get("student_id") or ""):
            return False
        if not str(student.get("name") or ""):
            return False
        if "timetable" not in student or "attendance" not in student:
            return False
    return True
