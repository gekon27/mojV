"""Expanded School Hub serialization layer for mojV."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from . import panel_base as _base
from .const import DOMAIN
from .coordinator import MojVCoordinator
from .panel_students import select_student_rows

PANEL_URL_PATH = _base.PANEL_URL_PATH
PANEL_TITLE = _base.PANEL_TITLE
PANEL_ICON = _base.PANEL_ICON
PANEL_ELEMENT = _base.PANEL_ELEMENT
PANEL_STATIC_URL = _base.PANEL_STATIC_URL
DATA_PANEL_REGISTERED = _base.DATA_PANEL_REGISTERED
DATA_NOTIFIERS = _base.DATA_NOTIFIERS
DAY_NAMES = _base.DAY_NAMES

DASHBOARD_URL_PATH = "mojv-dashboard"
DASHBOARD_ELEMENT = "mojv-school-dashboard"
DASHBOARD_TITLE = "Dashboard szkoły"
DASHBOARD_ICON = "mdi:view-dashboard-outline"
DATA_DASHBOARD_REGISTERED = f"{DOMAIN}_dashboard_registered"

_BASE_STUDENT_DICT = _base._student_dict


def _free_day_dict(item: Any) -> dict[str, Any]:
    return {
        "start": item.start.isoformat(),
        "end": item.end.isoformat(),
        "name": item.name,
    }


def _schoolwork_metadata(item: Any) -> dict[str, Any]:
    """Return only safe display metadata for one term-calendar entry."""
    return {
        "teacher": item.teacher,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "due_at": item.due_at.isoformat() if item.due_at else None,
    }


def _student_dict(
    snapshot: Any,
    now: Any,
    notification_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Add expanded, intentionally safe school modules to the existing payload."""
    row = _BASE_STUDENT_DICT(snapshot, now, notification_rows)

    schoolwork_by_id = {
        str(item.work_id): item
        for item in snapshot.schoolwork
    }
    for public_item in row.get("schoolwork", []):
        item = schoolwork_by_id.get(str(public_item.get("id") or ""))
        if item is not None:
            public_item.update(_schoolwork_metadata(item))

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
            "description": item.description,
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
    next_schoolwork = dashboard.get("next_schoolwork")
    if isinstance(next_schoolwork, dict):
        item = schoolwork_by_id.get(str(next_schoolwork.get("id") or ""))
        if item is not None:
            next_schoolwork = dict(next_schoolwork)
            next_schoolwork.update(_schoolwork_metadata(item))
            dashboard["next_schoolwork"] = next_schoolwork
    dashboard["lucky_number"] = row["lucky_number"]
    dashboard["important_today"] = row["important_today"]
    dashboard["next_free_day"] = (
        _free_day_dict(next_free_day) if next_free_day is not None else None
    )
    row["dashboard"] = dashboard
    return row


_base._student_dict = _student_dict


@callback
@websocket_api.websocket_command({vol.Required("type"): "mojv/panel"})
def websocket_panel_data(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return one newest safe panel row for every stable student ID."""
    now = dt_util.now()
    candidates: list[tuple[Any, int, dict[str, Any]]] = []
    updated_at = None
    notifiers = hass.data.get(DATA_NOTIFIERS, {})
    insertion_index = 0

    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if not isinstance(coordinator, MojVCoordinator):
            continue
        notifier = notifiers.get(entry_id)
        notification_rows = (
            notifier.notification_rows()
            if notifier is not None and hasattr(notifier, "notification_rows")
            else []
        )
        stamp = coordinator.data.updated_at
        for item in coordinator.data.students:
            candidates.append(
                (stamp, insertion_index, _student_dict(item, now, notification_rows))
            )
            insertion_index += 1
        if updated_at is None or stamp > updated_at:
            updated_at = stamp

    connection.send_result(
        msg["id"],
        {
            "students": select_student_rows(candidates),
            "updated_at": updated_at.isoformat() if updated_at else None,
            "now": now.isoformat(),
        },
    )


_base.websocket_panel_data = websocket_panel_data


async def async_register_school_panel(hass: HomeAssistant) -> None:
    """Register the regular School Hub and authenticated browser dashboard."""
    await _base.async_register_school_panel(hass)
    if hass.data.get(DATA_DASHBOARD_REGISTERED):
        return

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=DASHBOARD_ELEMENT,
        frontend_url_path=DASHBOARD_URL_PATH,
        module_url=f"{PANEL_STATIC_URL}/school-dashboard.js",
        sidebar_title=DASHBOARD_TITLE,
        sidebar_icon=DASHBOARD_ICON,
        require_admin=False,
        config={"title": DASHBOARD_TITLE, "full_screen": True},
    )
    hass.data[DATA_DASHBOARD_REGISTERED] = True


def async_unregister_school_panel(hass: HomeAssistant) -> None:
    """Remove both mojV panel surfaces when the last entry unloads."""
    if hass.data.get(DATA_DASHBOARD_REGISTERED):
        frontend.async_remove_panel(hass, DASHBOARD_URL_PATH)
        hass.data[DATA_DASHBOARD_REGISTERED] = False
    _base.async_unregister_school_panel(hass)


__all__ = [
    "DASHBOARD_ELEMENT",
    "DASHBOARD_TITLE",
    "DASHBOARD_URL_PATH",
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
