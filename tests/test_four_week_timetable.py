"""Four-week timetable horizon contracts."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_MODULE = ROOT / "custom_components" / "mojv" / "school_api.py"
PANEL_JS = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel.js"


def _load_api():
    spec = importlib.util.spec_from_file_location("mojv_four_week_api_test", API_MODULE)
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
        return []


def test_timetable_request_keeps_previous_week_and_four_full_future_weeks() -> None:
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

    asyncio.run(
        client.fetch_student(
            student,
            now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc),
        )
    )

    _, params = next(call for call in transport.calls if call[0].endswith("/api/PlanZajec"))
    assert params["dataOd"] == "2026-08-24T00:00:00.000Z"
    assert params["dataDo"] == "2026-10-04T23:59:59.999Z"
    assert params["zakresDanych"] == "2"


def test_schedule_navigation_allows_four_future_weeks() -> None:
    source = PANEL_JS.read_text(encoding="utf-8")

    assert 'this._weekOffset >= 4 ? "disabled" : ""' in source
    assert "Math.min(4, this._weekOffset + delta)" in source
    assert 'this._weekOffset >= 1 ? "disabled" : ""' not in source
