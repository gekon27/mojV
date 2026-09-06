from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mojv"


def test_custom_schedule_is_persisted_locally_and_never_sent_to_school_portal() -> None:
    source = (COMPONENT / "custom_schedule.py").read_text(encoding="utf-8")
    assert "Store(" in source
    assert "DATA_CUSTOM_SCHEDULE" in source
    assert "async_add" in source
    assert "async_remove" in source
    assert "http" not in source.casefold()


def test_panel_serializes_custom_schedule_and_registers_a_write_command() -> None:
    source = (COMPONENT / "panel.py").read_text(encoding="utf-8")
    assert '"custom_schedule"' in source
    assert '"mojv/custom_schedule"' in source
    assert 'vol.In(("add", "remove"))' in source


def test_frontend_has_a_local_schedule_form_and_custom_lesson_marker() -> None:
    source = (COMPONENT / "frontend" / "school-panel-custom-schedule.js").read_text(encoding="utf-8")
    schedule = (COMPONENT / "frontend" / "school-panel-lesson-states.js").read_text(encoding="utf-8")
    assert 'type: "mojv/custom_schedule"' in source
    assert "Zapisz lokalnie w Home Assistant" in source
    assert "data-mojv-add-custom" in schedule
    assert "custom-schedule-lesson" in schedule


def test_communication_templates_are_local_and_do_not_post_to_the_portal() -> None:
    source = (COMPONENT / "communication_templates.py").read_text(encoding="utf-8")
    panel = (COMPONENT / "panel.py").read_text(encoding="utf-8")
    hub = (COMPONENT / "frontend" / "school-panel-hub.js").read_text(encoding="utf-8")
    assert "Store(" in source
    assert "DATA_COMMUNICATION_TEMPLATES" in source
    assert "http" not in source.casefold()
    assert '"mojv/communication_templates"' in panel
    assert '"Korespondencja"' in hub
    assert "Zapisz szablon w Home Assistant" in hub
    assert "wymagało osobnego podglądu i potwierdzenia" in hub


def test_reply_requires_explicit_confirmation_before_the_helper_is_called() -> None:
    panel = (COMPONENT / "panel.py").read_text(encoding="utf-8")
    hub = (COMPONENT / "frontend" / "school-panel-hub.js").read_text(encoding="utf-8")
    gateway = (COMPONENT / "helper_gateway.py").read_text(encoding="utf-8")
    assert '"mojv/send_reply"' in panel
    assert 'vol.Required("confirmed"): True' in panel
    assert "window.confirm(\"Wysłać tę odpowiedź do szkoły?" in hub
    assert '"/v1/actions/reply"' in gateway
