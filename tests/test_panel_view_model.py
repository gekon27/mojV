from __future__ import annotations

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


def _load(name: str):
    full_name = f"custom_components.mojv.{name}"
    spec = importlib.util.spec_from_file_location(full_name, PKG_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


models = _load("models")
logic = _load("logic")

Lesson = models.Lesson
Student = models.Student
StudentSnapshot = models.StudentSnapshot


def test_attendance_summary_counts_known_states_and_skips_cancelled() -> None:
    attendance_summary = getattr(logic, "attendance_summary", None)
    assert attendance_summary is not None, "attendance_summary must be implemented"

    start = datetime(2026, 9, 3, 8, 0, tzinfo=timezone.utc)
    lessons = (
        Lesson(1, "A", start, start + timedelta(minutes=45), attendance="present"),
        Lesson(2, "B", start, start + timedelta(minutes=45), attendance="absent"),
        Lesson(3, "C", start, start + timedelta(minutes=45), attendance="late"),
        Lesson(4, "D", start, start + timedelta(minutes=45), attendance="released"),
        Lesson(5, "E", start, start + timedelta(minutes=45), attendance="mystery"),
        Lesson(
            6,
            "F",
            start,
            start + timedelta(minutes=45),
            attendance="absent",
            cancelled=True,
        ),
    )
    snapshot = StudentSnapshot(
        student=Student(student_id="1", name="Test", class_name="5A"),
        lessons=lessons,
    )

    assert attendance_summary(snapshot) == {
        "present": 1,
        "absent": 1,
        "excused_absence": 0,
        "late": 1,
        "excused_late": 0,
        "school_activity": 0,
        "released": 1,
        "not_recorded": 0,
        "unknown": 1,
    }
