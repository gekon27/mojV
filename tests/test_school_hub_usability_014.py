from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOJV = ROOT / "custom_components" / "mojv"
FRONTEND = MOJV / "frontend"
API_MODULE = MOJV / "school_api.py"
HUB_JS = FRONTEND / "school-panel-hub.js"
LESSON_STATES_JS = FRONTEND / "school-panel-lesson-states.js"
DETAILS_JS = FRONTEND / "school-panel-details.js"


def _load_api():
    spec = importlib.util.spec_from_file_location("mojv_usability_api_test", API_MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def get_json(self, path: str, params: dict[str, object]):
        self.calls.append((path, dict(params)))
        if path.endswith("/api/SprawdzianyZadaniaDomowe"):
            return [
                {
                    "id": 101,
                    "typ": 4,
                    "przedmiotNazwa": "Matematyka",
                    "data": "2026-09-10T00:00:00+02:00",
                },
                {
                    "id": 102,
                    "typ": 1,
                    "przedmiotNazwa": "Historia",
                    "data": "2026-09-11T00:00:00+02:00",
                },
            ]
        if path.endswith("/api/ZadanieDomoweSzczegoly"):
            return {
                "id": 101,
                "typ": 4,
                "terminOdpowiedzi": "2026-09-10T00:00:00+02:00",
                "przedmiotNazwa": "Matematyka",
                "opis": "Zrób zadania 1-5 ze strony 42.",
            }
        if path.endswith("/api/SprawdzianSzczegoly"):
            return {
                "id": 102,
                "typ": 1,
                "data": "2026-09-11T00:00:00+02:00",
                "przedmiotNazwa": "Historia",
                "opis": "Rozdziały 3 i 4.",
            }
        return []


def test_plan_is_exactly_four_weeks_total_one_back_current_two_forward() -> None:
    api_mod = _load_api()
    transport = FakeTransport()
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url="https://student.example/city",
        session_key="SECRET",
    )

    asyncio.run(client.fetch_student(student, now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc)))

    _, params = next(call for call in transport.calls if call[0].endswith("/api/PlanZajec"))
    assert params["dataOd"] == "2026-08-24T00:00:00.000Z"
    assert params["dataDo"] == "2026-09-20T23:59:59.999Z"

    frontend = LESSON_STATES_JS.read_text(encoding="utf-8")
    assert 'this._weekOffset >= 2 ? "disabled" : ""' in frontend
    assert "Math.min(2, this._weekOffset + delta)" in frontend


def test_plan_has_explicit_break_state_and_strong_finished_lesson_state() -> None:
    source = LESSON_STATES_JS.read_text(encoding="utf-8")
    assert "_mojvScheduleStatus" in source
    assert "Przerwa" in source
    assert "schedule-now-indicator" in source
    assert "schedule-state-break" in source
    assert "lesson-state-completed" in source
    assert "Odbyta" in source


def test_grades_and_messages_tabs_are_always_visible_even_when_empty() -> None:
    hub = HUB_JS.read_text(encoding="utf-8")
    assert "_mojvEnsureView" in hub
    assert '["grades", "Oceny", "5"]' in hub
    assert '["messages", "Wiadomości", "✉"]' in hub
    assert "Brak wiadomości" in hub


def test_topics_can_be_sorted_by_date_and_information_is_last_after_topics() -> None:
    hub = HUB_JS.read_text(encoding="utf-8")
    assert "data-topics-sort" in hub
    assert "_topicsSortDirection" in hub
    assert "new Date(a.date)" in hub
    assert "new Date(b.date)" in hub

    topics_push = hub.index('["topics", "Tematy", "≡"]')
    info_push = hub.index('["info", "Informacje", "ⓘ"]')
    assert topics_push < info_push


def test_plan_and_statistics_have_print_actions_with_print_css() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (HUB_JS, LESSON_STATES_JS)
    )
    assert "window.print()" in sources
    assert "data-mojv-print" in sources
    assert "@media print" in sources
    assert "Drukuj plan" in sources
    assert "Drukuj statystyki" in sources


def test_schoolwork_details_are_merged_into_homework_and_test_rows() -> None:
    api_mod = _load_api()
    transport = FakeTransport()
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url="https://student.example/city",
        session_key="SECRET",
    )

    bundle = asyncio.run(client.fetch_student(student, now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc)))

    rows = {str(row["id"]): row for row in bundle.schoolwork}
    assert rows["101"]["opis"] == "Zrób zadania 1-5 ze strony 42."
    assert rows["102"]["opis"] == "Rozdziały 3 i 4."

    homework_call = next(call for call in transport.calls if call[0].endswith("/api/ZadanieDomoweSzczegoly"))
    exam_call = next(call for call in transport.calls if call[0].endswith("/api/SprawdzianSzczegoly"))
    assert homework_call[1] == {"key": "SECRET", "id": 101}
    assert exam_call[1] == {"key": "SECRET", "id": 102}


def test_term_calendar_uses_full_description_in_detail_overlay() -> None:
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "item.description" in source
    assert "_openMojvDetail" in source
    assert "Brak dodatkowej treści" in source
