from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "helper_protocol.py"


def _load():
    assert MODULE.exists(), "helper_protocol.py must implement the local auth-helper contract"
    spec = importlib.util.spec_from_file_location("mojv_helper_protocol_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_selects_installed_auth_helper_by_slug_suffix() -> None:
    helper = _load()
    payload = {
        "data": {
            "addons": [
                {"slug": "core_mosquitto", "installed": "6.5.0"},
                {"slug": "abc123_mojv_auth_helper", "installed": "0.1.0"},
            ]
        }
    }
    assert helper.select_helper_slug(payload) == "abc123_mojv_auth_helper"


def test_supervisor_data_unwraps_result_and_data_envelopes() -> None:
    helper = _load()
    assert helper.unwrap_supervisor({"result": "ok", "data": {"hostname": "helper-host"}}) == {
        "hostname": "helper-host"
    }
    assert helper.unwrap_supervisor({"data": {"addons": []}}) == {"addons": []}


def test_helper_snapshot_rejects_secret_fields() -> None:
    helper = _load()
    payload = {
        "students": [
            {
                "student_id": "1",
                "name": "Jan Kowalski",
                "class_name": "5A",
                "timetable": [],
                "attendance": [],
                "journal_id": "99",
                "grades_by_period": {"1": {"token": "nested-secret"}},
            }
        ]
    }
    assert helper.validate_snapshot(payload) is False


def test_helper_snapshot_rejects_nested_secret_fields() -> None:
    helper = _load()
    payload = {
        "students": [
            {
                "student_id": "1",
                "name": "Jan Kowalski",
                "class_name": "5A",
                "timetable": [],
                "attendance": [],
                "grades_by_period": {"1": {"cookies": {"secret": "x"}}},
            }
        ]
    }
    assert helper.validate_snapshot(payload) is False


def test_helper_snapshot_accepts_public_school_payload() -> None:
    helper = _load()
    payload = {
        "students": [
            {
                "student_id": "1",
                "name": "Jan Kowalski",
                "class_name": "5A",
                "timetable": [{"przedmiot": "Matematyka"}],
                "attendance": [],
                "classification_periods": [{"id": 1, "numerOkresu": 1}],
                "grades_by_period": {"1": {"ocenyPrzedmioty": []}},
                "schoolwork": [{"id": 7, "typ": 4}],
                "errors": {},
            }
        ]
    }
    assert helper.validate_snapshot(payload) is True
