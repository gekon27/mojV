from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "mojv" / "messages_api.py"


def _load():
    spec = importlib.util.spec_from_file_location("mojv_messages_api_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self) -> None:
        self.prepared: list[str] = []
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def prepare(self, city: str) -> None:
        self.prepared.append(city)

    async def get_json(self, path: str, params: dict[str, object]):
        self.calls.append((path, dict(params)))
        if path.endswith("/api/OdebraneSkrzynka"):
            return [
                {
                    "apiGlobalKey": "m1",
                    "data": "2026-09-04T08:00:00",
                    "korespondenci": "Sekretariat",
                    "temat": "Informacja",
                    "przeczytana": False,
                },
                {"apiGlobalKey": "m2", "data": "2026-09-03T08:00:00"},
            ]
        if path.endswith("/api/WiadomoscSzczegoly"):
            return {"tresc": f"Body {params['apiGlobalKey']}"}
        return []


def test_messages_client_initializes_city_sso_and_fetches_details_concurrently() -> None:
    mod = _load()
    transport = FakeTransport()
    inbox, details = asyncio.run(
        mod.MessagesApiClient(transport).fetch("gryfino", "MAILBOX")
    )
    assert transport.prepared == ["gryfino"]
    inbox_call = next(call for call in transport.calls if call[0].endswith("/api/OdebraneSkrzynka"))
    assert inbox_call[1] == {
        "globalKeySkrzynka": "MAILBOX",
        "idLastWiadomosc": 0,
        "pageSize": 50,
    }
    assert len(inbox) == 2
    assert details == {"m1": {"tresc": "Body m1"}, "m2": {"tresc": "Body m2"}}


def test_messages_client_returns_empty_without_mailbox_key() -> None:
    mod = _load()
    transport = FakeTransport()
    inbox, details = asyncio.run(mod.MessagesApiClient(transport).fetch("gryfino", ""))
    assert inbox == []
    assert details == {}
    assert transport.prepared == []
