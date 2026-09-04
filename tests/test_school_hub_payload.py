from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components" / "mojv" / "panel.py"
PANEL_BASE = ROOT / "custom_components" / "mojv" / "panel_base.py"


def _panel_source() -> str:
    return PANEL_BASE.read_text(encoding="utf-8") + "\n" + PANEL.read_text(encoding="utf-8")


def test_panel_exposes_dashboard_activity_and_notification_history() -> None:
    source = _panel_source()
    assert "def _dashboard_dict" in source
    assert "def _activity_rows" in source
    assert '"dashboard": _dashboard_dict' in source
    assert '"activity": _activity_rows' in source
    assert '"notifications"' in source
    assert "notification_rows" in source


def test_dashboard_contains_all_available_summary_slots() -> None:
    source = _panel_source()
    for key in (
        "unread_messages",
        "latest_grade",
        "next_schoolwork",
        "next_meeting",
        "latest_remark",
        "attendance_percentage",
        "latest_achievement",
    ):
        assert f'"{key}"' in source


def test_activity_combines_live_modules_without_secrets() -> None:
    source = _panel_source()
    for kind in (
        '"grade"',
        '"remark"',
        '"praise"',
        '"message"',
        '"schoolwork"',
        '"meeting"',
        '"achievement"',
        '"attendance"',
    ):
        assert kind in source
    for forbidden in (
        "globalKeySkrzynka",
        "apiGlobalKey",
        "mailbox_key",
        "session_key",
    ):
        assert forbidden not in source
