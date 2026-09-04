from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "mojv" / "notifications.py"


def test_time_notifications_use_local_minute_ticker_without_portal_refresh() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "async_track_time_interval" in source
    assert "timedelta(minutes=1)" in source
    assert "def _schedule_time_process" in source
    assert "def _async_process_time" in source
    timer_body = source.split("def _async_process_time", 1)[1].split("def ", 1)[0]
    assert "build_time_candidates" in timer_body
    assert "coordinator.async_request_refresh" not in timer_body
    assert "client" not in timer_body


def test_enabled_notification_types_filter_change_and_time_candidates() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "CONF_NOTIFICATION_TYPES" in source
    assert "DEFAULT_NOTIFICATION_TYPES" in source
    assert "def _is_enabled" in source
    assert "if self._is_enabled(candidate)" in source


def test_time_tick_does_not_advance_change_baseline() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    timer_body = source.split("def _async_process_time", 1)[1].split("def ", 1)[0]
    assert "self.previous_snapshot =" not in timer_body
