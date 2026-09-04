"""Sidebar School Hub and WebSocket data API for mojV."""
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
DATA_NOTIFIERS = f"{DOMAIN}_notifiers"
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


def _grade_dict(grade) -> dict[str, Any]:
    return {
        "id": grade.grade_id,
        "subject": grade.subject,
        "value": grade.value,
        "date": grade.date.isoformat(),
        "description": grade.description,
        "weight": grade.weight,
        "category": grade.category,
        "period": grade.period,
    }


def _schoolwork_dict(item) -> dict[str, Any]:
    return {
        "id": item.work_id,
        "date": item.date.isoformat(),
        "subject": item.subject,
        "title": item.title,
        "kind": item.kind,
        "description": item.description,
    }


def _remark_dict(remark) -> dict[str, Any]:
    return {
        "id": remark.remark_id,
        "date": remark.date.isoformat(),
        "text": remark.text,
        "author": remark.author,
        "category": remark.category,
        "kind": remark.kind,
        "points": remark.points,
    }


def _meeting_dict(item) -> dict[str, Any]:
    return {
        "id": item.meeting_id,
        "start": item.start.isoformat(),
        "title": item.title,
        "location": item.location,
        "description": item.description,
        "online_url": item.online_url,
    }


def _achievement_dict(item) -> dict[str, Any]:
    return {
        "id": item.achievement_id,
        "date": item.date.isoformat() if item.date else None,
        "title": item.title,
        "description": item.description,
    }


def _dashboard_dict(snapshot, now) -> dict[str, Any]:
    """Build the compact School Hub summary from already fetched LIVE data."""
    latest_grade = max(snapshot.grades, key=lambda item: item.date, default=None)
    future_work = sorted(
        (item for item in snapshot.schoolwork if item.date >= now),
        key=lambda item: item.date,
    )
    future_meetings = sorted(
        (item for item in snapshot.meetings if item.start >= now),
        key=lambda item: item.start,
    )
    latest_remark = max(snapshot.remarks, key=lambda item: item.date, default=None)
    dated_achievements = [item for item in snapshot.achievements if item.date is not None]
    latest_achievement = (
        max(dated_achievements, key=lambda item: item.date)
        if dated_achievements
        else (snapshot.achievements[0] if snapshot.achievements else None)
    )
    overall_stat = next(
        (item for item in snapshot.attendance_stats if not item.subject), None
    )
    latest_message = max(snapshot.messages, key=lambda item: item.date, default=None)

    return {
        "unread_messages": sum(1 for item in snapshot.messages if item.unread),
        "upcoming_schoolwork": len(future_work),
        "upcoming_meetings": len(future_meetings),
        "latest_grade": _grade_dict(latest_grade) if latest_grade else None,
        "next_schoolwork": _schoolwork_dict(future_work[0]) if future_work else None,
        "next_meeting": _meeting_dict(future_meetings[0]) if future_meetings else None,
        "latest_remark": _remark_dict(latest_remark) if latest_remark else None,
        "attendance_percentage": overall_stat.percentage if overall_stat else None,
        "latest_achievement": (
            _achievement_dict(latest_achievement) if latest_achievement else None
        ),
        "latest_message": (
            {
                "id": latest_message.message_id,
                "date": latest_message.date.isoformat(),
                "sender": latest_message.sender,
                "subject": latest_message.subject,
                "unread": latest_message.unread,
            }
            if latest_message
            else None
        ),
    }


