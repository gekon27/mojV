"""Sensor platform for mojV."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTENDANCE_NOT_RECORDED, DOMAIN
from .coordinator import MojVCoordinator
from .entity import MojVStudentEntity
from .logic import active_lesson, lessons_today, minutes_to_end, next_lesson


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mojV sensors."""
    coordinator: MojVCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [MojVStudentsSensor(coordinator)]
    for snapshot in coordinator.data.students:
        student_id = snapshot.student.student_id
        entities.extend(
            (
                MojVCurrentLessonSensor(coordinator, student_id),
                MojVNextLessonSensor(coordinator, student_id),
                MojVLessonNumberSensor(coordinator, student_id),
                MojVMinutesToEndSensor(coordinator, student_id),
                MojVAttendanceSensor(coordinator, student_id),
                MojVTodayScheduleSensor(coordinator, student_id),
                MojVLastSyncSensor(coordinator, student_id),
            )
        )
    async_add_entities(entities)


class MojVStudentsSensor(CoordinatorEntity[MojVCoordinator], SensorEntity):
    """Number of students detected on the account."""

    _attr_name = "mojV uczniowie"
    _attr_icon = "mdi:account-school"

    def __init__(self, coordinator: MojVCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "mojv_students"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.students)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "students": [
                {
                    "id": item.student.student_id,
                    "name": item.student.name,
                    "class": item.student.class_name,
                }
                for item in self.coordinator.data.students
            ]
        }


class _StudentSensor(MojVStudentEntity, SensorEntity):
    key = ""
    label = ""

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_{self.key}"
        self._attr_name = self.label


class MojVCurrentLessonSensor(_StudentSensor):
    key = "current_lesson"
    label = "Aktualna lekcja"
    _attr_icon = "mdi:book-open-page-variant"

    @property
    def native_value(self) -> str:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.subject if lesson else "Przerwa"

    @property
    def extra_state_attributes(self) -> dict:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        if lesson is None:
            return {"active": False}
        return {
            "active": True,
            "number": lesson.number,
            "start": lesson.start.isoformat(),
            "end": lesson.end.isoformat(),
            "room": lesson.room,
            "teacher": lesson.teacher,
            "attendance": lesson.attendance,
        }


class MojVNextLessonSensor(_StudentSensor):
    key = "next_lesson"
    label = "Następna lekcja"
    _attr_icon = "mdi:book-arrow-right"

    @property
    def native_value(self) -> str:
        lesson = next_lesson(self.student_snapshot, dt_util.now())
        return lesson.subject if lesson else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        lesson = next_lesson(self.student_snapshot, dt_util.now())
        if lesson is None:
            return {}
        return {
            "number": lesson.number,
            "start": lesson.start.isoformat(),
            "end": lesson.end.isoformat(),
            "room": lesson.room,
            "teacher": lesson.teacher,
            "attendance": lesson.attendance,
        }


class MojVLessonNumberSensor(_StudentSensor):
    key = "lesson_number"
    label = "Numer lekcji"
    _attr_icon = "mdi:numeric"

    @property
    def native_value(self) -> int:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.number if lesson else 0


class MojVMinutesToEndSensor(_StudentSensor):
    key = "minutes_to_end"
    label = "Minuty do końca"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"

    @property
    def native_value(self) -> int:
        now = dt_util.now()
        return minutes_to_end(active_lesson(self.student_snapshot, now), now)


class MojVAttendanceSensor(_StudentSensor):
    key = "attendance"
    label = "Obecność"
    _attr_icon = "mdi:account-check"

    @property
    def native_value(self) -> str:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.attendance if lesson else ATTENDANCE_NOT_RECORDED


class MojVTodayScheduleSensor(_StudentSensor):
    key = "today_schedule"
    label = "Plan dzisiaj"
    _attr_icon = "mdi:calendar-today"

    @property
    def native_value(self) -> int:
        return len(lessons_today(self.student_snapshot, dt_util.now()))

    @property
    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        current = active_lesson(self.student_snapshot, now)
        return {
            "lessons": [
                {
                    "number": lesson.number,
                    "subject": lesson.subject,
                    "start": lesson.start.isoformat(),
                    "end": lesson.end.isoformat(),
                    "room": lesson.room,
                    "teacher": lesson.teacher,
                    "attendance": lesson.attendance,
                    "cancelled": lesson.cancelled,
                    "current": current == lesson,
                }
                for lesson in lessons_today(self.student_snapshot, now)
            ]
        }


class MojVLastSyncSensor(_StudentSensor):
    key = "last_sync"
    label = "Ostatnia synchronizacja"
    _attr_icon = "mdi:cloud-sync"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.updated_at.isoformat()
