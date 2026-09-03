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


def _snapshot(*lessons: Lesson) -> StudentSnapshot:
    return StudentSnapshot(
        student=Student(student_id="1", name="Test"),
        lessons=tuple(lessons),
    )


def test_active_lesson_returns_current_non_cancelled_lesson() -> None:
    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    cancelled = Lesson(
        number=1,
        subject="A",
        start=now - timedelta(minutes=10),
        end=now + timedelta(minutes=10),
        cancelled=True,
    )
    current = Lesson(
        number=2,
        subject="B",
        start=now - timedelta(minutes=5),
        end=now + timedelta(minutes=40),
    )

    assert logic.active_lesson(_snapshot(cancelled, current), now) == current


def test_next_lesson_skips_cancelled_lessons() -> None:
    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    cancelled = Lesson(
        number=2,
        subject="A",
        start=now + timedelta(minutes=10),
        end=now + timedelta(minutes=55),
        cancelled=True,
    )
    expected = Lesson(
        number=3,
        subject="B",
        start=now + timedelta(minutes=20),
        end=now + timedelta(minutes=65),
    )

    assert logic.next_lesson(_snapshot(cancelled, expected), now) == expected


def test_minutes_to_end_rounds_up() -> None:
    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    lesson = Lesson(
        number=1,
        subject="A",
        start=now - timedelta(minutes=10),
        end=now + timedelta(minutes=4, seconds=1),
    )

    assert logic.minutes_to_end(lesson, now) == 5


def test_lessons_today_filters_and_sorts() -> None:
    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    later = Lesson(
        number=2,
        subject="B",
        start=now + timedelta(hours=1),
        end=now + timedelta(hours=1, minutes=45),
    )
    earlier = Lesson(
        number=1,
        subject="A",
        start=now - timedelta(hours=1),
        end=now - timedelta(minutes=15),
    )
    tomorrow = Lesson(
        number=1,
        subject="C",
        start=now + timedelta(days=1),
        end=now + timedelta(days=1, minutes=45),
    )

    assert logic.lessons_today(_snapshot(later, tomorrow, earlier), now) == (
        earlier,
        later,
    )


def test_lesson_progress_pct_tracks_elapsed_lesson_time() -> None:
    progress = getattr(logic, "lesson_progress_pct", None)
    assert progress is not None, "lesson_progress_pct must be implemented"

    start = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    lesson = Lesson(
        number=1,
        subject="A",
        start=start,
        end=start + timedelta(minutes=40),
    )

    assert progress(lesson, start - timedelta(minutes=1)) == 0
    assert progress(lesson, start + timedelta(minutes=10)) == 25
    assert progress(lesson, start + timedelta(minutes=40)) == 100


def test_lesson_alerts_prioritize_absence_and_end_warning() -> None:
    alerts = getattr(logic, "lesson_alerts", None)
    assert alerts is not None, "lesson_alerts must be implemented"

    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    lesson = Lesson(
        number=3,
        subject="Biologia",
        start=now - timedelta(minutes=40),
        end=now + timedelta(minutes=5),
        attendance="absent",
    )

    assert alerts(lesson, now) == (
        ("absence", "Nieobecność na trwającej lekcji"),
        ("ending", "Koniec lekcji za 5 min"),
    )


def test_lesson_alerts_marks_lateness_without_inventing_presence() -> None:
    alerts = getattr(logic, "lesson_alerts", None)
    assert alerts is not None, "lesson_alerts must be implemented"

    now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)
    late = Lesson(
        number=2,
        subject="Matematyka",
        start=now - timedelta(minutes=5),
        end=now + timedelta(minutes=40),
        attendance="late",
    )
    no_record = Lesson(
        number=3,
        subject="Polski",
        start=now - timedelta(minutes=5),
        end=now + timedelta(minutes=40),
        attendance="not_recorded",
    )

    assert alerts(late, now) == (("late", "Spóźnienie na trwającą lekcję"),)
    assert alerts(no_record, now) == ()
