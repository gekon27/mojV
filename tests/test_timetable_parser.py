from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "mojv"
PARSERS_DIR = PKG_DIR / "parsers"

parent = types.ModuleType("custom_components")
parent.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", parent)

package = types.ModuleType("custom_components.mojv")
package.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("custom_components.mojv", package)

parsers_package = types.ModuleType("custom_components.mojv.parsers")
parsers_package.__path__ = [str(PARSERS_DIR)]
sys.modules.setdefault("custom_components.mojv.parsers", parsers_package)


def _load(full_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


models = _load("custom_components.mojv.models", PKG_DIR / "models.py")
timetable = _load(
    "custom_components.mojv.parsers.timetable", PARSERS_DIR / "timetable.py"
)


def test_parse_timetable_matches_attendance_by_date_and_start_time() -> None:
    plan = [
        {
            "data": "2026-09-03T00:00:00",
            "godzinaOd": "0001-01-01T08:00:00",
            "godzinaDo": "0001-01-01T08:45:00",
            "przedmiot": "Matematyka",
            "sala": "12",
            "prowadzacy": "Nauczyciel A",
            "numerLekcji": 1,
        },
        {
            "data": "2026-09-03T00:00:00",
            "godzinaOd": "0001-01-01T08:55:00",
            "godzinaDo": "0001-01-01T09:40:00",
            "przedmiot": "Historia",
            "numerLekcji": 2,
        },
    ]
    attendance = {
        "oddzialy": [
            {
                "data": "2026-09-03T00:00:00",
                "godzinaOd": "0001-01-01T08:00:00",
                "kategoriaFrekwencji": 4,
            }
        ]
    }

    lessons = timetable.parse_timetable(plan, attendance)

    assert len(lessons) == 2
    assert lessons[0].subject == "Matematyka"
    assert lessons[0].attendance == "late"
    assert lessons[1].attendance == "not_recorded"
    assert lessons[0].start.strftime("%Y-%m-%d %H:%M") == "2026-09-03 08:00"


def test_parse_timetable_preserves_change_semantics_without_guessing() -> None:
    plan = [
        {
            "data": "2026-09-03T00:00:00",
            "godzinaOd": "T10:00:00",
            "godzinaDo": "T10:45:00",
            "przedmiot": "Język polski",
            "adnotacja": 1,
            "zmiany": [{"opis": "Zastępstwo testowe"}],
        },
        {
            "data": "2026-09-03T00:00:00",
            "godzinaOd": "T10:55:00",
            "godzinaDo": "T11:40:00",
            "przedmiot": "WF",
            "adnotacja": 3,
        },
    ]

    first, second = timetable.parse_timetable(plan)

    assert first.replacement is True
    assert first.cancelled is False
    assert "replacement" in first.note
    assert "Zastępstwo testowe" in first.note
    assert second.cancelled is True
    assert second.replacement is False


def test_unknown_attendance_is_not_treated_as_present() -> None:
    plan = [
        {
            "data": "2026-09-03",
            "godzinaOd": "08:00",
            "godzinaDo": "08:45",
            "przedmiot": "Matematyka",
        }
    ]
    attendance = [
        {
            "data": "2026-09-03",
            "godzinaOd": "08:00",
            "kategoriaFrekwencji": 999,
        }
    ]

    (lesson,) = timetable.parse_timetable(plan, attendance)

    assert lesson.attendance == "unknown"
    assert lesson.attendance != "present"


def test_invalid_rows_are_skipped() -> None:
    plan = [
        {"data": "bad", "godzinaOd": "08:00", "godzinaDo": "08:45"},
        {"data": "2026-09-03", "godzinaOd": "bad", "godzinaDo": "08:45"},
        {
            "data": "2026-09-03",
            "godzinaOd": "09:00",
            "godzinaDo": "09:45",
            "przedmiot": "Poprawny wpis",
        },
    ]

    lessons = timetable.parse_timetable(plan)

    assert len(lessons) == 1
    assert lessons[0].subject == "Poprawny wpis"
