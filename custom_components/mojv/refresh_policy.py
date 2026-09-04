"""Adaptive refresh cadence for LIVE school data."""
from __future__ import annotations

from datetime import datetime, timedelta

from .const import LIVE_POST_LESSON_DELAY, LIVE_UPDATE_INTERVAL
from .models import AccountSnapshot


def next_live_refresh_delay(snapshot: AccountSnapshot, now: datetime) -> timedelta:
    """Return the next full refresh delay for a LIVE account.

    The normal ceiling is one hour. When a cached lesson ends sooner, schedule
    the next complete refresh shortly after that lesson so attendance, grades,
    messages and plan changes can be picked up without polling aggressively.
    For multi-student accounts the earliest lesson boundary wins.
    """
    delay = LIVE_UPDATE_INTERVAL

    for student_snapshot in snapshot.students:
        for lesson in student_snapshot.lessons:
            target = lesson.end + LIVE_POST_LESSON_DELAY
            if target <= now:
                continue
            candidate = target - now
            if candidate < delay:
                delay = candidate

    return delay
