"""Config-entry migration helpers for mojV."""
from __future__ import annotations

CURRENT_VERSION = 2


def migrate_entry_data(version: int, data: dict) -> tuple[int, dict]:
    """Return the current config-entry version and migrated data."""
    migrated = dict(data)

    if version == 1:
        migrated.setdefault("mode", "demo")
        return CURRENT_VERSION, migrated

    return version, migrated
