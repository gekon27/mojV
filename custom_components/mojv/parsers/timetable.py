"""Timetable and attendance payload parsing."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time
from typing import Any

from ..models import Lesson

_ATTENDANCE = {
    1: "present",
    2: "absent",
    3: "excused_absence",
    4: "late",
    5: "excused_late",
    6: "school_activity",
    7: "released",
}

_STATUS = {
    1: "replacement",
    2: "moved",
    3: "cancelled",
    4: "teacher_absent",
}


def parse_timetable(
    timetable_payload: Any,
    attendance_payload: Any = None,
) -> tuple[Lesson, ...]:
    """Convert raw timetable + attendance data to mojV Lesson objects."""
    attendance = _attendance_index(attendance_payload)
    lessons: list[Lesson] = []

    for row in _records(timetable_payload):
        lesson_date = _parse_date(row.get("data"))
        start_time = _parse_time(row.get("godzinaOd"))
        end_time = _parse_time(row.get("godzinaDo"))
        if lesson_date is None or start_time is None or end_time is None:
            continue

        start = datetime.combine(lesson_date, start_time)
        end = datetime.combine(lesson_date, end_time)
        if end <= start:
            continue

        status_code = _int(row.get("adnotacja"), default=0)
        status = _STATUS.get(status_code, "")
        note_parts: list[str] = []
        if status:
            note_parts.append(status)
        for change in row.get("zmiany") or ():
            if not isinstance(change, dict):
                continue
            text = str(
                change.get("informacjeNieobecnosc")
                or change.get("informacje")
                or change.get("opis")
                or ""
            ).strip()
            if text:
                note_parts.append(text)

        key = (lesson_date.isoformat(), start_time.strftime("%H:%M"))
        lessons.append(
            Lesson(
                number=_lesson_number(row, len(lessons) + 1),
                subject=str(row.get("przedmiot") or "Zajęcia").strip(),
                start=start,
                end=end,
                room=str(row.get("sala") or "").strip(),
                teacher=str(row.get("prowadzacy") or "").strip(),
                attendance=attendance.get(key, "not_recorded"),
                cancelled=status_code == 3,
                replacement=status_code == 1,
                note=" · ".join(dict.fromkeys(note_parts)),
            )
        )

    lessons.sort(key=lambda item: item.start)
    return _renumber_missing(lessons)


def apply_attendance(
    lessons: tuple[Lesson, ...],
    attendance_payload: Any,
) -> tuple[Lesson, ...]:
    """Apply a fresh attendance payload to previously parsed lessons."""
    attendance = _attendance_index(attendance_payload)
    result: list[Lesson] = []
    for lesson in lessons:
        key = (lesson.start.date().isoformat(), lesson.start.strftime("%H:%M"))
        result.append(
            replace(
                lesson,
                attendance=attendance.get(key, lesson.attendance),
            )
        )
    return tuple(result)


def _attendance_index(payload: Any) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for row in _records(payload, dict_list_keys=("oddzialy", "data", "items", "records")):
        item_date = _parse_date(row.get("data"))
        item_time = _parse_time(row.get("godzinaOd"))
        if item_date is None or item_time is None:
            continue
        category = _int(row.get("kategoriaFrekwencji"), default=0)
        result[(item_date.isoformat(), item_time.strftime("%H:%M"))] = (
            _ATTENDANCE.get(category, "unknown")
        )
    return result


def _records(
    payload: Any,
    *,
    dict_list_keys: tuple[str, ...] = ("data", "items", "lista", "records"),
) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in dict_list_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_time(value: Any) -> time | None:
    if not value:
        return None
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[1]
    if text.endswith("Z"):
        text = text[:-1]
    try:
        return time.fromisoformat(text)
    except ValueError:
        try:
            return time.fromisoformat(text[:5])
        except ValueError:
            return None


def _int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _lesson_number(row: dict[str, Any], fallback: int) -> int:
    for key in ("numerLekcji", "lekcja", "nrLekcji", "numer"):
        if key in row:
            number = _int(row.get(key), default=0)
            if number > 0:
                return number
    return fallback


def _renumber_missing(lessons: list[Lesson]) -> tuple[Lesson, ...]:
    """Keep explicit numbers, but normalize fallback numbering per day."""
    by_day: dict[date, int] = {}
    result: list[Lesson] = []
    for lesson in lessons:
        day = lesson.start.date()
        by_day[day] = by_day.get(day, 0) + 1
        number = lesson.number if lesson.number > 0 else by_day[day]
        result.append(replace(lesson, number=number))
    return tuple(result)
