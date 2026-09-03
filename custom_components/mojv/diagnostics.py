"""Diagnostics support for mojV."""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_REDACT = {"password", "key", "cookies", "cookie", "token", "username"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return safe diagnostics for a mojV config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), _REDACT),
        "students": [
            {
                "student_id": snapshot.student.student_id,
                "name": snapshot.student.name,
                "class": snapshot.student.class_name,
                "lesson_count": len(snapshot.lessons),
            }
            for snapshot in coordinator.data.students
        ],
        "updated_at": coordinator.data.updated_at.isoformat(),
        "last_update_success": coordinator.last_update_success,
    }
