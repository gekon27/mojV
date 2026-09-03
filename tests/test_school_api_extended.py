from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "school_api.py"


def _load():
    spec = importlib.util.spec_from_file_location("mojv_school_api_extended_test", MODULE)
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
        if path.endswith("/api/Przedmioty"):
            return [{"id": 7, "nazwa": "Matematyka"}]
        if path.endswith("/api/FrekwencjaStatystyki"):
            return {"podsumowanie": 95, "statystyki": []}
        if path.endswith("/api/OkresyKlasyfikacyjne"):
            return []
        return []


def test_fetch_student_requests_new_live_modules_and_subject_attendance() -> None:
    api_mod = _load()
    base = "https://student.example/city"
    transport = FakeTransport()
    student = api_mod.StudentContext(
        student_id="1",
        name="Jan",
        class_name="5A",
        base_url=base,
        session_key="SECRET",
        journal_id="99",
        mailbox_key="MAILBOX",
    )
    bundle = asyncio.run(
        api_mod.SchoolApiClient(transport).fetch_student(
            student,
            now=datetime(2026, 9, 4, 8, tzinfo=timezone.utc),
        )
    )

    paths = [path for path, _ in transport.calls]
    assert f"{base}/api/Uwagi" in paths
    assert f"{base}/api/Osiagniecia" in paths
    assert f"{base}/api/Zebrania" in paths
    assert f"{base}/api/Przedmioty" in paths
    assert f"{base}/api/FrekwencjaStatystyki" in paths
    assert bundle.remarks == []
    assert bundle.achievements == []
    assert bundle.meetings == []
    assert bundle.attendance_subjects == [{"id": 7, "nazwa": "Matematyka"}]
    assert bundle.attendance_summary == {"podsumowanie": 95, "statystyki": []}
    assert bundle.attendance_by_subject == {"7": {"podsumowanie": 95, "statystyki": []}}

    global_stats = next(
        params
        for path, params in transport.calls
        if path.endswith("/api/FrekwencjaStatystyki") and params.get("idPrzedmiot") == -1
    )
    assert global_stats == {"key": "SECRET", "idPrzedmiot": -1}

    subject_stats = [
        params
        for path, params in transport.calls
        if path.endswith("/api/FrekwencjaStatystyki") and params.get("idPrzedmiot") == 7
    ]
    assert subject_stats == [{"key": "SECRET", "idPrzedmiot": 7}]


def test_new_live_module_failures_are_isolated() -> None:
    api_mod = _load()
    base = "https://student.example/city"

    class Selective(FakeTransport):
        async def get_json(self, path: str, params: dict[str, object]):
            self.calls.append((path, dict(params)))
            if path.endswith("/api/Uwagi"):
                raise RuntimeError("down")
            if path.endswith("/api/Osiagniecia"):
                return [{"id": 1, "tresc": "OK"}]
            if path.endswith("/api/Przedmioty"):
                return []
            if path.endswith("/api/FrekwencjaStatystyki"):
                return {"podsumowanie": 100, "statystyki": []}
            return []

    bundle = asyncio.run(
        api_mod.SchoolApiClient(Selective()).fetch_student(
            api_mod.StudentContext(
                student_id="1",
                name="Jan",
                class_name="5A",
                base_url=base,
                session_key="SECRET",
            ),
            now=datetime(2026, 9, 4, tzinfo=timezone.utc),
        )
    )
    assert "remarks" in bundle.errors
    assert bundle.achievements == [{"id": 1, "tresc": "OK"}]
    assert bundle.timetable == []