def _activity_rows(snapshot) -> list[dict[str, Any]]:
    """Combine supported LIVE modules into one newest-first public timeline."""
    rows: list[tuple[Any, dict[str, Any]]] = []
    student_id = snapshot.student.student_id

    for grade in snapshot.grades:
        rows.append(
            (
                grade.date,
                {
                    "id": f"grade:{grade.grade_id}",
                    "kind": "grade",
                    "date": grade.date.isoformat(),
                    "title": f"Ocena {grade.value}",
                    "subtitle": grade.subject,
                    "detail": grade.description or grade.category,
                    "student_id": student_id,
                },
            )
        )
    for grade in snapshot.final_grades:
        value = grade.final or grade.proposed
        if value:
            rows.append(
                (
                    None,
                    {
                        "id": f"final:{grade.subject}:{grade.period}",
                        "kind": "final_grade",
                        "date": None,
                        "title": f"Ocena klasyfikacyjna {value}",
                        "subtitle": grade.subject,
                        "detail": grade.period,
                        "student_id": student_id,
                    },
                )
            )
    for remark in snapshot.remarks:
        kind = "praise" if remark.kind in {"positive", "praise"} else "remark"
        rows.append(
            (
                remark.date,
                {
                    "id": f"remark:{remark.remark_id}",
                    "kind": kind,
                    "date": remark.date.isoformat(),
                    "title": "Pochwała" if kind == "praise" else "Uwaga",
                    "subtitle": remark.category or remark.author,
                    "detail": remark.text,
                    "student_id": student_id,
                },
            )
        )
    for message in snapshot.messages:
        rows.append(
            (
                message.date,
                {
                    "id": f"message:{message.message_id}",
                    "kind": "message",
                    "date": message.date.isoformat(),
                    "title": message.subject or "Wiadomość",
                    "subtitle": message.sender,
                    "detail": message.body,
                    "unread": message.unread,
                    "student_id": student_id,
                },
            )
        )
    for item in snapshot.schoolwork:
        rows.append(
            (
                item.date,
                {
                    "id": f"schoolwork:{item.work_id}",
                    "kind": "schoolwork",
                    "date": item.date.isoformat(),
                    "title": item.title,
                    "subtitle": item.subject,
                    "detail": item.description,
                    "student_id": student_id,
                },
            )
        )
    for item in snapshot.meetings:
        rows.append(
            (
                item.start,
                {
                    "id": f"meeting:{item.meeting_id}",
                    "kind": "meeting",
                    "date": item.start.isoformat(),
                    "title": item.title or "Zebranie",
                    "subtitle": item.location,
                    "detail": item.description,
                    "student_id": student_id,
                },
            )
        )
    for item in snapshot.achievements:
        rows.append(
            (
                item.date,
                {
                    "id": f"achievement:{item.achievement_id}",
                    "kind": "achievement",
                    "date": item.date.isoformat() if item.date else None,
                    "title": item.title or "Osiągnięcie",
                    "subtitle": "Osiągnięcie",
                    "detail": item.description,
                    "student_id": student_id,
                },
            )
        )
    for lesson in snapshot.lessons:
        if lesson.attendance == "not_recorded" or lesson.cancelled:
            continue
        rows.append(
            (
                lesson.start,
                {
                    "id": f"attendance:{lesson.start.isoformat()}:{lesson.number}",
                    "kind": "attendance",
                    "date": lesson.start.isoformat(),
                    "title": "Frekwencja",
                    "subtitle": lesson.subject,
                    "detail": lesson.attendance,
                    "student_id": student_id,
                },
            )
        )

    rows.sort(
        key=lambda pair: (pair[0] is not None, pair[0] if pair[0] is not None else ""),
        reverse=True,
    )
    return [row for _, row in rows]


def _student_dict(
    snapshot,
    now,
    notification_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    current = active_lesson(snapshot, now)
    upcoming = next_lesson(snapshot, now)
    student_notifications = [
        dict(row)
        for row in (notification_rows or [])
        if row.get("student_id") == snapshot.student.student_id
    ]
    return {
        "id": snapshot.student.student_id,
        "name": snapshot.student.name,
        "class": snapshot.student.class_name,
        "current": _lesson_dict(current, now),
        "next": _lesson_dict(upcoming, now),
        "dashboard": _dashboard_dict(snapshot, now),
        "activity": _activity_rows(snapshot),
        "notifications": student_notifications,
        "lessons": [
            {
                **(_lesson_dict(lesson, now) or {}),
                "current": lesson == current,
            }
            for lesson in lessons_today(snapshot, now)
        ],
        "week": _week_dict(snapshot, now),
        "attendance_summary": attendance_summary(snapshot),
        "grades": [_grade_dict(grade) for grade in snapshot.grades],
        "final_grades": [
            {
                "subject": grade.subject,
                "proposed": grade.proposed,
                "final": grade.final,
                "period": grade.period,
            }
            for grade in snapshot.final_grades
        ],
        "schoolwork": [_schoolwork_dict(item) for item in snapshot.schoolwork],
        "remarks": [_remark_dict(remark) for remark in snapshot.remarks],
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
        "achievements": [_achievement_dict(item) for item in snapshot.achievements],
        "meetings": [_meeting_dict(item) for item in snapshot.meetings],
    }


@callback
@websocket_api.websocket_command({vol.Required("type"): "mojv/panel"})
def websocket_panel_data(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return structured data used by the School Hub panel."""
    now = dt_util.now()
    students: list[dict[str, Any]] = []
    updated_at = None
    notifiers = hass.data.get(DATA_NOTIFIERS, {})

    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if not isinstance(coordinator, MojVCoordinator):
            continue
        notifier = notifiers.get(entry_id)
        notification_rows = (
            notifier.notification_rows()
            if notifier is not None and hasattr(notifier, "notification_rows")
            else []
        )
        students.extend(
            _student_dict(item, now, notification_rows)
            for item in coordinator.data.students
        )
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
        module_url=f"{PANEL_STATIC_URL}/school-panel-hub.js",
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
