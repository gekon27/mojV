from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components" / "mojv" / "panel.py"
FRONTEND = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel.js"


def test_panel_payload_exposes_final_grades_and_schoolwork() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert '"final_grades": [' in source
    assert '"schoolwork": [' in source
    assert '"proposed": grade.proposed' in source
    assert '"final": grade.final' in source
    assert '"kind": item.kind' in source
    assert '"description": item.description' in source


def test_frontend_has_dedicated_grades_and_schoolwork_views() -> None:
    source = FRONTEND.read_text(encoding="utf-8")

    assert 'data-view="grades"' in source
    assert 'data-view="schoolwork"' in source
    assert 'case "grades"' in source
    assert 'case "schoolwork"' in source
