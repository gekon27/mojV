"""Binary sensor platform for mojV."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import ATTENDANCE_ABSENT, ATTENDANCE_LATE, DOMAIN
from .coordinator import MojVCoordinator
from .entity import MojVStudentEntity
from .logic import active_lesson, minutes_to_end


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mojV binary sensors."""
    coordinator: MojVCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []
    for item in coordinator.data.students:
        student_id = item.student.student_id
        entities.extend(
            (
                MojVInLessonBinarySensor(coordinator, student_id),
                MojVLessonEndingBinarySensor(coordinator, student_id),
                MojVAbsentNowBinarySensor(coordinator, student_id),
                MojVLateNowBinarySensor(coordinator, student_id),
                MojVUnreadMessagesBinarySensor(coordinator, student_id),
                MojVSchoolworkDueBinarySensor(coordinator, student_id),
                MojVMeetingDueBinarySensor(coordinator, student_id),
                MojVImportantTodayBinarySensor(coordinator, student_id),
            )
        )
    async_add_entities(entities)


class MojVInLessonBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether a lesson is currently in progress."""

    _attr_name = "Trwa lekcja"
    _attr_icon = "mdi:school"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_in_lesson"

    @property
    def is_on(self) -> bool:
        return active_lesson(self.student_snapshot, dt_util.now()) is not None


class MojVLessonEndingBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether the current lesson is in its final five minutes."""

    _attr_name = "Lekcja kończy się"
    _attr_icon = "mdi:timer-alert-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_lesson_ending"

    @property
    def is_on(self) -> bool:
        now = dt_util.now()
        lesson = active_lesson(self.student_snapshot, now)
        if lesson is None:
            return False
        remaining = minutes_to_end(lesson, now)
        return 0 < remaining <= 5

    @property
    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        lesson = active_lesson(self.student_snapshot, now)
        if lesson is None:
            return {"minutes_to_end": 0}
        return {
            "minutes_to_end": minutes_to_end(lesson, now),
            "subject": lesson.subject,
            "lesson_number": lesson.number,
            "end": lesson.end.isoformat(),
        }


class MojVAbsentNowBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether the active lesson is currently marked absent."""

    _attr_name = "Nieobecny teraz"
    _attr_icon = "mdi:account-off-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_absent_now"

    @property
    def is_on(self) -> bool:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return bool(lesson and lesson.attendance == ATTENDANCE_ABSENT)

    @property
    def extra_state_attributes(self) -> dict:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return {
            "subject": lesson.subject if lesson else "",
            "lesson_number": lesson.number if lesson else 0,
        }


class MojVLateNowBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether the active lesson is currently marked late."""

    _attr_name = "Spóźniony teraz"
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_late_now"

    @property
    def is_on(self) -> bool:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return bool(lesson and lesson.attendance == ATTENDANCE_LATE)


class MojVUnreadMessagesBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether any school messages are unread."""

    _attr_name = "Nieprzeczytane wiadomości"
    _attr_icon = "mdi:email-alert-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_has_unread_messages"

    @property
    def is_on(self) -> bool:
        return any(item.unread for item in self.student_snapshot.messages)

    @property
    def extra_state_attributes(self) -> dict:
        return {"count": sum(1 for item in self.student_snapshot.messages if item.unread)}


class MojVSchoolworkDueBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether schoolwork is due within the next 24 hours."""

    _attr_name = "Termin w ciągu 24 h"
    _attr_icon = "mdi:clipboard-alert-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_schoolwork_due_24h"

    @property
    def _items(self):  # type: ignore[no-untyped-def]
        now = dt_util.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        limit = now + timedelta(hours=24)
        return sorted(
            (item for item in self.student_snapshot.schoolwork if day_start <= item.date <= limit),
            key=lambda item: item.date,
        )

    @property
    def is_on(self) -> bool:
        return bool(self._items)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "count": len(self._items),
            "next": (
                {
                    "date": self._items[0].date.isoformat(),
                    "subject": self._items[0].subject,
                    "title": self._items[0].title,
                    "kind": self._items[0].kind,
                }
                if self._items
                else None
            ),
        }


class MojVMeetingDueBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether a parent meeting starts within the next 24 hours."""

    _attr_name = "Zebranie w ciągu 24 h"
    _attr_icon = "mdi:account-group-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_meeting_due_24h"

    @property
    def _items(self):  # type: ignore[no-untyped-def]
        now = dt_util.now()
        limit = now + timedelta(hours=24)
        return sorted(
            (item for item in self.student_snapshot.meetings if now <= item.start <= limit),
            key=lambda item: item.start,
        )

    @property
    def is_on(self) -> bool:
        return bool(self._items)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "count": len(self._items),
            "next_start": self._items[0].start.isoformat() if self._items else None,
            "next_title": self._items[0].title if self._items else None,
        }


class MojVImportantTodayBinarySensor(MojVStudentEntity, BinarySensorEntity):
    """Whether the school portal reports important items today."""

    _attr_name = "Ważne dzisiaj"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_important_today"

    @property
    def is_on(self) -> bool:
        return bool(self.student_snapshot.important_today)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "count": len(self.student_snapshot.important_today),
            "items": [item.title for item in self.student_snapshot.important_today[:10]],
        }
