from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "mojv" / "frontend"
HUB = FRONTEND / "school-panel-hub.js"
HUB_BASE = FRONTEND / "school-panel-hub-base.js"


def _hub_source() -> str:
    return HUB_BASE.read_text(encoding="utf-8") + "\n" + HUB.read_text(encoding="utf-8")


def test_hub_wrapper_extends_live_panel_and_is_registered() -> None:
    assert HUB.is_file()
    assert HUB_BASE.is_file()
    source = _hub_source()
    panel = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "custom_components" / "mojv" / "panel_base.py",
            ROOT / "custom_components" / "mojv" / "panel.py",
        )
    )
    assert 'import "./school-panel-live.js"' in source
    assert 'import "./school-panel-hub-base.js"' in HUB.read_text(encoding="utf-8")
    assert "school-panel-hub.js" in panel


def test_hub_adds_dashboard_activity_and_notifications_views() -> None:
    source = _hub_source()
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
    source = _hub_source()
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
