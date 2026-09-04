from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "mojv"


def test_manager_uses_pure_rules_and_bounded_history() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    assert "build_change_candidates" in source
    assert "build_time_candidates" in source
    assert "NotificationHistory" in source
    assert "self.previous_snapshot" in source
    assert "self.history" in source


def test_live_first_run_is_baseline_not_historical_notification_storm() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    assert "first_run" in source
    assert "self.previous_snapshot = self.coordinator.data" in source
    assert "if first_run and not self.demo_mode" in source


def test_delivery_keeps_legacy_events_and_adds_unified_event() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    for event_name in (
        "mojv_lesson_late",
        "mojv_lesson_absent",
        "mojv_new_grade",
        "mojv_new_remark",
        "mojv_notification",
    ):
        assert event_name in source
    assert "candidate.kind" in source
    assert "candidate.event_id" in source


def test_push_uses_configured_notify_entities_and_send_message() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    assert "CONF_NOTIFY_TARGETS" in source
    assert '"notify"' in source
    assert '"send_message"' in source
    assert 'target={"entity_id": target}' in source
    assert "for target in targets" in source


def test_quiet_hours_suppress_push_only() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    assert "def _is_quiet_hours" in source
    assert "if not self._is_quiet_hours" in source
    persistent_pos = source.index("persistent_notification.async_create")
    quiet_pos = source.index("if not self._is_quiet_hours")
    assert persistent_pos < quiet_pos


def test_one_push_target_failure_is_isolated() -> None:
    source = (PKG / "notifications.py").read_text(encoding="utf-8")
    assert "except Exception" in source
    assert "Failed to send mojV notification" in source


def test_init_passes_config_entry_options_to_notifier() -> None:
    source = (PKG / "__init__.py").read_text(encoding="utf-8")
    assert "options=dict(entry.options)" in source
