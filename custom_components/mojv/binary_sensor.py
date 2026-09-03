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
from .logic import active_lesson


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mojV binary sensors."""
    coordinator: MojVCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        MojVInLessonBinarySensor(coordinator, item.student.student_id)
        for item in coordinator.data.students
    )


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
