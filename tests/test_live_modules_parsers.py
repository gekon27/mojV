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


def test_parse_remarks_preserves_real_metadata_and_skips_invalid_rows() -> None:
    parser = _load("parsers.remarks", PARSERS_DIR / "remarks.py")
    rows = parser.parse_remarks(
        [
            {
                "id": 11,
                "data": "2026-09-03T10:15:00",
                "tresc": "Pochwała za pomoc kolegom",
                "autor": "A. Nowak",
                "kategoria": "Zachowanie",
                "liczbaPunktow": 5,
            },
            {"id": 12, "data": "03.09.2026", "tresc": "Informacja organizacyjna"},
            {"id": 13, "tresc": "brak daty"},
        ]
    )
    assert len(rows) == 2
    assert rows[0].remark_id == "11"
    assert rows[0].points == "5"
    assert rows[0].kind == "positive"
    assert rows[1].kind == "information"


def test_parse_messages_joins_inbox_with_real_message_details() -> None:
    parser = _load("parsers.messages", PARSERS_DIR / "messages.py")
    rows = parser.parse_messages(
        [
            {
                "apiGlobalKey": "m1",
                "data": "2026-09-03T09:20:00",
                "korespondenci": "Sekretariat",
                "temat": "Wycieczka",
                "przeczytana": False,
            },
            {"apiGlobalKey": "m2", "data": "bad", "temat": "Pominięta"},
        ],
        {"m1": {"tresc": "<p>Treść <b>wiadomości</b></p>"}},
    )
    assert len(rows) == 1
    assert rows[0].message_id == "m1"
    assert rows[0].sender == "Sekretariat"
    assert rows[0].subject == "Wycieczka"
    assert rows[0].body == "Treść wiadomości"
    assert rows[0].unread is True


def test_parse_attendance_stats_returns_global_and_per_subject_counts() -> None:
    parser = _load("parsers.attendance", PARSERS_DIR / "attendance.py")
    subjects = [{"id": 7, "nazwa": "Matematyka"}, {"id": 8, "nazwa": "Historia"}]
    global_payload = {
        "podsumowanie": 92.5,
        "statystyki": [
            {"kategoriaFrekwencji": 1, "razem": 90},
            {"kategoriaFrekwencji": 2, "razem": 4},
            {"kategoriaFrekwencji": 3, "razem": 3},
            {"kategoriaFrekwencji": 4, "razem": 2},
            {"kategoriaFrekwencji": 6, "razem": 1},
        ],
    }
    per_subject = {
        "7": {
            "podsumowanie": 95,
            "statystyki": [
                {"kategoriaFrekwencji": 1, "razem": 20},
                {"kategoriaFrekwencji": 2, "razem": 1},
            ],
        }
    }
    stats = parser.parse_attendance_stats(subjects, global_payload, per_subject)
    assert len(stats) == 2
    assert stats[0].subject == ""
    assert stats[0].present == 90
    assert stats[0].absent == 4
    assert stats[0].school_activity == 1
    assert stats[0].total == 100
    assert stats[0].percentage == 92.5
    assert stats[1].subject == "Matematyka"
    assert stats[1].present == 20
    assert stats[1].percentage == 95.0


def test_parse_achievements_does_not_invent_missing_dates() -> None:
    parser = _load("parsers.achievements", PARSERS_DIR / "achievements.py")
    rows = parser.parse_achievements(
        [
            {"id": 4, "tresc": "I miejsce w konkursie matematycznym"},
            {"id": 5, "data": "2026-09-02", "tytul": "Turniej", "tresc": "II miejsce"},
        ]
    )
    assert len(rows) == 2
    assert rows[0].date is None
    assert rows[0].title == "I miejsce w konkursie matematycznym"
    assert rows[1].date is not None
    assert rows[1].title == "Turniej"
    assert rows[1].description == "II miejsce"


def test_parse_meetings_keeps_room_description_and_online_reference() -> None:
    parser = _load("parsers.meetings", PARSERS_DIR / "meetings.py")
    rows = parser.parse_meetings(
        [
            {
                "id": 21,
                "dataCzas": "2026-09-10T17:30:00",
                "sala": "12",
                "opis": "Zebranie organizacyjne",
                "zebranieOnline": "https://meeting.example/abc",
            }
        ]
    )
    assert len(rows) == 1
    assert rows[0].meeting_id == "21"
    assert rows[0].start.isoformat().startswith("2026-09-10T17:30:00")
    assert rows[0].location == "12"
    assert rows[0].description == "Zebranie organizacyjne"
    assert rows[0].online_url == "https://meeting.example/abc"
