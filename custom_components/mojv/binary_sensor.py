"""Binary sensor platform for mojV."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
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
