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
parsers_pkg = types.ModuleType("custom_components.mojv.parsers")
parsers_pkg.__path__ = [str(PARSERS_DIR)]
sys.modules.setdefault("custom_components.mojv.parsers", parsers_pkg)


def _load(name: str, path: Path):
    full_name = f"custom_components.mojv.{name}"
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


models = _load("models", PKG_DIR / "models.py")


def _parser():
    return _load("parsers.grades", PARSERS_DIR / "grades.py")


def test_parse_grades_builds_partial_and_final_grades_for_each_period() -> None:
    parser = _parser()
    periods = [
        {"id": 101, "numerOkresu": 1},
        {"id": 102, "numerOkresu": 2},
    ]
    payloads = {
        "101": {
            "ocenyPrzedmioty": [
                {
                    "przedmiotNazwa": "Matematyka",
                    "proponowanaOcenaOkresowa": "5",
                    "ocenaOkresowa": "4",
                    "kolumnyOcenyCzastkowe": [
                        {
                            "idKolumny": 33,
                            "kategoriaKolumny": "Sprawdzian",
                            "nazwaKolumny": "Ułamki",
                            "oceny": [
                                {"wpis": "5", "dataOceny": "03.09.2026"},
                                {"wpis": "4+", "dataOceny": "2026-09-01T10:20:00"},
                            ],
                        }
                    ],
                }
            ]
        },
        "102": {
            "ocenyPrzedmioty": [
                {
                    "przedmiotNazwa": "Język polski",
                    "proponowanaOcenaOkresowa": "",
                    "ocenaOkresowa": "",
                    "kolumnyOcenyCzastkowe": [],
                }
            ]
        },
    }

    grades, finals = parser.parse_grades(periods, payloads)

    assert [(g.subject, g.value, g.period) for g in grades] == [
        ("Matematyka", "5", "1"),
        ("Matematyka", "4+", "1"),
    ]
    assert grades[0].date.date().isoformat() == "2026-09-03"
    assert grades[0].category == "Sprawdzian"
    assert grades[0].description == "Sprawdzian: Ułamki"
    assert grades[0].grade_id != grades[1].grade_id
    assert [(g.subject, g.proposed, g.final, g.period) for g in finals] == [
        ("Matematyka", "5", "4", "1")
    ]


def test_parse_grades_skips_malformed_rows_without_losing_valid_rows() -> None:
    parser = _parser()
    periods = [{"id": "p1", "numerOkresu": 1}]
    payloads = {
        "p1": {
            "ocenyPrzedmioty": [
                {
                    "przedmiotNazwa": "Historia",
                    "kolumnyOcenyCzastkowe": [
                        {
                            "idKolumny": "x",
                            "nazwaKolumny": "Daty",
                            "oceny": [
                                {"wpis": "5", "dataOceny": "bad-date"},
                                {"wpis": "4", "dataOceny": "02.09.2026"},
                            ],
                        }
                    ],
                },
                "not-a-dict",
            ]
        }
    }

    grades, finals = parser.parse_grades(periods, payloads)

    assert len(grades) == 1
    assert grades[0].value == "4"
    assert finals == ()
