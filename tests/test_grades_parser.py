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


_load("custom_components.mojv.models", PKG_DIR / "models.py")
grades_parser = _load(
    "custom_components.mojv.parsers.grades", PARSERS_DIR / "grades.py"
)


def _payload(value: str = "5") -> dict:
    return {
        "ocenyPrzedmioty": [
            {
                "przedmiotNazwa": "Matematyka",
                "proponowanaOcenaOkresowa": "5",
                "ocenaOkresowa": "4",
                "kolumnyOcenyCzastkowe": [
                    {
                        "idKolumny": 7,
                        "kategoriaKolumny": "Sprawdzian",
                        "nazwaKolumny": "Ułamki",
                        "waga": 3,
                        "oceny": [
                            {
                                "wpis": value,
                                "dataOceny": "2026-09-03T10:15:00",
                            }
                        ],
                    }
                ],
            }
        ]
    }


def test_parse_grades_separates_partial_and_final_grades() -> None:
    grades, finals = grades_parser.parse_grades(_payload(), period="1")

    assert len(grades) == 1
    assert grades[0].subject == "Matematyka"
    assert grades[0].value == "5"
    assert grades[0].description == "Sprawdzian: Ułamki"
    assert grades[0].weight == "3"
    assert grades[0].period == "1"
    assert grades[0].grade_id.startswith("grade-")

    assert len(finals) == 1
    assert finals[0].proposed == "5"
    assert finals[0].final == "4"
    assert finals[0].period == "1"


def test_grade_fallback_id_is_stable() -> None:
    first, _ = grades_parser.parse_grades(_payload(), period="1")
    second, _ = grades_parser.parse_grades(_payload(), period="1")

    assert first[0].grade_id == second[0].grade_id


def test_grade_change_produces_a_different_fallback_id() -> None:
    first, _ = grades_parser.parse_grades(_payload("5"), period="1")
    changed, _ = grades_parser.parse_grades(_payload("4+"), period="1")

    assert first[0].grade_id != changed[0].grade_id


def test_merge_periods_keeps_period_specific_final_grades() -> None:
    grades, finals = grades_parser.merge_grade_periods(
        {"1": _payload("5"), "2": _payload("4")}
    )

    assert len(grades) == 2
    assert {(item.period, item.value) for item in grades} == {("1", "5"), ("2", "4")}
    assert {(item.period, item.subject) for item in finals} == {
        ("1", "Matematyka"),
        ("2", "Matematyka"),
    }


def test_invalid_or_empty_grade_entries_are_skipped() -> None:
    payload = _payload()
    payload["ocenyPrzedmioty"][0]["kolumnyOcenyCzastkowe"][0]["oceny"] = [
        {"wpis": "", "dataOceny": "2026-09-03"},
        {"wpis": "5", "dataOceny": "not-a-date"},
    ]

    grades, finals = grades_parser.parse_grades(payload, period="1")

    assert grades == ()
    assert len(finals) == 1
