"""Pure timetable logic for mojV."""
from __future__ import annotations

import math
from datetime import datetime

from .models import Lesson, StudentSnapshot


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


def minutes_to_end(lesson: Lesson | None, now: datetime) -> int:
    """Return whole minutes until lesson end, rounded up."""
    if lesson is None:
        return 0
    return max(0, math.ceil((lesson.end - now).total_seconds() / 60))
