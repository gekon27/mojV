"""Message-tenant API contract for mojV live mode."""
from __future__ import annotations

import asyncio
from typing import Any, Protocol

_MESSAGES_ROOT = "https://wiadomosci." + "edu" + "vulcan.pl"


class MessageTransport(Protocol):
    async def prepare(self, city: str) -> None:
        """Initialize the message SSO session for one tenant."""

    async def get_json(self, path: str, params: dict[str, Any]) -> Any:
        """Return JSON from one message endpoint."""


def messages_base(city: str) -> str:
    return f"{_MESSAGES_ROOT}/{city}"


class MessagesApiClient:
    """Fetch inbox metadata and message bodies without exposing mailbox keys."""

    def __init__(self, transport: MessageTransport) -> None:
        self._transport = transport

    async def fetch(
        self,
        city: str,
        mailbox_key: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        city = str(city or "").strip()
        mailbox_key = str(mailbox_key or "").strip()
        if not city or not mailbox_key:
            return [], {}

        await self._transport.prepare(city)
        base = messages_base(city)
        payload = await self._transport.get_json(
            f"{base}/api/OdebraneSkrzynka",
            {
                "globalKeySkrzynka": mailbox_key,
                "idLastWiadomosc": 0,
                "pageSize": 50,
            },
        )
        inbox = self._records(payload)
        keys = tuple(
            str(row.get("apiGlobalKey") or "").strip()
            for row in inbox
            if str(row.get("apiGlobalKey") or "").strip()
        )
        if not keys:
            return inbox, {}

        responses = await asyncio.gather(
            *(
                self._transport.get_json(
                    f"{base}/api/WiadomoscSzczegoly",
                    {"apiGlobalKey": key},
                )
                for key in keys
            ),
            return_exceptions=True,
        )
        details: dict[str, Any] = {}
        for key, response in zip(keys, responses, strict=True):
            if not isinstance(response, Exception):
                details[key] = response
        return inbox, details

    @staticmethod
    def _records(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            for key in ("wiadomosci", "data", "result"):
                rows = payload.get(key)
                if isinstance(rows, list):
                    return [row for row in rows if isinstance(row, dict)]
        return []
