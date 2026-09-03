"""Data client for mojV."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import json
from typing import Any
from urllib.parse import urlparse

import aiohttp
from homeassistant.util import dt as dt_util

from .auth import (
    MojVAuthError,
    MojVBrowserVerificationRequired,
    MojVCannotConnect,
    MojVInvalidAuth,
    MojVNoStudents,
    StudentTarget,
    async_login,
    create_session,
)
from .const import (
    ATTENDANCE_ABSENT,
    ATTENDANCE_LATE,
    ATTENDANCE_PRESENT,
    AUTH_BACKEND_HELPER,
    AUTH_BACKEND_HTTP,
    MODE_DEMO,
)
from .helper_gateway import (
    HelperGateway,
    HelperInvalidAuth,
    HelperRequestError,
    HelperUnavailable,
)
from .messages_api import MessagesApiClient, messages_base
from .models import AccountSnapshot, Grade, Lesson, Remark, Student, StudentSnapshot
from .school_api import SchoolApiClient, StudentContext
from .snapshot_builder import build_student_snapshot


class MojVClientError(Exception):
    """Base mojV client error."""


class MojVLiveAuthPending(MojVClientError):
    """Compatibility alias for older diagnostics."""


class _SessionExpired(Exception):
    """Authenticated session is no longer accepted."""


async def _decode_json_response(response: aiohttp.ClientResponse, path: str) -> Any:
    raw = await response.text(errors="replace")
    if response.status in (401, 403):
        raise _SessionExpired(f"HTTP {response.status}")
    if response.status >= 400:
        raise MojVClientError(f"HTTP {response.status} for {urlparse(path).path}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as err:
        raise MojVClientError(f"Invalid JSON returned by {urlparse(path).path}") from err


class _JsonTransport:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_json(self, path: str, params: dict[str, Any]) -> Any:
        try:
            async with self._session.get(
                path,
                params=params,
                headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
            ) as response:
                return await _decode_json_response(response, path)
        except (_SessionExpired, MojVClientError):
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MojVClientError(type(err).__name__) from err


class _MessageSessionTransport:
    """Initialize and use the separate message SSO tenant on the account cookie jar."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._ready: set[str] = set()
        self._lock = asyncio.Lock()

    async def prepare(self, city: str) -> None:
        if city in self._ready:
            return
        async with self._lock:
            if city in self._ready:
                return
            base = messages_base(city)
            try:
                async with self._session.get(
                    f"{base}/App",
                    allow_redirects=True,
                    headers={
                        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{base}/App",
                    },
                ) as response:
                    await response.read()
                    if response.status in (401, 403):
                        raise _SessionExpired(f"HTTP {response.status}")
                    if response.status >= 400:
                        raise MojVClientError(f"Message SSO HTTP {response.status}")
                    expected_host = urlparse(base).netloc
                    if urlparse(str(response.url)).netloc != expected_host:
                        raise MojVClientError("Message SSO did not reach the message tenant")
            except (_SessionExpired, MojVClientError):
                raise
            except (aiohttp.ClientError, TimeoutError) as err:
                raise MojVClientError(type(err).__name__) from err
            self._ready.add(city)

    async def get_json(self, path: str, params: dict[str, Any]) -> Any:
        base = f"{urlparse(path).scheme}://{urlparse(path).netloc}"
        try:
            async with self._session.get(
                path,
                params=params,
                headers={
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{base}{urlparse(path).path.rsplit('/api/', 1)[0]}/App",
                },
            ) as response:
                return await _decode_json_response(response, path)
        except (_SessionExpired, MojVClientError):
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MojVClientError(type(err).__name__) from err


