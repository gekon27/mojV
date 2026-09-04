"""Sidebar School panel and WebSocket data API for mojV."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import MojVCoordinator
from .logic import (
    active_lesson,
    attendance_summary,
    lesson_alerts,
    lesson_progress_pct,
    lessons_today,
    minutes_to_end,
    next_lesson,
)

PANEL_URL_PATH = "school"
PANEL_TITLE = "Szkoła"
PANEL_ICON = "mdi:school-outline"
PANEL_ELEMENT = "mojv-school-panel"
PANEL_STATIC_URL = "/mojv-static"
DATA_PANEL_REGISTERED = f"{DOMAIN}_panel_registered"
DAY_NAMES = (
    "Poniedziałek",
    "Wtorek",
    "Środa",
    "Czwartek",
    "Piątek",
    "Sobota",
    "Niedziela",
)


def _lesson_dict(lesson, now) -> dict[str, Any] | None:
    if lesson is None:
        return None
    return {
        "number": lesson.number,
        "subject": lesson.subject,
        "start": lesson.start.isoformat(),
        "end": lesson.end.isoformat(),
        "room": lesson.room,
        "teacher": lesson.teacher,
        "attendance": lesson.attendance,
        "cancelled": lesson.cancelled,
        "replacement": lesson.replacement,
        "note": lesson.note,
        "minutes_to_end": minutes_to_end(lesson, now),
        "progress_pct": lesson_progress_pct(lesson, now),
        "alerts": [
            {"kind": kind, "text": text}
            for kind, text in lesson_alerts(lesson, now)
        ],
    }


def _week_dict(snapshot, now) -> list[dict[str, Any]]:
    current = active_lesson(snapshot, now)
    grouped: dict[str, list] = {}
    for lesson in sorted(snapshot.lessons, key=lambda item: item.start):
        grouped.setdefault(lesson.start.date().isoformat(), []).append(lesson)

    return [
        {
            "date": date_key,
            "label": DAY_NAMES[items[0].start.weekday()],
            "today": items[0].start.date() == now.date(),
            "lessons": [
                {
                    **(_lesson_dict(lesson, now) or {}),
                    "current": lesson == current,
                }
                for lesson in items
            ],
        }
        for date_key, items in grouped.items()
    ]


def _student_dict(snapshot, now) -> dict[str, Any]:
    current = active_lesson(snapshot, now)
    upcoming = next_lesson(snapshot, now)
    return {
        "id": snapshot.student.student_id,
        "name": snapshot.student.name,
        "class": snapshot.student.class_name,
        "current": _lesson_dict(current, now),
        "next": _lesson_dict(upcoming, now),
        "lessons": [
            {
                **(_lesson_dict(lesson, now) or {}),
                "current": lesson == current,
            }
            for lesson in lessons_today(snapshot, now)
        ],
        "week": _week_dict(snapshot, now),
        "attendance_summary": attendance_summary(snapshot),
        "grades": [
            {
                "id": grade.grade_id,
                "subject": grade.subject,
                "value": grade.value,
                "date": grade.date.isoformat(),
                "description": grade.description,
                "category": grade.category,
                "period": grade.period,
            }
            for grade in snapshot.grades
        ],
        "final_grades": [
            {
                "subject": grade.subject,
                "proposed": grade.proposed,
                "final": grade.final,
                "period": grade.period,
            }
            for grade in snapshot.final_grades
        ],
        "schoolwork": [
            {
                "id": item.work_id,
                "date": item.date.isoformat(),
                "subject": item.subject,
                "title": item.title,
                "kind": item.kind,
                "description": item.description,
            }
            for item in snapshot.schoolwork
        ],
        "remarks": [
            {
                "id": remark.remark_id,
                "date": remark.date.isoformat(),
                "text": remark.text,
                "author": remark.author,
                "category": remark.category,
                "kind": remark.kind,
                "points": remark.points,
            }
            for remark in snapshot.remarks
        ],
        "messages": [
            {
                "id": message.message_id,
                "date": message.date.isoformat(),
                "sender": message.sender,
                "subject": message.subject,
                "body": message.body,
                "unread": message.unread,
            }
            for message in snapshot.messages
        ],
        "attendance_stats": [
            {
                "subject": stat.subject,
                "present": stat.present,
                "absent": stat.absent,
                "excused": stat.excused,
                "late": stat.late,
                "excused_late": stat.excused_late,
                "school_activity": stat.school_activity,
                "released": stat.released,
                "total": stat.total,
                "percentage": stat.percentage,
            }
            for stat in snapshot.attendance_stats
        ],
        "achievements": [
            {
                "id": item.achievement_id,
                "date": item.date.isoformat() if item.date else None,
                "title": item.title,
                "description": item.description,
            }
            for item in snapshot.achievements
        ],
        "meetings": [
            {
                "id": item.meeting_id,
                "start": item.start.isoformat(),
                "title": item.title,
                "location": item.location,
                "description": item.description,
                "online_url": item.online_url,
            }
            for item in snapshot.meetings
        ],
    }


@callback
@websocket_api.websocket_command({vol.Required("type"): "mojv/panel"})
def websocket_panel_data(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return structured data used by the School panel."""
    now = dt_util.now()
    coordinators = [
        value
        for value in hass.data.get(DOMAIN, {}).values()
        if isinstance(value, MojVCoordinator)
    ]
    students: list[dict[str, Any]] = []
    updated_at = None
    for coordinator in coordinators:
        students.extend(_student_dict(item, now) for item in coordinator.data.students)
        stamp = coordinator.data.updated_at
        if updated_at is None or stamp > updated_at:
            updated_at = stamp

    connection.send_result(
        msg["id"],
        {
            "students": students,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "now": now.isoformat(),
        },
    )


async def async_register_school_panel(hass: HomeAssistant) -> None:
    """Register the School sidebar panel once."""
    if hass.data.get(DATA_PANEL_REGISTERED):
        return

    frontend_path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_STATIC_URL, str(frontend_path), False)]
        )
    except RuntimeError:
        pass

    websocket_api.async_register_command(hass, websocket_panel_data)
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_ELEMENT,
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{PANEL_STATIC_URL}/school-panel-live.js",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config={"title": PANEL_TITLE},
        config_panel_domain=DOMAIN,
    )
    hass.data[DATA_PANEL_REGISTERED] = True


def async_unregister_school_panel(hass: HomeAssistant) -> None:
    """Remove the School panel when no mojV entries remain."""
    if not hass.data.get(DATA_PANEL_REGISTERED):
        return
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
    hass.data[DATA_PANEL_REGISTERED] = False
