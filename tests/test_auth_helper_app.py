from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "mojv_auth_helper" / "rootfs" / "app" / "auth_runtime.py"


def _load():
    assert MODULE.exists(), "auth_runtime.py must implement browser helper parsing"
    spec = importlib.util.spec_from_file_location("mojv_auth_runtime_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_unwrap_context_accepts_nested_data_and_result() -> None:
    runtime = _load()
    payload = {"result": "ok", "data": {"uczniowie": [{"uczen": "Jan"}]}}
    assert runtime.unwrap_context(payload) == {"uczniowie": [{"uczen": "Jan"}]}


def test_context_rows_become_internal_targets_without_secret_in_public_row() -> None:
    runtime = _load()
    targets = runtime.targets_from_context(
        "gryfino",
        "https://uczen.example/gryfino/App/abc/tablica",
        {
            "uczniowie": [
                {
                    "idUczen": 12,
                    "idDziennik": 99,
                    "uczen": "Jan Kowalski",
                    "oddzial": "5A",
                    "key": "SECRET-KEY",
                }
            ]
        },
    )
    assert len(targets) == 1
    target = targets[0]
    assert target.session_key == "SECRET-KEY"
    assert target.public_dict() == {
        "student_id": "12",
        "name": "Jan Kowalski",
        "class_name": "5A",
    }
    assert "SECRET" not in str(target.public_dict())


def test_snapshot_student_never_contains_browser_or_session_secrets() -> None:
    runtime = _load()
    target = runtime.StudentTarget(
        student_id="12",
        name="Jan",
        class_name="5A",
        city="gryfino",
        app_url="https://uczen.example/gryfino/App/abc/tablica",
        session_key="SECRET",
    )
    row = runtime.public_snapshot_row(target, timetable=[], attendance=[], errors={})
    assert set(row) == {
        "student_id",
        "name",
        "class_name",
        "timetable",
        "attendance",
        "errors",
    }
    assert "SECRET" not in str(row)


def test_browser_cache_key_is_bound_to_both_username_and_password() -> None:
    runtime = _load()
    first = runtime.credential_cache_key("Parent", "secret-one")
    same = runtime.credential_cache_key(" parent ", "secret-one")
    wrong_password = runtime.credential_cache_key("Parent", "secret-two")

    assert first == same
    assert first != wrong_password
    assert "Parent" not in first
    assert "secret-one" not in first
