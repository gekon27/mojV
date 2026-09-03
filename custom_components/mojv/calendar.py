"""Calendar platform for mojV."""
from __future__ import annotations

from datetime import datetime

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
    async_add_entities(
        MojVSchoolCalendar(coordinator, item.student.student_id)
        for item in coordinator.data.students
    )


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
