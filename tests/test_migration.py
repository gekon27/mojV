from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "migration.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("mojv_migration_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v1_demo_entry_migrates_to_v2_with_explicit_mode() -> None:
    migration = _load_module()
    version, data = migration.migrate_entry_data(1, {"demo_students": 2})
    assert version == 2
    assert data == {"mode": "demo", "demo_students": 2}


def test_v2_entry_is_left_unchanged() -> None:
    migration = _load_module()
    original = {"mode": "live", "username": "x", "password": "y"}
    version, data = migration.migrate_entry_data(2, original)
    assert version == 2
    assert data == original
