"""Calendar platform for mojV."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import MojVCoordinator
from .entity import MojVStudentEntity
from .logic import active_lesson, next_lesson


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mojV calendars."""
    coordinator: MojVCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[CalendarEntity] = []
    for item in coordinator.data.students:
        student_id = item.student.student_id
        entities.extend(
            (
                MojVSchoolCalendar(coordinator, student_id),
                MojVSchoolworkCalendar(coordinator, student_id),
                MojVMeetingsCalendar(coordinator, student_id),
            )
        )
    async_add_entities(entities)


class MojVSchoolCalendar(MojVStudentEntity, CalendarEntity):
    """School lesson calendar for one student."""

    _attr_name = "Plan lekcji"
    _attr_icon = "mdi:calendar-school"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_school_calendar"

    @staticmethod
    def _event_from_lesson(lesson) -> CalendarEvent:
        status = " [ODWOŁANA]" if lesson.cancelled else ""
        details = []
        if lesson.teacher:
            details.append(f"Nauczyciel: {lesson.teacher}")
        details.append(f"Obecność: {lesson.attendance}")
        return CalendarEvent(
            summary=f"{lesson.number}. {lesson.subject}{status}",
            start=lesson.start,
            end=lesson.end,
            description="\n".join(details),
            location=lesson.room or None,
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        lesson = active_lesson(self.student_snapshot, now) or next_lesson(
            self.student_snapshot, now
        )
        return self._event_from_lesson(lesson) if lesson else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return lessons within the requested calendar range."""
        return [
            self._event_from_lesson(lesson)
            for lesson in self.student_snapshot.lessons
            if lesson.end >= start_date and lesson.start <= end_date
        ]


class MojVSchoolworkCalendar(MojVStudentEntity, CalendarEntity):
    """Tests, quizzes, homework and other dated school work."""

    _attr_name = "Terminarz szkolny"
    _attr_icon = "mdi:clipboard-text-clock-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_schoolwork_calendar"

    @staticmethod
    def _event_from_item(item) -> CalendarEvent:
        summary = item.title or item.kind or "Termin szkolny"
        details = [f"Przedmiot: {item.subject}"] if item.subject else []
        if item.teacher:
            details.append(f"Nauczyciel: {item.teacher}")
        if item.created_at:
            details.append(f"Utworzone: {item.created_at:%d.%m.%Y %H:%M}")
        if item.due_at:
            details.append(f"Termin: {item.due_at:%d.%m.%Y %H:%M}")
        if item.description:
            details.append(f"Opis: {item.description}")
        event_time = item.due_at or item.date
        return CalendarEvent(
            summary=summary,
            start=event_time,
            end=event_time + timedelta(hours=1),
            description="\n".join(details) or None,
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        rows = sorted(
            (item for item in self.student_snapshot.schoolwork if item.date >= day_start),
            key=lambda item: item.date,
        )
        return self._event_from_item(rows[0]) if rows else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return schoolwork within the requested calendar range."""
        return [
            self._event_from_item(item)
            for item in self.student_snapshot.schoolwork
            if start_date <= item.date <= end_date
        ]


class MojVMeetingsCalendar(MojVStudentEntity, CalendarEntity):
    """Parent meeting or consultation."""

    _attr_name = "Zebrania i konsultacje"
    _attr_icon = "mdi:account-group-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_meetings_calendar"

    @staticmethod
    def _event_from_item(item) -> CalendarEvent:
        details = []
        if item.description:
            details.append(item.description)
        if item.online_url:
            details.append(f"Online: {item.online_url}")
        return CalendarEvent(
            summary=item.title or "Zebranie",
            start=item.start,
            end=item.start + timedelta(hours=1),
            description="\n".join(details) or None,
            location=item.location or None,
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        rows = sorted(
            (item for item in self.student_snapshot.meetings if item.start >= now),
            key=lambda item: item.start,
        )
        return self._event_from_item(rows[0]) if rows else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return meetings within the requested calendar range."""
        return [
            self._event_from_item(item)
            for item in self.student_snapshot.meetings
            if start_date <= item.start <= end_date
        ]
