"""Modular school API client used by mojV live mode."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Protocol


class JsonTransport(Protocol):
    """Minimal transport required by the school API client."""

    async def get_json(self, path: str, params: dict[str, Any]) -> Any:
        """Return JSON data for one authenticated request."""


@dataclass(frozen=True, slots=True)
class StudentContext:
    """Authenticated routing data for one student."""

    student_id: str
    name: str
    class_name: str
    base_url: str
    session_key: str
    journal_id: str = ""


@dataclass(slots=True)
class RawStudentBundle:
    """Raw module payloads collected for one student."""

    student: StudentContext
    timetable: Any = None
    attendance: Any = None
    attendance_subjects: Any = None
    attendance_summary: Any = None
    classification_periods: Any = None
    grades_by_period: dict[str, Any] = field(default_factory=dict)
    remarks: Any = None
    schoolwork: Any = None
    achievements: Any = None
    meetings: Any = None
    lucky_number: Any = None
    errors: dict[str, str] = field(default_factory=dict)


class SchoolApiClient:
    """Fetch independent school modules with failure isolation."""

    def __init__(self, transport: JsonTransport) -> None:
        self._transport = transport

    async def fetch_student(
        self,
        student: StudentContext,
        *,
        now: datetime,
    ) -> RawStudentBundle:
        bundle = RawStudentBundle(student=student)
        common = {"key": student.session_key}
        timetable_from = now - timedelta(days=now.weekday() + 7)
        timetable_to = now + timedelta(days=21)

        requests = {
            "timetable": self._transport.get_json(
                f"{student.base_url}/api/PlanZajec",
                {
                    **common,
                    "dataOd": self._stamp(timetable_from, start=True),
                    "dataDo": self._stamp(timetable_to, start=False),
                },
            ),
            "attendance": self._transport.get_json(
                f"{student.base_url}/api/Frekwencja", common
            ),
        }

        names = tuple(requests)
        results = await asyncio.gather(*requests.values(), return_exceptions=True)
        for name, result in zip(names, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[name] = f"{type(result).__name__}: {result}"
            else:
                setattr(bundle, name, result)
        return bundle

    async def fetch_many(
        self,
        students: tuple[StudentContext, ...],
        *,
        now: datetime,
    ) -> tuple[RawStudentBundle, ...]:
        results = await asyncio.gather(
            *(self.fetch_student(student, now=now) for student in students),
            return_exceptions=True,
        )
        bundles: list[RawStudentBundle] = []
        for student, result in zip(students, results, strict=True):
            if isinstance(result, Exception):
                bundles.append(
                    RawStudentBundle(
                        student=student,
                        errors={"student": f"{type(result).__name__}: {result}"},
                    )
                )
            else:
                bundles.append(result)
        return tuple(bundles)

    @staticmethod
    def _stamp(value: datetime, *, start: bool) -> str:
        suffix = "00:00:00.000Z" if start else "23:59:59.999Z"
        return f"{value:%Y-%m-%d}T{suffix}"
