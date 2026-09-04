"""Modular school API client used by mojV live mode."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Protocol


class JsonTransport(Protocol):
    async def get_json(self, path: str, params: dict[str, Any]) -> Any:
        """Return JSON data for one authenticated request."""


class MessagesClient(Protocol):
    async def fetch(
        self,
        city: str,
        mailbox_key: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Return inbox metadata and detail payloads for one mailbox."""


@dataclass(frozen=True, slots=True)
class StudentContext:
    student_id: str
    name: str
    class_name: str
    base_url: str
    session_key: str
    journal_id: str = ""
    city: str = ""
    mailbox_key: str = ""


@dataclass(slots=True)
class RawStudentBundle:
    student: StudentContext
    timetable: Any = None
    attendance: Any = None
    attendance_subjects: Any = None
    attendance_summary: Any = None
    attendance_by_subject: dict[str, Any] = field(default_factory=dict)
    classification_periods: Any = None
    grades_by_period: dict[str, Any] = field(default_factory=dict)
    remarks: Any = None
    schoolwork: Any = None
    messages: Any = None
    message_details: dict[str, Any] = field(default_factory=dict)
    achievements: Any = None
    meetings: Any = None
    lucky_number: Any = None
    errors: dict[str, str] = field(default_factory=dict)


class SchoolApiClient:
    """Fetch independent school modules with failure isolation."""

    def __init__(
        self,
        transport: JsonTransport,
        *,
        messages: MessagesClient | None = None,
    ) -> None:
        self._transport = transport
        self._messages = messages

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
            "attendance_subjects": self._transport.get_json(
                f"{student.base_url}/api/Przedmioty", common
            ),
            "attendance_summary": self._transport.get_json(
                f"{student.base_url}/api/FrekwencjaStatystyki",
                {**common, "idPrzedmiot": -1},
            ),
            "remarks": self._transport.get_json(f"{student.base_url}/api/Uwagi", common),
            "schoolwork": self._transport.get_json(
                f"{student.base_url}/api/SprawdzianyZadaniaDomowe",
                {
                    **common,
                    "dataOd": self._stamp(schoolwork_from, start=True),
                    "dataDo": self._stamp(schoolwork_to, start=False),
                },
            ),
            "achievements": self._transport.get_json(
                f"{student.base_url}/api/Osiagniecia", common
            ),
            "meetings": self._transport.get_json(
                f"{student.base_url}/api/Zebrania", common
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

        await asyncio.gather(
            self._fetch_grades(student, bundle),
            self._fetch_attendance_by_subject(student, bundle),
            self._fetch_messages(student, bundle),
        )
        return bundle

    async def _fetch_grades(self, student: StudentContext, bundle: RawStudentBundle) -> None:
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
                {"key": student.session_key, "idOkresKlasyfikacyjny": period_id},
            )
            for period_id in period_ids
        )
        results = await asyncio.gather(*requests, return_exceptions=True)
        for period_id, result in zip(period_ids, results, strict=True):
            if isinstance(result, Exception):
                bundle.errors[f"grades:{period_id}"] = self._error_text(result)
            else:
                bundle.grades_by_period[period_id] = result

    async def _fetch_attendance_by_subject(
        self,
        student: StudentContext,
        bundle: RawStudentBundle,
    ) -> None:
        subjects = bundle.attendance_subjects
        if not isinstance(subjects, list):
            return
        rows = [
            row
            for row in subjects
            if isinstance(row, dict)
            and row.get("id") is not None
            and str(row.get("id")) != "-1"
        ]
        if not rows:
            return
        requests = tuple(
            self._transport.get_json(
                f"{student.base_url}/api/FrekwencjaStatystyki",
                {"key": student.session_key, "idPrzedmiot": row["id"]},
            )
            for row in rows
        )
        results = await asyncio.gather(*requests, return_exceptions=True)
        for row, result in zip(rows, results, strict=True):
            subject_id = str(row["id"])
            if isinstance(result, Exception):
                bundle.errors[f"attendance_stats:{subject_id}"] = self._error_text(result)
            else:
                bundle.attendance_by_subject[subject_id] = result

    async def _fetch_messages(self, student: StudentContext, bundle: RawStudentBundle) -> None:
        if self._messages is None or not student.city or not student.mailbox_key:
            return
        try:
            inbox, details = await self._messages.fetch(student.city, student.mailbox_key)
        except Exception as err:
            bundle.errors["messages"] = self._error_text(err)
            return
        bundle.messages = inbox
        bundle.message_details = details

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
        return type(error).__name__
