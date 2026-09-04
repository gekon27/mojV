"""Notification Engine v2 and Home Assistant delivery for mojV."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import time
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NOTIFY_TARGETS,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_HOURS_END,
    CONF_QUIET_HOURS_START,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DOMAIN,
)
from .coordinator import MojVCoordinator
from .notification_history import NotificationHistory
from .notification_rules import (
    NotificationCandidate,
    build_change_candidates,
    build_time_candidates,
)

_LOGGER = logging.getLogger(__name__)

EVENT_LATE = "mojv_lesson_late"
EVENT_ABSENT = "mojv_lesson_absent"
EVENT_GRADE = "mojv_new_grade"
EVENT_REMARK = "mojv_new_remark"
EVENT_NOTIFICATION = "mojv_notification"

_LEGACY_EVENTS = {
    "late": EVENT_LATE,
    "absence": EVENT_ABSENT,
    "grade": EVENT_GRADE,
    "remark": EVENT_REMARK,
    "praise": EVENT_REMARK,
}


class MojVNotificationManager:
    """Detect school changes and deliver deduplicated Home Assistant alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: MojVCoordinator,
        entry_id: str,
        *,
        demo_mode: bool = False,
        options: dict[str, Any] | None = None,
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.demo_mode = demo_mode
        self.options = dict(options or {})
        self.store: Store[dict[str, Any]] = Store(
            hass, 2, f"{DOMAIN}_notifications_{entry_id}"
        )
        self.history = NotificationHistory(hass, entry_id)
        self.previous_snapshot = None
        self._remove_listener: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Load state, establish a LIVE baseline and observe coordinator updates."""
        stored = await self.store.async_load()
        first_run = stored is None
        await self.history.async_load()

        # A real account must never emit a backlog when notification v2 starts.
        # This assignment also makes an upgrade from the legacy notifier safe even
        # when its old Store already exists but no previous AccountSnapshot does.
        if first_run and not self.demo_mode:
            self.previous_snapshot = self.coordinator.data
        elif self.previous_snapshot is None:
            self.previous_snapshot = self.coordinator.data

        await self.store.async_save({"initialized": True})
        await self._async_process(include_changes=False)
        self._remove_listener = self.coordinator.async_add_listener(self._schedule_process)

    def async_stop(self) -> None:
        """Stop observing coordinator updates."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def _schedule_process(self) -> None:
        self.hass.async_create_task(self._async_process())

    async def _async_process(self, *, include_changes: bool = True) -> None:
        """Evaluate current coordinator data and deliver unseen candidates."""
        now = dt_util.now()
        current = self.coordinator.data
        candidates: list[NotificationCandidate] = []

        if include_changes:
            candidates.extend(
                build_change_candidates(self.previous_snapshot, current, now)
            )
        for snapshot in current.students:
            candidates.extend(build_time_candidates(snapshot, now, self.options))

        self.previous_snapshot = current
        for candidate in candidates:
            if await self.history.async_append(candidate):
                await self._deliver(candidate, now)

    async def _deliver(self, candidate: NotificationCandidate, now) -> None:
        """Persist/publicly emit an accepted candidate through HA channels."""
        persistent_notification.async_create(
            self.hass,
            candidate.message,
            title=candidate.title,
            notification_id=f"{DOMAIN}_{candidate.event_id}",
        )

        event_data = {
            "event_id": candidate.event_id,
            "kind": candidate.kind,
            "priority": candidate.priority,
            "student_id": candidate.student_id,
            "student": candidate.student_name,
            "title": candidate.title,
            "message": candidate.message,
            "created_at": candidate.created_at.isoformat(),
            **candidate.data,
        }
        self.hass.bus.async_fire(EVENT_NOTIFICATION, event_data)
        legacy_event = _LEGACY_EVENTS.get(candidate.kind)
        if legacy_event:
            self.hass.bus.async_fire(legacy_event, event_data)

        if not self._is_quiet_hours(now):
            await self._async_push(candidate)

    async def _async_push(self, candidate: NotificationCandidate) -> None:
        """Send optional push to explicitly configured notify entities."""
        targets = tuple(self.options.get(CONF_NOTIFY_TARGETS, ()) or ())
        for target in targets:
            try:
                await self.hass.services.async_call(
                    "notify",
                    "send_message",
                    {
                        "title": candidate.title,
                        "message": candidate.message,
                    },
                    target={"entity_id": target},
                    blocking=True,
                )
            except Exception as err:  # delivery failures must stay isolated
                _LOGGER.warning(
                    "Failed to send mojV notification to %s: %s",
                    target,
                    type(err).__name__,
                )

    def _is_quiet_hours(self, now) -> bool:
        """Return whether optional push is currently inside configured quiet time."""
        if not self.options.get(CONF_QUIET_HOURS_ENABLED, False):
            return False
        start = self._parse_time(
            str(self.options.get(CONF_QUIET_HOURS_START, DEFAULT_QUIET_HOURS_START))
        )
        end = self._parse_time(
            str(self.options.get(CONF_QUIET_HOURS_END, DEFAULT_QUIET_HOURS_END))
        )
        current = now.timetz().replace(tzinfo=None)
        if start == end:
            return True
        if start < end:
            return start <= current < end
        return current >= start or current < end

    @staticmethod
    def _parse_time(value: str) -> time:
        """Parse validated HH:MM option values."""
        hour, minute = value.split(":", 1)
        return time(hour=int(hour), minute=int(minute))

    def notification_rows(self) -> list[dict[str, Any]]:
        """Return public newest-first history for the School Hub panel."""
        return self.history.as_panel_rows()
