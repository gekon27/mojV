from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime, timezone
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
    return _load("parsers.extras", PARSERS_DIR / "extras.py")


def test_parse_lucky_number_uses_real_value_and_supplied_date() -> None:
    parser = _parser()
    now = datetime(2026, 9, 4, 8, 30, tzinfo=timezone.utc)
    item = parser.parse_lucky_number({"id": 77, "numer": 20}, now)
    assert item is not None
    assert item.value == "20"
    assert item.date == now
    assert not hasattr(item, "id")


def test_parse_free_days_keeps_named_date_ranges() -> None:
    parser = _parser()
    rows = parser.parse_free_days(
        [{"dataOd": "2026-12-23T00:00:00", "dataDo": "2027-01-01T00:00:00", "nazwa": "Przerwa świąteczna"}]
    )
    assert len(rows) == 1
    assert rows[0].name == "Przerwa świąteczna"
    assert rows[0].start.isoformat().startswith("2026-12-23")
    assert rows[0].end.isoformat().startswith("2027-01-01")


def test_parse_teachers_whitelists_school_fields_only() -> None:
    parser = _parser()
    rows = parser.parse_teachers(
        {
            "nauczyciele": [
                {
                    "przedmiot": "Historia",
                    "imie": "Joanna",
                    "nazwisko": "Budna",
                    "wychowawca": False,
                    "globalKeySkrzynka": "SECRET",
                }
            ]
        }
    )
    assert len(rows) == 1
    assert rows[0].name == "Joanna Budna"
    assert rows[0].subject == "Historia"
    assert rows[0].homeroom is False
    assert "SECRET" not in repr(rows[0])
    assert not hasattr(rows[0], "mailbox_key")


def test_parse_homeroom_teachers_drops_mailbox_routing_key() -> None:
    parser = _parser()
    rows = parser.parse_homeroom_teachers(
        [{"imieNazwisko": "Jan Kowalski", "isGlowny": True, "globalKeySkrzynka": "SECRET"}]
    )
    assert len(rows) == 1
    assert rows[0].name == "Jan Kowalski"
    assert rows[0].primary is True
    assert "SECRET" not in repr(rows[0])


def test_parse_school_info_normalizes_public_contact_data() -> None:
    parser = _parser()
    item = parser.parse_school_info(
        {
            "nazwa": "Szkoła Podstawowa nr 1",
            "miejscowosc": "Gryfino",
            "ulica": "Szkolna",
            "kodPocztowy": "74-100",
            "nrDomu": "5",
            "nrMieszkania": "",
            "stronaWwwUrl": "https://school.example",
            "mail": "sekretariat@school.example",
            "dyrektorzy": [{"imieNazwisko": "Anna Dyrektor"}],
            "telKomorkowy": "123456789",
        }
    )
    assert item is not None
    assert item.name == "Szkoła Podstawowa nr 1"
    assert item.city == "Gryfino"
    assert "Szkolna 5" in item.address
    assert "74-100" in item.address
    assert item.website == "https://school.example"
    assert item.email == "sekretariat@school.example"
    assert item.directors == ("Anna Dyrektor",)
    assert "123456789" not in repr(item)


def test_parse_important_today_keeps_portal_titles() -> None:
    parser = _parser()
    rows = parser.parse_important_today(
        [{"przedmiot": "Matematyka", "nazwaZdarzenia": "sprawdzian", "nazwa": "Matematyka - sprawdzian"}]
    )
    assert len(rows) == 1
    assert rows[0].subject == "Matematyka"
    assert rows[0].kind == "sprawdzian"
    assert rows[0].title == "Matematyka - sprawdzian"


def test_parse_completed_lessons_preserves_topic_without_raw_ids() -> None:
    parser = _parser()
    rows = parser.parse_completed_lessons(
        [
            {
                "id": 12345,
                "data": "2026-09-04T08:00:00+02:00",
                "przedmiot": "Język angielski",
                "nauczyciel": "A. Teacher",
                "tematOpis": "Human - vocabulary practice",
                "online": "https://lesson.example",
                "nrLekcji": 1,
                "globalKeySkrzynka": "SECRET",
            }
        ]
    )
    assert len(rows) == 1
    assert rows[0].lesson_id != "12345"
    assert len(rows[0].lesson_id) == 24
    assert rows[0].subject == "Język angielski"
    assert rows[0].topic == "Human - vocabulary practice"
    assert rows[0].lesson_number == 1
    assert "SECRET" not in repr(rows[0])


def test_parse_excuses_keeps_status_without_portal_ids() -> None:
    parser = _parser()
    item = parser.parse_excuses(
        {
            "usprawiedliwieniaAktywne": True,
            "usprawiedliwienia": [
                {
                    "dzien": "2026-09-03T00:00:00+02:00",
                    "idUsprawiedliwienieDzien": 111,
                    "idUsprawiedliwienieLekcjaOddzial": 222,
                    "numerLekcji": 4,
                    "status": 1,
                }
            ],
            "usprawiedliwieniaBlokada": None,
        }
    )
    assert item.active is True
    assert item.blocked is False
    assert len(item.entries) == 1
    assert item.entries[0].lesson_number == 4
    assert item.entries[0].status == 1
    assert "111" not in repr(item)
    assert "222" not in repr(item)
