"""Modular school API client used by mojV live-data research.

This module is a clean-room implementation. It models observed service
capabilities but does not reuse implementation code from other projects.
"""
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
        """Fetch the high-value modules for one student concurrently."""
        bundle = RawStudentBundle(student=student)
        common = {"key": student.session_key}
        timetable_from = now - timedelta(days=now.weekday() + 7)
        timetable_to = now + timedelta(days=21)
        work_from = now.replace(day=1) - timedelta(days=1)
        work_to = now + timedelta(days=61)

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
            "attendance_subjects": self._transport.get_json(
                f"{student.base_url}/api/Przedmioty", common
            ),
            "attendance_summary": self._transport.get_json(
                f"{student.base_url}/api/FrekwencjaStatystyki",
                {**common, "idPrzedmiot": -1},
            ),
            "classification_periods": self._transport.get_json(
                f"{student.base_url}/api/OkresyKlasyfikacyjne",
                {**common, "idDziennik": student.journal_id},
            ),
            "remarks": self._transport.get_json(
                f"{student.base_url}/api/Uwagi", common
            ),
            "schoolwork": self._transport.get_json(
                f"{student.base_url}/api/SprawdzianyZadaniaDomowe",
                {
                    **common,
                    "dataOd": self._stamp(work_from, start=True),
                    "dataDo": self._stamp(work_to, start=False),
                },
            ),
            "achievements": self._transport.get_json(
                f"{student.base_url}/api/Osiagniecia", common
            ),
            "meetings": self._transport.get_json(
                f"{student.base_url}/api/Zebrania", common
            ),
            "lucky_number": self._transport.get_json(
                f"{student.base_url}/api/SzczesliwyNumerTablica", common
            ),
        }

        names = tuple(requests)
        results = await asyncio.gather(*requests.values(), return_exceptions=True)
        for name, result in zip(names, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[name] = f"{type(result).__name__}: {result}"
            else:
                setattr(bundle, name, result)

        await self._fetch_grades(bundle)
        return bundle

    async def fetch_many(
        self,
        students: tuple[StudentContext, ...],
        *,
        now: datetime,
    ) -> tuple[RawStudentBundle, ...]:
        """Fetch all students concurrently without coupling their failures."""
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

    async def _fetch_grades(self, bundle: RawStudentBundle) -> None:
        periods = self._as_records(bundle.classification_periods)
        if not periods:
            return

        tasks: list[tuple[str, Any]] = []
        for period in periods:
            period_id = str(period.get("id", ""))
            if not period_id:
                continue
            label = str(period.get("numerOkresu", period_id))
            tasks.append(
                (
                    label,
                    self._transport.get_json(
                        f"{bundle.student.base_url}/api/Oceny",
                        {
                            "key": bundle.student.session_key,
                            "idOkresKlasyfikacyjny": period_id,
                        },
                    ),
                )
            )

        if not tasks:
            return
        results = await asyncio.gather(
            *(task for _, task in tasks), return_exceptions=True
        )
        for (label, _), result in zip(tasks, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[f"grades:{label}"] = (
                    f"{type(result).__name__}: {result}"
                )
            else:
                bundle.grades_by_period[label] = result

    @staticmethod
    def _as_records(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("data", "items", "lista", "records"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    @staticmethod
    def _stamp(value: datetime, *, start: bool) -> str:
        suffix = "00:00:00.000Z" if start else "23:59:59.999Z"
        return f"{value:%Y-%m-%d}T{suffix}"
