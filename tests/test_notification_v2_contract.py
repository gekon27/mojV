from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "mojv"


def test_notification_rules_are_isolated_from_delivery() -> None:
    path = PKG / "notification_rules.py"
    assert path.is_file()
    source = path.read_text(encoding="utf-8")
    assert "class NotificationCandidate" in source
    assert "def build_change_candidates" in source
    assert "def build_time_candidates" in source
    assert "persistent_notification" not in source
    assert "hass.services" not in source


def test_notification_history_is_bounded_and_public_only() -> None:
    path = PKG / "notification_history.py"
    assert path.is_file()
    source = path.read_text(encoding="utf-8")
    assert "MAX_HISTORY = 200" in source
    assert "class NotificationHistory" in source
    forbidden = (
        "globalKeySkrzynka",
        "apiGlobalKey",
        "mailbox_key",
        "session_key",
        "password",
        "cookie",
    )
    for needle in forbidden:
        assert needle not in source


def test_notification_options_are_config_entry_options_not_credentials() -> None:
    flow = (PKG / "config_flow.py").read_text(encoding="utf-8")
    const = (PKG / "const.py").read_text(encoding="utf-8")
    assert "async_get_options_flow" in flow
    assert "MojVOptionsFlow" in flow
    assert "CONF_NOTIFICATION_TYPES" in const
    assert "CONF_NOTIFY_TARGETS" in const
    assert "DEFAULT_LESSON_END_MINUTES = 5" in const
    assert "DEFAULT_SCHOOLWORK_LEAD_HOURS = 24" in const
    assert "DEFAULT_MEETING_LEAD_HOURS = 24" in const
