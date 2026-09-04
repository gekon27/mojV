from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "custom_components" / "mojv" / "panel_students.py"


def _load_module():
    assert MODULE_PATH.exists(), "panel_students helper is not implemented yet"
    spec = importlib.util.spec_from_file_location("mojv_panel_students", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ts(hour: int) -> datetime:
    return datetime(2026, 9, 4, hour, tzinfo=timezone.utc)


def test_select_student_rows_keeps_one_row_per_student_and_newest_snapshot() -> None:
    module = _load_module()
    rows = module.select_student_rows(
        [
            (_ts(8), 0, {"id": "s1", "name": "A", "class": "8A", "marker": "old"}),
            (_ts(8), 1, {"id": "s2", "name": "B", "class": "5C", "marker": "only"}),
            (_ts(9), 2, {"id": "s1", "name": "A", "class": "8A", "marker": "new"}),
        ]
    )
    assert [row["id"] for row in rows] == ["s1", "s2"]
    assert rows[0]["marker"] == "new"
    assert rows[1]["marker"] == "only"


def test_select_student_rows_equal_timestamp_is_stable() -> None:
    module = _load_module()
    stamp = _ts(8)
    rows = module.select_student_rows(
        [
            (stamp, 0, {"id": "s1", "marker": "first"}),
            (stamp, 1, {"id": "s1", "marker": "second"}),
        ]
    )
    assert rows == [{"id": "s1", "marker": "first"}]


def test_select_student_rows_preserves_different_students() -> None:
    module = _load_module()
    rows = module.select_student_rows(
        [
            (_ts(8), 0, {"id": "s1", "name": "A"}),
            (_ts(8), 1, {"id": "s2", "name": "B"}),
        ]
    )
    assert [row["id"] for row in rows] == ["s1", "s2"]
