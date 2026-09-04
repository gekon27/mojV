from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components" / "mojv" / "panel.py"
PANEL_BASE = ROOT / "custom_components" / "mojv" / "panel_base.py"
FRONTEND = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel.js"
FRONTEND_LIVE = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel-live.js"
FRONTEND_HUB = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel-hub.js"
FRONTEND_HUB_BASE = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel-hub-base.js"


def test_panel_payload_exposes_all_live_modules() -> None:
    source = PANEL_BASE.read_text(encoding="utf-8") + "\n" + PANEL.read_text(encoding="utf-8")

    for marker in (
        '"final_grades": [',
        '"schoolwork": [',
        '"remarks": [',
        '"messages": [',
        '"attendance_stats": [',
        '"achievements": [',
        '"meetings": [',
    ):
        assert marker in source
    assert '"proposed": grade.proposed' in source
    assert '"final": grade.final' in source
    assert '"kind": item.kind' in source
    assert '"description": item.description' in source
    assert '"body": message.body' in source
    assert '"unread": message.unread' in source
    assert '"percentage": stat.percentage' in source
    assert "school-panel-hub.js" in source
    assert 'import "./school-panel-live.js"' in FRONTEND_HUB_BASE.read_text(encoding="utf-8")
    assert 'import "./school-panel-hub-base.js"' in FRONTEND_HUB.read_text(encoding="utf-8")


def test_frontend_has_dynamic_live_module_views() -> None:
    source = FRONTEND.read_text(encoding="utf-8") + FRONTEND_LIVE.read_text(encoding="utf-8")

    for view in (
        "grades",
        "schoolwork",
        "remarks",
        "messages",
        "attendance_stats",
        "achievements",
        "meetings",
    ):
        assert f'case "{view}"' in source
    for field in (
        "student?.messages",
        "student?.attendance_stats",
        "student?.achievements",
        "student?.meetings",
    ):
        assert field in source


def test_empty_live_modules_do_not_force_empty_tabs() -> None:
    source = FRONTEND_LIVE.read_text(encoding="utf-8")

    assert 'if ((student?.messages || []).length)' in source
    assert 'if ((student?.attendance_stats || []).length)' in source
    assert 'if ((student?.achievements || []).length)' in source
    assert 'if ((student?.meetings || []).length)' in source
