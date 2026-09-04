from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "mojv" / "frontend"


def test_hub_wrapper_extends_live_panel_and_is_registered() -> None:
    hub = FRONTEND / "school-panel-hub.js"
    assert hub.is_file()
    source = hub.read_text(encoding="utf-8")
    panel = (ROOT / "custom_components" / "mojv" / "panel.py").read_text(
        encoding="utf-8"
    )
    assert 'import "./school-panel-live.js"' in source
    assert "school-panel-hub.js" in panel


def test_hub_adds_dashboard_activity_and_notifications_views() -> None:
    source = (FRONTEND / "school-panel-hub.js").read_text(encoding="utf-8")
    for view, label in (
        ("dashboard", "Pulpit"),
        ("activity", "Aktywność"),
        ("notifications", "Powiadomienia"),
    ):
        assert f'"{view}"' in source
        assert label in source
    assert "_renderDashboard" in source
    assert "_renderActivity" in source
    assert "_renderNotifications" in source


def test_hub_has_badges_and_responsive_layout_without_new_ws_polling() -> None:
    source = (FRONTEND / "school-panel-hub.js").read_text(encoding="utf-8")
    assert "view-badge" in source
    assert "unread_messages" in source
    assert "@media" in source
    assert "grid-template-columns" in source
    assert "callWS" not in source


def test_ci_syntax_checks_all_three_panel_modules() -> None:
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
        encoding="utf-8"
    )
    for filename in (
        "school-panel.js",
        "school-panel-live.js",
        "school-panel-hub.js",
    ):
        assert f"node --check custom_components/mojv/frontend/{filename}" in workflow
