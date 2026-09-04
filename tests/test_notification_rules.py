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


def _load(name: str, path: Path):
    full_name = f"custom_components.mojv.{name}"
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


models = _load("models", PKG_DIR / "models.py")
rules = _load("notification_rules", PKG_DIR / "notification_rules.py")


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 4, hour, minute, tzinfo=timezone.utc)


def _student_snapshot(**changes):
    base = dict(
        student=models.Student("s1", "Ala", "4A"),
        lessons=(),
        grades=(),
        final_grades=(),
        remarks=(),
        schoolwork=(),
        messages=(),
        attendance_stats=(),
        achievements=(),
        meetings=(),
    )
    base.update(changes)
    return models.StudentSnapshot(**base)


def _account(student, stamp=None):
    return models.AccountSnapshot((student,), stamp or _dt(8))


def test_change_candidates_detect_new_school_records_and_keep_stable_ids() -> None:
    previous = _student_snapshot(
        grades=(models.Grade("g1", "Matematyka", "4", _dt(7)),),
        final_grades=(models.FinalGrade("Matematyka", proposed="4", final="", period="I"),),
    )
    current = _student_snapshot(
        grades=(
            models.Grade("g1", "Matematyka", "4", _dt(7)),
            models.Grade("g2", "Polski", "5", _dt(8), description="Kartkówka"),
        ),
        final_grades=(models.FinalGrade("Matematyka", proposed="5", final="", period="I"),),
        remarks=(models.Remark("r1", _dt(8), "Pomoc kolegom", kind="positive"),),
        messages=(models.Message("m-public-hash", _dt(8), "Sekretariat", "Wycieczka", unread=True),),
        schoolwork=(models.SchoolWork("w1", _dt(12), "Historia", "Sprawdzian", kind="test"),),
        achievements=(models.Achievement("a1", _dt(8), "Konkurs", "I miejsce"),),
        meetings=(models.Meeting("z1", _dt(18), "Zebranie", "12"),),
    )

    first = rules.build_change_candidates(_account(previous), _account(current), _dt(9))
    second = rules.build_change_candidates(_account(previous), _account(current), _dt(9, 1))
    kinds = {item.kind for item in first}

    assert {"grade", "final_grade", "praise", "message", "schoolwork_new", "achievement", "meeting_new"} <= kinds
    assert [item.event_id for item in first] == [item.event_id for item in second]
    assert all(item.student_id == "s1" and item.student_name == "Ala" for item in first)
    assert all("apiGlobalKey" not in repr(item.data) for item in first)


def test_change_candidates_detect_attendance_and_lesson_changes() -> None:
    before_lesson = models.Lesson(
        2,
        "Matematyka",
        _dt(9),
        _dt(9, 45),
        room="12",
        teacher="A. Nowak",
        attendance="not_recorded",
    )
    after_lesson = models.Lesson(
        2,
        "Matematyka",
        _dt(9),
        _dt(9, 45),
        room="18",
        teacher="A. Nowak",
        attendance="absent",
        replacement=True,
    )
    cancelled_before = models.Lesson(3, "Historia", _dt(10), _dt(10, 45))
    cancelled_after = models.Lesson(3, "Historia", _dt(10), _dt(10, 45), cancelled=True)

    candidates = rules.build_change_candidates(
        _account(_student_snapshot(lessons=(before_lesson, cancelled_before))),
        _account(_student_snapshot(lessons=(after_lesson, cancelled_after))),
        _dt(9, 5),
    )
    kinds = {item.kind for item in candidates}

    assert "absence" in kinds
    assert "lesson_replacement" in kinds
    assert "lesson_changed" in kinds
    assert "lesson_cancelled" in kinds


def test_time_candidates_create_only_future_window_reminders() -> None:
    now = _dt(9, 40)
    snapshot = _student_snapshot(
        lessons=(models.Lesson(2, "Matematyka", _dt(9), _dt(9, 45)),),
        schoolwork=(
            models.SchoolWork("w1", now + timedelta(hours=20), "Historia", "Sprawdzian", kind="test"),
            models.SchoolWork("w-old", now - timedelta(hours=1), "Polski", "Stare zadanie"),
        ),
        meetings=(models.Meeting("z1", now + timedelta(hours=23), "Zebranie", "12"),),
    )
    options = {
        "lesson_end_minutes": 5,
        "schoolwork_lead_hours": 24,
        "meeting_lead_hours": 24,
        "notification_types": ["lesson_ending", "schoolwork_due", "meeting_due"],
    }

    candidates = rules.build_time_candidates(snapshot, now, options)
    kinds = [item.kind for item in candidates]

    assert kinds.count("lesson_ending") == 1
    assert kinds.count("schoolwork_due") == 1
    assert kinds.count("meeting_due") == 1
    assert all(item.event_id for item in candidates)


def test_disabled_notification_kind_is_not_returned() -> None:
    now = _dt(9, 40)
    snapshot = _student_snapshot(
        lessons=(models.Lesson(2, "Matematyka", _dt(9), _dt(9, 45)),),
    )
    candidates = rules.build_time_candidates(
        snapshot,
        now,
        {
            "lesson_end_minutes": 5,
            "notification_types": [],
        },
    )
    assert candidates == ()
