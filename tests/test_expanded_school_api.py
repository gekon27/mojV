from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "school_api.py"


def _load():
    spec = importlib.util.spec_from_file_location("mojv_expanded_school_api_test", MODULE)
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
        value = self.responses.get(path, [])
        if isinstance(value, Exception):
            raise value
        return value


def test_fetch_student_requests_safe_extended_school_modules() -> None:
    api_mod = _load()
    base = "https://student.example/city"
    responses = {
        f"{base}/api/DniWolne": [{"nazwa": "Przerwa"}],
        f"{base}/api/Usprawiedliwienia": {"usprawiedliwieniaAktywne": True, "usprawiedliwienia": []},
        f"{base}/api/Nauczyciele": {"nauczyciele": [{"przedmiot": "Historia"}]},
        f"{base}/api/Informacje": {"nazwa": "Szkoła testowa"},
        f"{base}/api/SzczesliwyNumerTablica": {"id": 3, "numer": 20},
        f"{base}/api/WazneDzisiajTablica": [{"nazwa": "Matematyka - sprawdzian"}],
        f"{base}/api/WychowawcyTablica": [{"imieNazwisko": "Jan Kowalski", "isGlowny": True}],
        f"{base}/api/RealizacjaZajec": [{"id": 1, "tematOpis": "Ułamki"}],
    }
    transport = FakeTransport(responses)
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
        client.fetch_student(student, now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc))
    )

    assert bundle.free_days == responses[f"{base}/api/DniWolne"]
    assert bundle.excuses == responses[f"{base}/api/Usprawiedliwienia"]
    assert bundle.teachers == responses[f"{base}/api/Nauczyciele"]
    assert bundle.school_info == responses[f"{base}/api/Informacje"]
    assert bundle.lucky_number == responses[f"{base}/api/SzczesliwyNumerTablica"]
    assert bundle.important_today == responses[f"{base}/api/WazneDzisiajTablica"]
    assert bundle.homeroom_teachers == responses[f"{base}/api/WychowawcyTablica"]
    assert bundle.completed_lessons == responses[f"{base}/api/RealizacjaZajec"]

    paths = {path.rsplit("/api/", 1)[-1] for path, _ in transport.calls if "/api/" in path}
    assert {
        "DniWolne",
        "Usprawiedliwienia",
        "Nauczyciele",
        "Informacje",
        "SzczesliwyNumerTablica",
        "WazneDzisiajTablica",
        "WychowawcyTablica",
        "RealizacjaZajec",
    } <= paths

    completed = next(call for call in transport.calls if call[0].endswith("/api/RealizacjaZajec"))
    assert completed[1]["key"] == "SECRET"
    assert completed[1]["status"] == 1
    assert "dataOd" in completed[1]
    assert "dataDo" in completed[1]

    excuses = next(call for call in transport.calls if call[0].endswith("/api/Usprawiedliwienia"))
    assert excuses[1]["key"] == "SECRET"
    assert "dataOd" in excuses[1]
    assert "dataDo" in excuses[1]


def test_extended_modules_are_failure_isolated() -> None:
    api_mod = _load()
    base = "https://student.example/city"
    transport = FakeTransport({f"{base}/api/Informacje": RuntimeError("down")})
    client = api_mod.SchoolApiClient(transport)
    student = api_mod.StudentContext(
        student_id="1",
        name="Test",
        class_name="5A",
        base_url=base,
        session_key="SECRET",
    )

    bundle = asyncio.run(
        client.fetch_student(student, now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc))
    )

    assert "school_info" in bundle.errors
    assert bundle.school_info is None
