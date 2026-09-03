from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "mojv"

parent = types.ModuleType("custom_components")
parent.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", parent)

package = types.ModuleType("custom_components.mojv")
package.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("custom_components.mojv", package)


def _load(name: str):
    full_name = f"custom_components.mojv.{name}"
    spec = importlib.util.spec_from_file_location(full_name, PKG_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


school_api = _load("school_api")
StudentContext = school_api.StudentContext
SchoolApiClient = school_api.SchoolApiClient


class FakeTransport:
    def __init__(self, *, fail: set[str] | None = None) -> None:
        self.fail = fail or set()
        self.calls: list[tuple[str, dict]] = []

    async def get_json(self, path: str, params: dict):
        self.calls.append((path, dict(params)))
        endpoint = path.rsplit("/", 1)[-1]
        if endpoint in self.fail:
            raise RuntimeError(f"{endpoint} unavailable")
        if endpoint == "OkresyKlasyfikacyjne":
            return [
                {"id": 10, "numerOkresu": 1},
                {"id": 20, "numerOkresu": 2},
            ]
        if endpoint == "Oceny":
            return [{"period": params["idOkresKlasyfikacyjny"]}]
        return {"endpoint": endpoint}


def _student(student_id: str = "s1") -> StudentContext:
    return StudentContext(
        student_id=student_id,
        name=f"Student {student_id}",
        base_url="https://school.invalid/city",
        session_key=f"key-{student_id}",
        journal_id=f"journal-{student_id}",
    )


def test_fetch_student_isolates_optional_module_failure() -> None:
    transport = FakeTransport(fail={"Uwagi"})
    client = SchoolApiClient(transport)
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)

    bundle = asyncio.run(client.fetch_student(_student(), now=now))

    assert bundle.timetable == {"endpoint": "PlanZajec"}
    assert bundle.attendance == {"endpoint": "Frekwencja"}
    assert "remarks" in bundle.errors
    assert "grades:1" not in bundle.errors
    assert bundle.grades_by_period["1"] == [{"period": "10"}]
    assert bundle.grades_by_period["2"] == [{"period": "20"}]


def test_fetch_student_uses_expected_journal_and_date_parameters() -> None:
    transport = FakeTransport()
    client = SchoolApiClient(transport)
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)

    asyncio.run(client.fetch_student(_student(), now=now))

    calls = {path.rsplit("/", 1)[-1]: params for path, params in transport.calls}
    assert calls["OkresyKlasyfikacyjne"]["idDziennik"] == "journal-s1"
    assert calls["PlanZajec"]["dataOd"].startswith("2026-08-24T")
    assert calls["PlanZajec"]["dataDo"].startswith("2026-09-24T")
    assert calls["FrekwencjaStatystyki"]["idPrzedmiot"] == -1


def test_fetch_many_keeps_students_independent() -> None:
    class SelectiveTransport(FakeTransport):
        async def get_json(self, path: str, params: dict):
            if params.get("key") == "key-s2" and path.endswith("/PlanZajec"):
                raise RuntimeError("student 2 timetable unavailable")
            return await super().get_json(path, params)

    transport = SelectiveTransport()
    client = SchoolApiClient(transport)
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)

    first, second = asyncio.run(
        client.fetch_many((_student("s1"), _student("s2")), now=now)
    )

    assert first.timetable == {"endpoint": "PlanZajec"}
    assert not first.errors.get("timetable")
    assert "timetable" in second.errors
    assert second.attendance == {"endpoint": "Frekwencja"}
