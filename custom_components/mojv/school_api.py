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
        schoolwork_from = now.replace(day=1) - timedelta(days=1)
        schoolwork_to = now + timedelta(days=61)

        requests: dict[str, Any] = {
            "timetable": self._transport.get_json(
                f"{student.base_url}/api/PlanZajec",
                {
                    **common,
                    "dataOd": self._stamp(timetable_from, start=True),
                    "dataDo": self._stamp(timetable_to, start=False),
                    "zakresDanych": "2",
                },
            ),
            "attendance": self._transport.get_json(
                f"{student.base_url}/api/Frekwencja", common
            ),
            "schoolwork": self._transport.get_json(
                f"{student.base_url}/api/SprawdzianyZadaniaDomowe",
                {
                    **common,
                    "dataOd": self._stamp(schoolwork_from, start=True),
                    "dataDo": self._stamp(schoolwork_to, start=False),
                },
            ),
        }
        if student.journal_id:
            requests["classification_periods"] = self._transport.get_json(
                f"{student.base_url}/api/OkresyKlasyfikacyjne",
                {**common, "idDziennik": student.journal_id},
            )

        names = tuple(requests)
        results = await asyncio.gather(*requests.values(), return_exceptions=True)
        for name, result in zip(names, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[name] = self._error_text(result)
            else:
                setattr(bundle, name, result)

        await self._fetch_grades(student, bundle)
        return bundle

    async def _fetch_grades(
        self,
        student: StudentContext,
        bundle: RawStudentBundle,
    ) -> None:
        periods = bundle.classification_periods
        if not student.journal_id or not isinstance(periods, list):
            return

        period_ids = tuple(
            str(row.get("id"))
            for row in periods
            if isinstance(row, dict) and row.get("id") is not None
        )
        if not period_ids:
            return

        requests = tuple(
            self._transport.get_json(
                f"{student.base_url}/api/Oceny",
                {
                    "key": student.session_key,
                    "idOkresKlasyfikacyjny": period_id,
                },
            )
            for period_id in period_ids
        )
        results = await asyncio.gather(*requests, return_exceptions=True)
        for period_id, result in zip(period_ids, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[f"grades:{period_id}"] = self._error_text(result)
            else:
                bundle.grades_by_period[period_id] = result

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
                        errors={"student": self._error_text(result)},
                    )
                )
            else:
                bundles.append(result)
        return tuple(bundles)

    @staticmethod
    def _stamp(value: datetime, *, start: bool) -> str:
        suffix = "00:00:00.000Z" if start else "23:59:59.999Z"
        return f"{value:%Y-%m-%d}T{suffix}"

    @staticmethod
    def _error_text(error: Exception) -> str:
        """Return short diagnostic text without request parameters or auth data."""
        return type(error).__name__
