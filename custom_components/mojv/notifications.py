"""Notifications and Home Assistant events for mojV."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import ATTENDANCE_ABSENT, ATTENDANCE_LATE, DOMAIN
from .coordinator import MojVCoordinator
from .logic import active_lesson

EVENT_LATE = "mojv_lesson_late"
EVENT_ABSENT = "mojv_lesson_absent"
EVENT_GRADE = "mojv_new_grade"
EVENT_REMARK = "mojv_new_remark"


class MojVNotificationManager:
    """Detect meaningful school changes and publish HA notifications/events."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: MojVCoordinator,
        entry_id: str,
        *,
        demo_mode: bool = False,
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.demo_mode = demo_mode
        self.store: Store[dict] = Store(hass, 1, f"{DOMAIN}_notifications_{entry_id}")
        self.seen_grades: set[str] = set()
        self.seen_remarks: set[str] = set()
        self.attendance_state: dict[str, str] = {}
        self._remove_listener: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Load state and start observing coordinator updates."""
        stored = await self.store.async_load()
        first_run = stored is None
        if stored:
            self.seen_grades = set(stored.get("seen_grades", []))
            self.seen_remarks = set(stored.get("seen_remarks", []))
            self.attendance_state = dict(stored.get("attendance_state", {}))

        if first_run and not self.demo_mode:
            for snapshot in self.coordinator.data.students:
                self.seen_grades.update(grade.grade_id for grade in snapshot.grades)
                self.seen_remarks.update(remark.remark_id for remark in snapshot.remarks)

        await self._async_process()
        self._remove_listener = self.coordinator.async_add_listener(self._schedule_process)

    def async_stop(self) -> None:
        """Stop observing updates."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def _schedule_process(self) -> None:
        self.hass.async_create_task(self._async_process())

    async def _async_process(self) -> None:
        now = dt_util.now()
        for snapshot in self.coordinator.data.students:
            student = snapshot.student
            lesson = active_lesson(snapshot, now)
            if lesson and lesson.attendance in (ATTENDANCE_LATE, ATTENDANCE_ABSENT):
                signature = f"{lesson.start.isoformat()}:{lesson.attendance}"
                if self.attendance_state.get(student.student_id) != signature:
                    self.attendance_state[student.student_id] = signature
                    if lesson.attendance == ATTENDANCE_LATE:
                        event_type = EVENT_LATE
                        title = f"{student.name}: spóźnienie"
                        message = f"Spóźnienie na lekcję: {lesson.subject}."
                    else:
                        event_type = EVENT_ABSENT
                        title = f"{student.name}: nieobecność"
                        message = f"Brak obecności na lekcji: {lesson.subject}."
                    self._notify(event_type, student.student_id, title, message, {
                        "student": student.name,
                        "subject": lesson.subject,
                        "lesson_number": lesson.number,
                        "start": lesson.start.isoformat(),
                    })

            for grade in snapshot.grades:
                if grade.grade_id in self.seen_grades:
                    continue
                self.seen_grades.add(grade.grade_id)
                self._notify(
                    EVENT_GRADE,
                    student.student_id,
                    f"{student.name}: nowa ocena {grade.value}",
                    f"{grade.subject}: {grade.value} — {grade.description or 'nowy wpis'}",
                    {
                        "student": student.name,
                        "subject": grade.subject,
                        "grade": grade.value,
                        "description": grade.description,
                        "date": grade.date.isoformat(),
                    },
                )

            for remark in snapshot.remarks:
                if remark.remark_id in self.seen_remarks:
                    continue
                self.seen_remarks.add(remark.remark_id)
                self._notify(
                    EVENT_REMARK,
                    student.student_id,
                    f"{student.name}: nowa uwaga",
                    remark.text,
                    {
                        "student": student.name,
                        "text": remark.text,
                        "author": remark.author,
                        "category": remark.category,
                        "date": remark.date.isoformat(),
                    },
                )

        await self.store.async_save(
            {
                "seen_grades": sorted(self.seen_grades),
                "seen_remarks": sorted(self.seen_remarks),
                "attendance_state": self.attendance_state,
            }
        )

    def _notify(
        self,
        event_type: str,
        student_id: str,
        title: str,
        message: str,
        data: dict,
    ) -> None:
        persistent_notification.async_create(
            self.hass,
            message,
            title=title,
            notification_id=f"{DOMAIN}_{event_type}_{student_id}",
        )
        self.hass.bus.async_fire(event_type, data)
