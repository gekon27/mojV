"""Data client for mojV.

The first HACS test build intentionally contains a deterministic demo backend.
The live eduVULCAN transport will replace only this boundary, while entities,
multi-student handling and Home Assistant plumbing stay unchanged.
"""
from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util

from .const import ATTENDANCE_LATE, ATTENDANCE_PRESENT, MODE_DEMO
from .models import AccountSnapshot, Lesson, Student, StudentSnapshot


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
                "Live eduVULCAN authentication is not enabled in this test build"
            )
        return self._build_demo_snapshot()

    def _build_demo_snapshot(self) -> AccountSnapshot:
        now = dt_util.now()
        if self._demo_anchor is None:
            self._demo_anchor = now.replace(second=0, microsecond=0)

        anchor = self._demo_anchor
        students: list[StudentSnapshot] = []
        subjects = (
            ("Matematyka", "Język polski", "Informatyka"),
            ("Język angielski", "Przyroda", "WF"),
            ("Historia", "Matematyka", "Plastyka"),
        )

        for index in range(self._demo_students):
            student_no = index + 1
            student = Student(
                student_id=f"demo_{student_no}",
                name=f"Dziecko {student_no}",
                class_name=f"{student_no + 3}A",
            )
            selected = subjects[index % len(subjects)]
            offset = timedelta(minutes=index * 2)
            lessons = (
                Lesson(
                    number=1,
                    subject=selected[0],
                    start=anchor - timedelta(minutes=40) + offset,
                    end=anchor + timedelta(minutes=5) + offset,
                    room=str(101 + index),
                    teacher="Nauczyciel testowy",
                    attendance=(
                        ATTENDANCE_LATE if index == 1 else ATTENDANCE_PRESENT
                    ),
                ),
                Lesson(
                    number=2,
                    subject=selected[1],
                    start=anchor + timedelta(minutes=15) + offset,
                    end=anchor + timedelta(minutes=60) + offset,
                    room=str(201 + index),
                    teacher="Nauczyciel testowy",
                    attendance=ATTENDANCE_PRESENT,
                ),
                Lesson(
                    number=3,
                    subject=selected[2],
                    start=anchor + timedelta(minutes=70) + offset,
                    end=anchor + timedelta(minutes=115) + offset,
                    room=(
                        "Sala gimnastyczna"
                        if selected[2] == "WF"
                        else str(301 + index)
                    ),
                    teacher="Nauczyciel testowy",
                ),
            )
            students.append(StudentSnapshot(student=student, lessons=lessons))

        return AccountSnapshot(students=tuple(students), updated_at=now)
