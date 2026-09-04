from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "custom_components" / "mojv" / "frontend"
DETAILS_JS = FRONTEND / "school-panel-details.js"
HUB_JS = FRONTEND / "school-panel-hub.js"


def test_detail_module_exposes_accessible_overlay_contract() -> None:
    assert DETAILS_JS.exists(), "detail frontend module is not implemented yet"
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "_detailPreview" in source
    assert "_openMojvDetail" in source
    assert "_closeMojvDetail" in source
    assert 'role="dialog"' in source
    assert 'aria-modal="true"' in source
    assert 'event.key === "Escape"' in source
    assert "focus()" in source
    assert "__mojvDetailReturnFocus" in source


def test_schoolwork_rows_are_clickable_and_show_length_limited_safe_preview() -> None:
    assert DETAILS_JS.exists(), "detail frontend module is not implemented yet"
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "mojv-detail-trigger" in source
    assert 'data-mojv-detail-kind="schoolwork"' in source
    assert "item.description" in source
    assert "_detailPreview(item.description" in source
    assert "limit = 120" in source
    assert "this._e(" in source
    assert "innerHTML = detail.body" not in source


def test_detail_overlay_has_neutral_fallback_when_source_has_no_body() -> None:
    assert DETAILS_JS.exists(), "detail frontend module is not implemented yet"
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "Brak dodatkowej treści" in source


def test_important_today_details_use_the_same_safe_overlay() -> None:
    hub = HUB_JS.read_text(encoding="utf-8")
    assert 'import "./school-panel-details.js"' in hub
    assert 'data-mojv-detail-kind="important"' in hub
    assert "item.description" in hub
    assert "_detailPreview(item.description" in hub