class MojVClient:
    """Fetch account data in demo or live mode."""

    def __init__(
        self,
        mode: str,
        demo_students: int = 2,
        *,
        username: str = "",
        password: str = "",
        auth_backend: str = AUTH_BACKEND_HTTP,
        helper_gateway: HelperGateway | None = None,
    ) -> None:
        self._mode = mode
        self._demo_students = demo_students
        self._username = username
        self._password = password
        self._auth_backend = auth_backend
        self._helper_gateway = helper_gateway
        self._demo_anchor = None
        self._session: aiohttp.ClientSession | None = None
        self._targets: tuple[StudentTarget, ...] = ()

    async def async_fetch(self) -> AccountSnapshot:
        """Fetch data for all students."""
        if self._mode == MODE_DEMO:
            return self._build_demo_snapshot()
        if self._auth_backend == AUTH_BACKEND_HELPER:
            return await self._async_fetch_helper()
        return await self._async_fetch_live()

    async def async_close(self) -> None:
        """Close the dedicated direct-HTTP session, if one exists."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None
        self._targets = ()

    def _student_snapshot(
        self,
        *,
        student_id: str,
        name: str,
        class_name: str,
        timetable: Any,
        attendance: Any,
        attendance_subjects: Any = None,
        attendance_summary: Any = None,
        attendance_by_subject: dict[str, Any] | None = None,
        classification_periods: Any = None,
        grades_by_period: dict[str, Any] | None = None,
        remarks: Any = None,
        schoolwork: Any = None,
        messages: Any = None,
        message_details: dict[str, Any] | None = None,
        achievements: Any = None,
        meetings: Any = None,
    ) -> StudentSnapshot:
        return build_student_snapshot(
            student_id=student_id,
            name=name,
            class_name=class_name,
            timetable=timetable,
            attendance=attendance,
            attendance_subjects=attendance_subjects,
            attendance_summary=attendance_summary,
            attendance_by_subject=attendance_by_subject,
            classification_periods=classification_periods,
            grades_by_period=grades_by_period,
            remarks=remarks,
            schoolwork=schoolwork,
            messages=messages,
            message_details=message_details,
            achievements=achievements,
            meetings=meetings,
            timezone=dt_util.DEFAULT_TIME_ZONE,
        )

    async def _async_fetch_helper(self) -> AccountSnapshot:
        if not self._username or not self._password:
            raise MojVClientError("Brak danych logowania")
        if self._helper_gateway is None:
            raise MojVClientError("Lokalny helper logowania nie jest dostępny")
        try:
            payload = await self._helper_gateway.async_snapshot(self._username, self._password)
        except HelperInvalidAuth as err:
            raise MojVClientError("Nieprawidłowy login lub hasło") from err
        except HelperUnavailable as err:
            raise MojVClientError("Lokalny helper logowania nie jest uruchomiony") from err
        except HelperRequestError as err:
            raise MojVClientError(f"Błąd lokalnego helpera logowania: {err}") from err

        students: list[StudentSnapshot] = []
        for row in payload.get("students", []):
            if not isinstance(row, dict):
                continue
            students.append(
                self._student_snapshot(
                    student_id=str(row.get("student_id") or ""),
                    name=str(row.get("name") or ""),
                    class_name=str(row.get("class_name") or ""),
                    timetable=row.get("timetable"),
                    attendance=row.get("attendance"),
                    attendance_subjects=row.get("attendance_subjects"),
                    attendance_summary=row.get("attendance_summary"),
                    attendance_by_subject=row.get("attendance_by_subject"),
                    classification_periods=row.get("classification_periods"),
                    grades_by_period=row.get("grades_by_period"),
                    remarks=row.get("remarks"),
                    schoolwork=row.get("schoolwork"),
                    messages=row.get("messages"),
                    message_details=row.get("message_details"),
                    achievements=row.get("achievements"),
                    meetings=row.get("meetings"),
                )
            )
        if not students:
            raise MojVClientError("Nie otrzymano danych żadnego dziecka")
        return AccountSnapshot(students=tuple(students), updated_at=dt_util.now())

    async def _async_login(self) -> None:
        await self.async_close()
        self._session = create_session()
        try:
            self._targets = await async_login(self._session, self._username, self._password)
        except MojVBrowserVerificationRequired as err:
            await self.async_close()
            raise MojVClientError("Portal wymaga lokalnego helpera z pełną przeglądarką") from err
        except MojVInvalidAuth as err:
            await self.async_close()
            raise MojVClientError("Nieprawidłowy login lub hasło") from err
        except MojVNoStudents as err:
            await self.async_close()
            raise MojVClientError("Nie wykryto żadnego dziecka na koncie") from err
        except MojVCannotConnect as err:
            await self.async_close()
            raise MojVClientError(f"Nie można połączyć się z portalem: {err}") from err
        except MojVAuthError as err:
            await self.async_close()
            raise MojVClientError(str(err)) from err

    async def _mailbox_key(self, target: StudentTarget) -> str:
        """Read mailbox routing from the already authenticated student context."""
        assert self._session is not None
        try:
            payload = await _JsonTransport(self._session).get_json(
                f"{target.base_url}/api/Context", {}
            )
        except Exception:
            return ""
        current: Any = payload
        for _ in range(4):
            if not isinstance(current, dict):
                break
            nested = current.get("data") if isinstance(current.get("data"), (dict, list)) else current.get("result")
            if isinstance(nested, (dict, list)):
                current = nested
            else:
                break
        if isinstance(current, dict):
            current = current.get("uczniowie")
        if not isinstance(current, list):
            return ""
        for row in current:
            if not isinstance(row, dict):
                continue
            if str(row.get("key") or "") == target.key:
                return str(row.get("globalKeySkrzynka") or "").strip()
        return ""

    async def _async_fetch_live(self, *, retry_auth: bool = True) -> AccountSnapshot:
        if not self._username or not self._password:
            raise MojVClientError("Brak danych logowania")
        if self._session is None or self._session.closed or not self._targets:
            await self._async_login()
        assert self._session is not None

        mailbox_keys = await asyncio.gather(*(self._mailbox_key(target) for target in self._targets))
        contexts = tuple(
            StudentContext(
                student_id=target.student_id,
                name=target.name,
                class_name=target.class_name,
                base_url=target.base_url,
                session_key=target.key,
                journal_id=target.diary_id,
                city=target.base_url.rstrip("/").rsplit("/", 1)[-1],
                mailbox_key=mailbox_key,
            )
            for target, mailbox_key in zip(self._targets, mailbox_keys, strict=True)
        )
        api = SchoolApiClient(
            _JsonTransport(self._session),
            messages=MessagesApiClient(_MessageSessionTransport(self._session)),
        )
        now = dt_util.now()
        bundles = await api.fetch_many(contexts, now=now)

        if retry_auth and any(
            "_SessionExpired" in error
            for bundle in bundles
            for error in bundle.errors.values()
        ):
            await self._async_login()
            return await self._async_fetch_live(retry_auth=False)

        students = [
            self._student_snapshot(
                student_id=bundle.student.student_id,
                name=bundle.student.name,
                class_name=bundle.student.class_name,
                timetable=bundle.timetable,
                attendance=bundle.attendance,
                attendance_subjects=bundle.attendance_subjects,
                attendance_summary=bundle.attendance_summary,
                attendance_by_subject=bundle.attendance_by_subject,
                classification_periods=bundle.classification_periods,
                grades_by_period=bundle.grades_by_period,
                remarks=bundle.remarks,
                schoolwork=bundle.schoolwork,
                messages=bundle.messages,
                message_details=bundle.message_details,
                achievements=bundle.achievements,
                meetings=bundle.meetings,
            )
            for bundle in bundles
        ]
        if not students:
            raise MojVClientError("Nie otrzymano danych żadnego dziecka")
        return AccountSnapshot(students=tuple(students), updated_at=now)

    def _build_demo_snapshot(self) -> AccountSnapshot:
        now = dt_util.now()
        if self._demo_anchor is None:
            self._demo_anchor = now.replace(second=0, microsecond=0)
        anchor = self._demo_anchor
        week_start = anchor - timedelta(days=anchor.weekday())
        students: list[StudentSnapshot] = []
        subject_pool = (
            "Matematyka", "Język polski", "Język angielski", "Przyroda",
            "Historia", "Informatyka", "Plastyka", "Muzyka", "WF",
        )
        for index in range(self._demo_students):
            student_no = index + 1
            student = Student(
                student_id=f"demo_{student_no}",
                name=f"Dziecko {student_no}",
                class_name=f"{student_no + 3}A",
            )
            current_attendance = (
                ATTENDANCE_ABSENT if index == 0 else
                ATTENDANCE_LATE if index == 1 else ATTENDANCE_PRESENT
            )
            lessons: list[Lesson] = []
            for weekday in range(5):
                if weekday == anchor.weekday():
                    starts = (
                        anchor - timedelta(minutes=150), anchor - timedelta(minutes=95),
                        anchor - timedelta(minutes=40), anchor + timedelta(minutes=15),
                        anchor + timedelta(minutes=70),
                    )
                else:
                    day_base = (week_start + timedelta(days=weekday)).replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
                    starts = tuple(day_base + timedelta(minutes=55 * i) for i in range(5))
                for lesson_index, start in enumerate(starts, start=1):
                    subject = subject_pool[(index * 2 + weekday * 3 + lesson_index - 1) % len(subject_pool)]
                    attendance = ATTENDANCE_PRESENT
                    if weekday == anchor.weekday() and lesson_index == 3:
                        attendance = current_attendance
                    lessons.append(
                        Lesson(
                            number=lesson_index,
                            subject=subject,
                            start=start,
                            end=start + timedelta(minutes=45),
                            room="Sala gimnastyczna" if subject == "WF" else str(100 + weekday * 10 + lesson_index + index),
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
                    text="Bardzo dobre przygotowanie do zajęć." if index % 2 == 0 else "Prośba o uzupełnienie zaległego zadania.",
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
