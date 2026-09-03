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
    return _load("parsers.schoolwork", PARSERS_DIR / "schoolwork.py")


def test_parse_schoolwork_maps_types_dates_and_plain_text() -> None:
    parser = _parser()
    payload = [
        {
            "id": 12,
            "typ": 4,
            "data": "2026-09-03T00:00:00",
            "terminOdpowiedzi": "2026-09-05T18:00:00",
            "przedmiotNazwa": "Matematyka",
            "temat": "Ułamki",
            "opis": "<p>Zrób <strong>zadania 1–5</strong><br>str. 20</p>",
        },
        {
            "id": 13,
            "typ": 2,
            "data": "06.09.2026",
            "przedmiotNazwa": "Historia",
            "temat": "Daty",
            "opis": "Powtórka",
        },
        {
            "id": 14,
            "typ": 99,
            "data": "2026-09-07",
            "przedmiotNazwa": "Informatyka",
            "opis": "Projekt",
        },
    ]

    rows = parser.parse_schoolwork(payload)

    assert [(row.work_id, row.kind) for row in rows] == [
        ("12", "homework"),
        ("13", "quiz"),
        ("14", "other"),
    ]
    assert rows[0].date.isoformat() == "2026-09-05T18:00:00"
    assert rows[0].subject == "Matematyka"
    assert rows[0].title == "Ułamki"
    assert "<" not in rows[0].description
    assert "zadania 1–5" in rows[0].description
    assert "str. 20" in rows[0].description
    assert rows[2].title == "Inne"


def test_parse_schoolwork_accepts_envelope_and_skips_invalid_records() -> None:
    parser = _parser()
    payload = {
        "data": [
            {"id": "bad", "typ": 1, "data": "not-a-date", "temat": "Pomiń"},
            {"id": "ok", "typ": 3, "data": "08.09.2026", "temat": "Epoki"},
            "not-a-dict",
        ]
    }

    rows = parser.parse_schoolwork(payload)

    assert len(rows) == 1
    assert rows[0].work_id == "ok"
    assert rows[0].kind == "class_test"
    assert rows[0].date.date().isoformat() == "2026-09-08"
