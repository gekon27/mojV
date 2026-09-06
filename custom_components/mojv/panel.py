"""Expanded School Hub serialization layer for mojV."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from . import panel_base as _base
from .const import DOMAIN
from .coordinator import MojVCoordinator
from .communication_templates import (
    CommunicationTemplateStore,
    DATA_COMMUNICATION_TEMPLATES,
)
from .custom_schedule import CustomScheduleStore, DATA_CUSTOM_SCHEDULE
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
# Kept as a migration target for installations upgraded from 0.14.x.  The
# School Hub is the sole sidebar surface; a second dashboard entry was
# confusing and duplicated navigation.

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
        # The local panel is available while its first portal refresh runs.
        # Keep its WebSocket response valid until a snapshot arrives.
        if coordinator.data is None:
            continue
        notifier = notifiers.get(entry_id)
        notification_rows = (
            notifier.notification_rows()
            if notifier is not None and hasattr(notifier, "notification_rows")
            else []
        )
        stamp = coordinator.data.updated_at
        schedule_store = hass.data.get(DATA_CUSTOM_SCHEDULE)
        for item in coordinator.data.students:
            row = _student_dict(item, now, notification_rows)
            row["custom_schedule"] = (
                schedule_store.rows_for(item.student.student_id)
                if isinstance(schedule_store, CustomScheduleStore)
                else []
            )
            template_store = hass.data.get(DATA_COMMUNICATION_TEMPLATES)
            row["communication_templates"] = (
                template_store.rows_for(item.student.student_id)
                if isinstance(template_store, CommunicationTemplateStore)
                else []
            )
            candidates.append(
                (stamp, insertion_index, row)
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


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "mojv/custom_schedule",
        vol.Required("action"): vol.In(("add", "remove")),
        vol.Optional("event"): dict,
        vol.Optional("id"): str,
    }
)
async def websocket_custom_schedule(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Store a local recurring timetable row; never call the school portal."""
    store = hass.data.get(DATA_CUSTOM_SCHEDULE)
    if not isinstance(store, CustomScheduleStore):
        connection.send_error(msg["id"], "not_ready", "Custom schedule is not ready")
        return
    try:
        if msg["action"] == "add":
            event = await store.async_add(msg.get("event") or {})
            connection.send_result(msg["id"], {"event": event})
            return
        await store.async_remove(msg.get("id") or "")
        connection.send_result(msg["id"], {"removed": True})
    except vol.Invalid as err:
        connection.send_error(msg["id"], "invalid_format", str(err))


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "mojv/communication_templates",
        vol.Required("action"): vol.In(("add", "remove")),
        vol.Optional("template"): dict,
        vol.Optional("id"): str,
    }
)
async def websocket_communication_templates(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save local message/excuse templates, without posting to the portal."""
    store = hass.data.get(DATA_COMMUNICATION_TEMPLATES)
    if not isinstance(store, CommunicationTemplateStore):
        connection.send_error(msg["id"], "not_ready", "Communication templates are not ready")
        return
    try:
        if msg["action"] == "add":
            template = await store.async_add(msg.get("template") or {})
            connection.send_result(msg["id"], {"template": template})
            return
        await store.async_remove(msg.get("id") or "")
        connection.send_result(msg["id"], {"removed": True})
    except vol.Invalid as err:
        connection.send_error(msg["id"], "invalid_format", str(err))


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "mojv/send_reply",
        vol.Required("student_id"): str,
        vol.Required("message_id"): str,
        vol.Required("body"): str,
        vol.Required("confirmed"): True,
    }
)
async def websocket_send_reply(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send one explicitly confirmed reply through the private browser helper."""
    body = str(msg["body"]).strip()
    if not body or len(body) > 4000:
        connection.send_error(msg["id"], "invalid_format", "Message body is invalid")
        return
    for coordinator in hass.data.get(DOMAIN, {}).values():
        if not isinstance(coordinator, MojVCoordinator):
            continue
        if not any(item.student.student_id == msg["student_id"] for item in coordinator.data.students):
            continue
        try:
            await coordinator.client.async_send_reply(
                msg["student_id"], msg["message_id"], body
            )
        except Exception as err:  # Portal errors are intentionally secret-free.
            connection.send_error(msg["id"], "send_failed", str(err))
            return
        connection.send_result(msg["id"], {"sent": True})
        return
    connection.send_error(msg["id"], "student_not_found", "Student is not configured")


async def async_register_school_panel(hass: HomeAssistant) -> None:
    """Register one School Hub surface and remove the retired duplicate."""
    await _base.async_register_school_panel(hass)
    if DATA_CUSTOM_SCHEDULE not in hass.data:
        schedule_store = CustomScheduleStore(hass)
        await schedule_store.async_load()
        hass.data[DATA_CUSTOM_SCHEDULE] = schedule_store
        websocket_api.async_register_command(hass, websocket_custom_schedule)
    if DATA_COMMUNICATION_TEMPLATES not in hass.data:
        template_store = CommunicationTemplateStore(hass)
        await template_store.async_load()
        hass.data[DATA_COMMUNICATION_TEMPLATES] = template_store
        websocket_api.async_register_command(hass, websocket_communication_templates)
        websocket_api.async_register_command(hass, websocket_send_reply)
    frontend.async_remove_panel(hass, DASHBOARD_URL_PATH)


def async_unregister_school_panel(hass: HomeAssistant) -> None:
    """Remove the sole mojV panel surface when the last entry unloads."""
    _base.async_unregister_school_panel(hass)


__all__ = [
    "DATA_NOTIFIERS",
    "DASHBOARD_ELEMENT",
    "DASHBOARD_URL_PATH",
    "PANEL_ELEMENT",
    "PANEL_ICON",
    "PANEL_STATIC_URL",
    "PANEL_TITLE",
    "PANEL_URL_PATH",
    "async_register_school_panel",
    "async_unregister_school_panel",
    "websocket_panel_data",
]
