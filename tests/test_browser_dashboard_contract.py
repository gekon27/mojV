from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mojv"
PANEL = COMPONENT / "panel.py"
DASHBOARD_JS = COMPONENT / "frontend" / "school-dashboard.js"
HUB_JS = COMPONENT / "frontend" / "school-panel-hub.js"


def test_browser_dashboard_is_second_home_assistant_custom_panel() -> None:
    source = PANEL.read_text(encoding="utf-8")
    assert 'DASHBOARD_URL_PATH = "mojv-dashboard"' in source
    assert 'DASHBOARD_ELEMENT = "mojv-school-dashboard"' in source
    assert 'DASHBOARD_TITLE = "Dashboard szkoły"' in source
    assert 'module_url=f"{PANEL_STATIC_URL}/school-dashboard.js"' in source
    assert "panel_custom.async_register_panel" in source
    assert "require_admin=False" in source


def test_dashboard_reuses_school_hub_instead_of_fetching_portal_or_ws_itself() -> None:
    assert DASHBOARD_JS.exists(), "browser dashboard module is not implemented yet"
    source = DASHBOARD_JS.read_text(encoding="utf-8")
    assert 'import "./school-panel-hub.js"' in source
    assert 'document.createElement("mojv-school-panel")' in source
    assert 'customElements.define("mojv-school-dashboard"' in source
    assert "mojv/panel" not in source
    assert "fetch(" not in source


def test_school_hub_exposes_browser_dashboard_action() -> None:
    source = HUB_JS.read_text(encoding="utf-8")
    assert 'href="/mojv-dashboard"' in source
    assert "Otwórz dashboard" in source
