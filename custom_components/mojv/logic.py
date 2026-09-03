"""Pure timetable logic for mojV."""
from __future__ import annotations

import math
from datetime import datetime

from .models import Lesson, StudentSnapshot

_ATTENDANCE_STATES = (
    "present",
    "absent",
    "excused_absence",
    "late",
    "excused_late",
    "school_activity",
    "released",
    "not_recorded",
    "unknown",
)


def active_lesson(snapshot: StudentSnapshot, now: datetime) -> Lesson | None:
    """Return the lesson active at *now*, excluding cancelled lessons."""
    for lesson in snapshot.lessons:
        if not lesson.cancelled and lesson.start <= now < lesson.end:
            return lesson
    return None


def next_lesson(snapshot: StudentSnapshot, now: datetime) -> Lesson | None:
    """Return the next non-cancelled lesson after *now*."""
    candidates = [
        lesson
        for lesson in snapshot.lessons
        if not lesson.cancelled and lesson.start > now
    ]
    return min(candidates, key=lambda item: item.start) if candidates else None


def lessons_today(snapshot: StudentSnapshot, now: datetime) -> tuple[Lesson, ...]:
    """Return today's lessons in chronological order."""
    today = now.date()
    return tuple(
        sorted(
            (lesson for lesson in snapshot.lessons if lesson.start.date() == today),
            key=lambda item: item.start,
        )
    )


def attendance_summary(snapshot: StudentSnapshot) -> dict[str, int]:
    """Count attendance states for non-cancelled lessons in a snapshot."""
    counts = {state: 0 for state in _ATTENDANCE_STATES}
    known = set(_ATTENDANCE_STATES[:-1])
    for lesson in snapshot.lessons:
        if lesson.cancelled:
            continue
        state = lesson.attendance if lesson.attendance in known else "unknown"
        counts[state] += 1
    return counts


def minutes_to_end(lesson: Lesson | None, now: datetime) -> int:
    """Return whole minutes until lesson end, rounded up."""
    if lesson is None:
        return 0
    return max(0, math.ceil((lesson.end - now).total_seconds() / 60))


def lesson_progress_pct(lesson: Lesson | None, now: datetime) -> int:
    """Return elapsed lesson time as a clamped whole percentage."""
    if lesson is None:
        return 0
    duration = (lesson.end - lesson.start).total_seconds()
    if duration <= 0:
        return 0
    elapsed = (now - lesson.start).total_seconds()
    return max(0, min(100, round((elapsed / duration) * 100)))


def lesson_alerts(
    lesson: Lesson | None,
    now: datetime,
) -> tuple[tuple[str, str], ...]:
    """Return concise, ordered alerts for the active lesson."""
    if lesson is None:
        return ()

    alerts: list[tuple[str, str]] = []
    if lesson.attendance == "absent":
        alerts.append(("absence", "Nieobecność na trwającej lekcji"))
    elif lesson.attendance == "late":
        alerts.append(("late", "Spóźnienie na trwającą lekcję"))

    remaining = minutes_to_end(lesson, now)
    if 0 < remaining <= 5:
        alerts.append(("ending", f"Koniec lekcji za {remaining} min"))

    return tuple(alerts)
