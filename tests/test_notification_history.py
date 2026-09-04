from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "mojv"

parent = types.ModuleType("custom_components")
parent.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", parent)
package = types.ModuleType("custom_components.mojv")
package.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("custom_components.mojv", package)

ha = types.ModuleType("homeassistant")
ha.__path__ = []
sys.modules.setdefault("homeassistant", ha)
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = object
sys.modules["homeassistant.core"] = core
helpers = types.ModuleType("homeassistant.helpers")
helpers.__path__ = []
sys.modules["homeassistant.helpers"] = helpers


class FakeStore:
    def __init__(self, hass, version, key):
        self.data = None

    @classmethod
    def __class_getitem__(cls, item):
        return cls

    async def async_load(self):
        return self.data

    async def async_save(self, data):
        self.data = data


storage = types.ModuleType("homeassistant.helpers.storage")
storage.Store = FakeStore
sys.modules["homeassistant.helpers.storage"] = storage
const = types.ModuleType("custom_components.mojv.const")
const.DOMAIN = "mojv"
sys.modules["custom_components.mojv.const"] = const


def _load(name: str, path: Path):
    full_name = f"custom_components.mojv.{name}"
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


_load("models", PKG_DIR / "models.py")
rules = _load("notification_rules", PKG_DIR / "notification_rules.py")
history_mod = _load("notification_history", PKG_DIR / "notification_history.py")


def _candidate(index: int):
    return rules.NotificationCandidate(
        event_id=f"event-{index}",
        student_id="s1",
        student_name="Ala",
        kind="grade",
        priority="normal",
        title=f"Ocena {index}",
        message="Matematyka",
        created_at=datetime(2026, 9, 4, tzinfo=timezone.utc) + timedelta(minutes=index),
        data={"subject": "Matematyka"},
    )


def test_history_deduplicates_and_keeps_newest_200() -> None:
    async def scenario():
        history = history_mod.NotificationHistory(object(), "entry")
        await history.async_load()
        assert await history.async_append(_candidate(0)) is True
        assert await history.async_append(_candidate(0)) is False
        for index in range(1, 205):
            await history.async_append(_candidate(index))
        rows = history.as_panel_rows()
        assert len(rows) == 200
        assert rows[0]["event_id"] == "event-204"
        assert rows[-1]["event_id"] == "event-5"
        assert all(isinstance(row["created_at"], str) for row in rows)

    asyncio.run(scenario())


def test_history_round_trip_loads_saved_rows() -> None:
    async def scenario():
        first = history_mod.NotificationHistory(object(), "entry")
        await first.async_append(_candidate(7))
        persisted = first._store.data

        second = history_mod.NotificationHistory(object(), "entry")
        second._store.data = persisted
        await second.async_load()
        assert second.as_panel_rows()[0]["event_id"] == "event-7"

    asyncio.run(scenario())
