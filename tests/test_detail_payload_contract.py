from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "mojv"
PARSERS_DIR = PKG_DIR / "parsers"
PANEL = PKG_DIR / "panel.py"
PANEL_BASE = PKG_DIR / "panel_base.py"

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


def _extras():
    return _load("parsers.extras", PARSERS_DIR / "extras.py")


def test_important_today_preserves_safe_long_description() -> None:
    rows = _extras().parse_important_today(
        {
            "wazneDzisiaj": [
                {
                    "nazwa": "Wycieczka",
                    "przedmiot": "Historia",
                    "nazwaZdarzenia": "Informacja",
                    "opis": "Zbiórka o 7:45 przy wejściu głównym.",
                    "globalKeySkrzynka": "must-not-leak",
                }
            ]
        }
    )

    assert len(rows) == 1
    assert rows[0].description == "Zbiórka o 7:45 przy wejściu głównym."
    assert "must-not-leak" not in repr(rows[0])


def test_panel_serializes_full_safe_schoolwork_and_information_descriptions() -> None:
    source = PANEL_BASE.read_text(encoding="utf-8") + "\n" + PANEL.read_text(encoding="utf-8")
    assert '"description": item.description' in source
    assert 'row["important_today"]' in source
    important_block = source.split('row["important_today"]', 1)[1].split('row["homeroom_teachers"]', 1)[0]
    assert '"description": item.description' in important_block


def test_expanded_detail_payload_source_contains_no_forbidden_routing_fields() -> None:
    source = PANEL.read_text(encoding="utf-8")
    forbidden = (
        "globalKeySkrzynka",
        "apiGlobalKey",
        "mailbox_key",
        "session_key",
    )
    for key in forbidden:
        assert key not in source
