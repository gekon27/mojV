"""Pure notification rules for mojV.

This module must stay independent from Home Assistant delivery services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import AccountSnapshot, StudentSnapshot


@dataclass(frozen=True, slots=True)
class NotificationCandidate:
    """A public, delivery-agnostic notification candidate."""

    event_id: str
    student_id: str
    student_name: str
    kind: str
    priority: str
    title: str
    message: str
    created_at: datetime
    data: dict[str, Any] = field(default_factory=dict)


def build_change_candidates(
    previous: AccountSnapshot | None,
    current: AccountSnapshot,
    now: datetime,
) -> tuple[NotificationCandidate, ...]:
    """Return notifications caused by differences between snapshots."""
    return ()


def build_time_candidates(
    snapshot: StudentSnapshot,
    now: datetime,
    options: dict[str, Any],
) -> tuple[NotificationCandidate, ...]:
    """Return notifications caused only by the current time window."""
    return ()
