"""Bounded public notification history for mojV."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .notification_rules import NotificationCandidate

MAX_HISTORY = 200


class NotificationHistory:
    """Persist a bounded, deduplicated public notification history."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, 1, f"{DOMAIN}_notification_history_{entry_id}"
        )
        self._rows: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        """Load saved public rows."""
        stored = await self._store.async_load() or {}
        rows = stored.get("rows", [])
        self._rows = [dict(row) for row in rows if isinstance(row, dict)][:MAX_HISTORY]

    async def async_append(self, candidate: NotificationCandidate) -> bool:
        """Append candidate unless it already exists."""
        if any(row.get("event_id") == candidate.event_id for row in self._rows):
            return False
        row = asdict(candidate)
        row["created_at"] = candidate.created_at.isoformat()
        self._rows.insert(0, row)
        del self._rows[MAX_HISTORY:]
        await self.async_save()
        return True

    async def async_save(self) -> None:
        """Persist current rows."""
        await self._store.async_save({"rows": self._rows[:MAX_HISTORY]})

    def as_panel_rows(self) -> list[dict[str, Any]]:
        """Return newest-first public rows for the sidebar panel."""
        return [dict(row) for row in self._rows[:MAX_HISTORY]]
