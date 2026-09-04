"""Adaptive LIVE refresh policy tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from custom_components.mojv.models import AccountSnapshot, Lesson, Student, StudentSnapshot
from custom_components.mojv.refresh_policy import next_live_refresh_delay

UTC = timezone.utc


def _snapshot(*lesson_sets: tuple[Lesson, ...]) -> AccountSnapshot:
    students = tuple(
        StudentSnapshot(
            student=Student(student_id=f"student-{index}", name=f"Student {index}"),
            lessons=lessons,
        )
        for index, lessons in enumerate(lesson_sets, start=1)
    )
    return AccountSnapshot(students=students, updated_at=datetime(2026, 9, 4, 8, 0, tzinfo=UTC))


def _lesson(start: datetime, end: datetime, *, number: int = 1) -> Lesson:
    return Lesson(number=number, subject="Test", start=start, end=end)


def test_idle_refresh_is_hourly_without_lessons() -> None:
    now = datetime(2026, 9, 4, 18, 0, tzinfo=UTC)
    assert next_live_refresh_delay(_snapshot(()), now) == timedelta(hours=1)


def test_refresh_targets_two_minutes_after_next_lesson_end() -> None:
    now = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
    lesson = _lesson(now - timedelta(minutes=5), now + timedelta(minutes=30))

    assert next_live_refresh_delay(_snapshot((lesson,)), now) == timedelta(minutes=32)


def test_refresh_does_not_wait_an_hour_when_post_lesson_boundary_is_near() -> None:
    now = datetime(2026, 9, 4, 8, 46, tzinfo=UTC)
    lesson = _lesson(now - timedelta(minutes=46), now - timedelta(minutes=1))

    assert next_live_refresh_delay(_snapshot((lesson,)), now) == timedelta(minutes=1)


def test_refresh_is_capped_at_one_hour_when_next_lesson_end_is_far_away() -> None:
    now = datetime(2026, 9, 4, 6, 0, tzinfo=UTC)
    lesson = _lesson(now + timedelta(hours=2), now + timedelta(hours=2, minutes=45))

    assert next_live_refresh_delay(_snapshot((lesson,)), now) == timedelta(hours=1)


def test_refresh_returns_to_hourly_after_last_post_lesson_boundary() -> None:
    now = datetime(2026, 9, 4, 16, 0, tzinfo=UTC)
    lesson = _lesson(now - timedelta(hours=2), now - timedelta(hours=1))

    assert next_live_refresh_delay(_snapshot((lesson,)), now) == timedelta(hours=1)


def test_multiple_students_use_the_earliest_post_lesson_boundary() -> None:
    now = datetime(2026, 9, 4, 8, 0, tzinfo=UTC)
    first = _lesson(now, now + timedelta(minutes=45))
    second = _lesson(now, now + timedelta(minutes=30))

    assert next_live_refresh_delay(_snapshot((first,), (second,)), now) == timedelta(minutes=32)
