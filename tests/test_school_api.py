from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "school_api.py"


def _load():
    spec = importlib.util.spec_from_file_location("mojv_school_api_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def get_json(self, path: str, params: dict[str, object]):
        self.calls.append((path, dict(params)))
        response = self.responses.get(path, [])
        if isinstance(response, Exception):
            raise response
        return response


def test_fetch_student_requests_plan_attendance_schoolwork_periods_and_grades() -> None:
    api_mod = _load()
    base = "https://student.example/city"
    transport = FakeTransport(
        {
            f"{base}/api/PlanZajec": [{"plan": 1}],
            f"{base}/api/Frekwencja": [{"attendance": 1}],
            f"{base}/api/SprawdzianyZadaniaDomowe": [{"id": 7}],
            f"{base}/api/OkresyKlasyfikacyjne": [
                {"id": 101, "numerOkresu": 1},
                {"id": 102, "numerOkresu": 2},
            ],
            f"{base}/api/Oceny": {"ocenyPrzedmioty": []},
        }
    )
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url=base,
        session_key="SECRET",
        journal_id="99",
    )

    bundle = asyncio.run(
        client.fetch_student(student, now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc))
    )

    assert bundle.timetable == [{"plan": 1}]
    assert bundle.attendance == [{"attendance": 1}]
    assert bundle.schoolwork == [{"id": 7}]
    assert len(bundle.classification_periods) == 2
    assert set(bundle.grades_by_period) == {"101", "102"}
    assert bundle.errors == {}

    plan_call = next(call for call in transport.calls if call[0].endswith("/api/PlanZajec"))
    assert plan_call[1]["zakresDanych"] == "2"

    period_call = next(
        call for call in transport.calls if call[0].endswith("/api/OkresyKlasyfikacyjne")
    )
    assert period_call[1] == {"key": "SECRET", "idDziennik": "99"}

    grade_calls = [call for call in transport.calls if call[0].endswith("/api/Oceny")]
    assert {call[1]["idOkresKlasyfikacyjny"] for call in grade_calls} == {"101", "102"}

    schoolwork_call = next(
        call for call in transport.calls if call[0].endswith("/api/SprawdzianyZadaniaDomowe")
    )
    assert schoolwork_call[1]["key"] == "SECRET"
    assert "dataOd" in schoolwork_call[1]
    assert "dataDo" in schoolwork_call[1]


def test_fetch_student_isolates_optional_module_and_grade_period_failures() -> None:
    api_mod = _load()
    base = "https://student.example/city"

    class SelectiveTransport(FakeTransport):
        async def get_json(self, path: str, params: dict[str, object]):
            self.calls.append((path, dict(params)))
            if path.endswith("/api/SprawdzianyZadaniaDomowe"):
                raise RuntimeError("schoolwork down")
            if path.endswith("/api/Oceny") and params.get("idOkresKlasyfikacyjny") == "102":
                raise RuntimeError("period down")
            if path.endswith("/api/OkresyKlasyfikacyjne"):
                return [{"id": 101, "numerOkresu": 1}, {"id": 102, "numerOkresu": 2}]
            if path.endswith("/api/PlanZajec"):
                return ["plan"]
            if path.endswith("/api/Frekwencja"):
                return ["attendance"]
            if path.endswith("/api/Oceny"):
                return {"ocenyPrzedmioty": []}
            return []

    transport = SelectiveTransport({})
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url=base,
        session_key="SECRET",
        journal_id="99",
    )

    bundle = asyncio.run(
        client.fetch_student(student, now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc))
    )

    assert bundle.timetable == ["plan"]
    assert bundle.attendance == ["attendance"]
    assert bundle.grades_by_period == {"101": {"ocenyPrzedmioty": []}}
    assert "schoolwork" in bundle.errors
    assert "grades:102" in bundle.errors


def test_fetch_student_skips_classification_requests_without_journal_id() -> None:
    api_mod = _load()
    base = "https://student.example/city"
    transport = FakeTransport({})
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url=base,
        session_key="SECRET",
    )

    asyncio.run(client.fetch_student(student, now=datetime(2026, 9, 3, tzinfo=timezone.utc)))

    assert not any(path.endswith("/api/OkresyKlasyfikacyjne") for path, _ in transport.calls)
    assert not any(path.endswith("/api/Oceny") for path, _ in transport.calls)
