"""Persisted, user-created timetable rows for the mojV School panel."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

DATA_CUSTOM_SCHEDULE = f"{DOMAIN}_custom_schedule"
STORE_VERSION = 1


def _text(value: Any, field: str, *, required: bool = False) -> str:
    result = str(value or "").strip()
    if required and not result:
        raise vol.Invalid(f"{field} is required")
    if len(result) > 160:
        raise vol.Invalid(f"{field} is too long")
    return result


def _time(value: Any, field: str) -> str:
    result = _text(value, field, required=True)
    if len(result) != 5 or result[2] != ":":
        raise vol.Invalid(f"{field} must use HH:MM")
    try:
        hour, minute = (int(part) for part in result.split(":", 1))
    except ValueError as err:
        raise vol.Invalid(f"{field} must use HH:MM") from err
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise vol.Invalid(f"{field} is out of range")
    return result


def normalize_event(value: Mapping[str, Any], *, event_id: str | None = None) -> dict[str, Any]:
    """Validate one local recurring event without accepting portal identifiers."""
    weekday = value.get("weekday")
    if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
        raise vol.Invalid("weekday must be between 0 and 6")
    start = _time(value.get("start"), "start")
    end = _time(value.get("end"), "end")
    if end <= start:
        raise vol.Invalid("end must be after start")
    return {
        "id": event_id or uuid4().hex,
        "student_id": _text(value.get("student_id"), "student_id"),
        "weekday": weekday,
        "subject": _text(value.get("subject"), "subject", required=True),
        "start": start,
        "end": end,
        "room": _text(value.get("room"), "room"),
        "note": _text(value.get("note"), "note"),
    }


class CustomScheduleStore:
    """Small HA storage wrapper used only for local timetable additions."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, list[dict[str, Any]]]] = Store(
            hass, STORE_VERSION, DATA_CUSTOM_SCHEDULE
        )
        self._events: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        payload = await self._store.async_load() or {}
        events = payload.get("events", []) if isinstance(payload, dict) else []
        self._events = []
        for item in events:
            if not isinstance(item, Mapping):
                continue
            try:
                self._events.append(normalize_event(item, event_id=str(item.get("id") or "")))
            except vol.Invalid:
                continue

    def rows_for(self, student_id: str) -> list[dict[str, Any]]:
        return deepcopy([
            item for item in self._events if not item["student_id"] or item["student_id"] == student_id
        ])

    async def async_add(self, value: Mapping[str, Any]) -> dict[str, Any]:
        event = normalize_event(value)
        self._events.append(event)
        await self._store.async_save({"events": self._events})
        return deepcopy(event)

    async def async_remove(self, event_id: str) -> None:
        event_id = _text(event_id, "id", required=True)
        prior = len(self._events)
        self._events = [item for item in self._events if item["id"] != event_id]
        if len(self._events) == prior:
            raise vol.Invalid("event not found")
        await self._store.async_save({"events": self._events})
