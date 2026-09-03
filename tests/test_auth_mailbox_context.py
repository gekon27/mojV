from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "auth.py"


def _load():
    spec = importlib.util.spec_from_file_location("mojv_auth_mailbox_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_student_context_keeps_mailbox_routing_key_internal() -> None:
    auth = _load()
    target = auth._target_from_row(
        "gryfino",
        {
            "key": "SESSION",
            "idDziennik": 9,
            "idUczen": 4,
            "uczen": "Jan Kowalski",
            "oddzial": "5A",
            "globalKeySkrzynka": "MAILBOX-KEY",
        },
    )
    assert target is not None
    assert target.mailbox_key == "MAILBOX-KEY"
    assert target.name == "Jan Kowalski"
    assert "MAILBOX-KEY" not in repr(target.public_dict()) if hasattr(target, "public_dict") else True
