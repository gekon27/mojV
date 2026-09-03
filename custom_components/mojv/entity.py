"""Shared entity helpers for mojV."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MojVCoordinator
from .models import StudentSnapshot


class MojVStudentEntity(CoordinatorEntity[MojVCoordinator]):
    """Base class for a student-specific entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator)
        self.student_id = student_id

    @property
    def student_snapshot(self) -> StudentSnapshot:
        for snapshot in self.coordinator.data.students:
            if snapshot.student.student_id == self.student_id:
                return snapshot
        raise RuntimeError(f"Student {self.student_id} disappeared from coordinator data")

    @property
    def device_info(self) -> DeviceInfo:
        student = self.student_snapshot.student
        return DeviceInfo(
            identifiers={(DOMAIN, student.student_id)},
            name=student.name,
            manufacturer="mojV",
            model=f"Uczeń {student.class_name}".strip(),
        )
