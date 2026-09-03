"""Data client for mojV.

The test build contains a deterministic demo backend. The live school-portal
transport will replace only this boundary while the Home Assistant data model,
panel and multi-student handling stay unchanged.
"""
from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util

from .const import (
    ATTENDANCE_ABSENT,
    ATTENDANCE_LATE,
    ATTENDANCE_PRESENT,
    MODE_DEMO,
)
from .models import AccountSnapshot, Grade, Lesson, Remark, Student, StudentSnapshot


class MojVClientError(Exception):
    """Base mojV client error."""


class MojVLiveAuthPending(MojVClientError):
    """Live auth transport is not available yet."""


class MojVClient:
    """Fetch account data."""

    def __init__(self, mode: str, demo_students: int = 2) -> None:
        self._mode = mode
        self._demo_students = demo_students
        self._demo_anchor = None

    async def async_fetch(self) -> AccountSnapshot:
        """Fetch data for all students."""
        if self._mode != MODE_DEMO:
            raise MojVLiveAuthPending(
                "Live school-portal authentication is not enabled in this test build"
            )
        return self._build_demo_snapshot()

    def _build_demo_snapshot(self) -> AccountSnapshot:
        now = dt_util.now()
        if self._demo_anchor is None:
            self._demo_anchor = now.replace(second=0, microsecond=0)

        anchor = self._demo_anchor
        week_start = anchor - timedelta(days=anchor.weekday())
        students: list[StudentSnapshot] = []
        subject_pool = (
            "Matematyka",
            "Język polski",
            "Język angielski",
            "Przyroda",
            "Historia",
            "Informatyka",
            "Plastyka",
            "Muzyka",
            "WF",
        )

        for index in range(self._demo_students):
            student_no = index + 1
            student = Student(
                student_id=f"demo_{student_no}",
                name=f"Dziecko {student_no}",
                class_name=f"{student_no + 3}A",
            )
            if index == 0:
                current_attendance = ATTENDANCE_ABSENT
            elif index == 1:
                current_attendance = ATTENDANCE_LATE
            else:
                current_attendance = ATTENDANCE_PRESENT

            lessons: list[Lesson] = []
            for weekday in range(5):
                day_date = (week_start + timedelta(days=weekday)).date()
                if weekday == anchor.weekday():
                    starts = (
                        anchor - timedelta(minutes=150),
                        anchor - timedelta(minutes=95),
                        anchor - timedelta(minutes=40),
                        anchor + timedelta(minutes=15),
                        anchor + timedelta(minutes=70),
                    )
                else:
                    day_base = (week_start + timedelta(days=weekday)).replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
                    starts = tuple(
                        day_base + timedelta(minutes=55 * lesson_index)
                        for lesson_index in range(5)
                    )

                for lesson_index, start in enumerate(starts, start=1):
                    subject = subject_pool[
                        (index * 2 + weekday * 3 + lesson_index - 1) % len(subject_pool)
                    ]
                    attendance = ATTENDANCE_PRESENT
                    if weekday == anchor.weekday() and lesson_index == 3:
                        attendance = current_attendance
                    lessons.append(
                        Lesson(
                            number=lesson_index,
                            subject=subject,
                            start=start,
                            end=start + timedelta(minutes=45),
                            room=(
                                "Sala gimnastyczna"
                                if subject == "WF"
                                else str(100 + weekday * 10 + lesson_index + index)
                            ),
                            teacher="Nauczyciel testowy",
                            attendance=attendance,
                        )
                    )

            grades = (
                Grade(
                    grade_id=f"demo-grade-{student_no}-1",
                    subject=subject_pool[(index + 1) % len(subject_pool)],
                    value="5" if index % 2 == 0 else "4+",
                    date=anchor - timedelta(hours=2),
                    description="Sprawdzian — wpis testowy",
                ),
            )
            remarks = (
                Remark(
                    remark_id=f"demo-remark-{student_no}-1",
                    date=anchor - timedelta(hours=1),
                    text=(
                        "Bardzo dobre przygotowanie do zajęć."
                        if index % 2 == 0
                        else "Prośba o uzupełnienie zaległego zadania."
                    ),
                    author="Nauczyciel testowy",
                    category="Informacja",
                ),
            )
            students.append(
                StudentSnapshot(
                    student=student,
                    lessons=tuple(sorted(lessons, key=lambda item: item.start)),
                    grades=grades,
                    remarks=remarks,
                )
            )

        return AccountSnapshot(students=tuple(students), updated_at=now)
