"""Expanded School Hub serialization layer for mojV."""
from __future__ import annotations

from typing import Any

from . import panel_base as _base

PANEL_URL_PATH = _base.PANEL_URL_PATH
PANEL_TITLE = _base.PANEL_TITLE
PANEL_ICON = _base.PANEL_ICON
PANEL_ELEMENT = _base.PANEL_ELEMENT
PANEL_STATIC_URL = _base.PANEL_STATIC_URL
DATA_PANEL_REGISTERED = _base.DATA_PANEL_REGISTERED
DATA_NOTIFIERS = _base.DATA_NOTIFIERS
DAY_NAMES = _base.DAY_NAMES

_BASE_STUDENT_DICT = _base._student_dict


def _free_day_dict(item: Any) -> dict[str, Any]:
    return {
        "start": item.start.isoformat(),
        "end": item.end.isoformat(),
        "name": item.name,
    }


def _student_dict(
    snapshot: Any,
    now: Any,
    notification_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Add expanded, intentionally safe school modules to the existing payload."""
    row = _BASE_STUDENT_DICT(snapshot, now, notification_rows)

    lucky = snapshot.lucky_number
    row["lucky_number"] = (
        {"date": lucky.date.isoformat(), "value": lucky.value}
        if lucky is not None
        else None
    )
    row["free_days"] = [_free_day_dict(item) for item in snapshot.free_days]
    row["excuses"] = {
        "active": snapshot.excuses.active,
        "blocked": snapshot.excuses.blocked,
        "entries": [
            {
                "date": item.date.isoformat(),
                "lesson_number": item.lesson_number,
                "status": item.status,
            }
            for item in snapshot.excuses.entries
        ],
    }
    row["teachers"] = [
        {
            "name": item.name,
            "subject": item.subject,
            "homeroom": item.homeroom,
        }
        for item in snapshot.teachers
    ]
    school = snapshot.school_info
    row["school_info"] = (
        {
            "name": school.name,
            "city": school.city,
            "address": school.address,
            "website": school.website,
            "email": school.email,
            "directors": list(school.directors),
        }
        if school is not None
        else None
    )
    row["important_today"] = [
        {
            "subject": item.subject,
            "kind": item.kind,
            "title": item.title,
        }
        for item in snapshot.important_today
    ]
    row["homeroom_teachers"] = [
        {
            "name": item.name,
            "primary": item.primary,
        }
        for item in snapshot.homeroom_teachers
    ]
    row["completed_lessons"] = [
        {
            "id": item.lesson_id,
            "date": item.date.isoformat(),
            "subject": item.subject,
            "teacher": item.teacher,
            "topic": item.topic,
            "lesson_number": item.lesson_number,
            "online_url": item.online_url,
        }
        for item in snapshot.completed_lessons
    ]

    future_free_days = [
        item for item in snapshot.free_days if item.end.date() >= now.date()
    ]
    next_free_day = (
        min(future_free_days, key=lambda item: item.start)
        if future_free_days
        else None
    )
    dashboard = dict(row.get("dashboard") or {})
    dashboard["lucky_number"] = row["lucky_number"]
    dashboard["important_today"] = row["important_today"]
    dashboard["next_free_day"] = (
        _free_day_dict(next_free_day) if next_free_day is not None else None
    )
    row["dashboard"] = dashboard
    return row


_base._student_dict = _student_dict

websocket_panel_data = _base.websocket_panel_data
async_register_school_panel = _base.async_register_school_panel
async_unregister_school_panel = _base.async_unregister_school_panel

__all__ = [
    "DATA_NOTIFIERS",
    "PANEL_ELEMENT",
    "PANEL_ICON",
    "PANEL_STATIC_URL",
    "PANEL_TITLE",
    "PANEL_URL_PATH",
    "async_register_school_panel",
    "async_unregister_school_panel",
    "websocket_panel_data",
]
