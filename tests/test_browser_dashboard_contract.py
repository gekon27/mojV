from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mojv"
PANEL = COMPONENT / "panel.py"
DASHBOARD_JS = COMPONENT / "frontend" / "school-dashboard.js"
HUB_JS = COMPONENT / "frontend" / "school-panel-hub.js"


def test_legacy_browser_dashboard_is_removed_so_school_has_one_sidebar_entry() -> None:
    source = PANEL.read_text(encoding="utf-8")
    assert 'DASHBOARD_URL_PATH = "mojv-dashboard"' in source
    assert "frontend.async_remove_panel(hass, DASHBOARD_URL_PATH)" in source
    assert "panel_custom.async_register_panel" not in source


def test_legacy_dashboard_module_remains_data_free_during_migration() -> None:
    assert DASHBOARD_JS.exists(), "browser dashboard module is not implemented yet"
    source = DASHBOARD_JS.read_text(encoding="utf-8")
    assert 'import "./school-panel-hub.js"' in source
    assert 'document.createElement("mojv-school-panel")' in source
    assert 'customElements.define("mojv-school-dashboard"' in source
    assert "mojv/panel" not in source
    assert "fetch(" not in source


def test_school_hub_does_not_link_to_retired_dashboard() -> None:
    source = HUB_JS.read_text(encoding="utf-8")
    assert 'href="/mojv-dashboard"' not in source
    assert "Otwórz dashboard" not in source
