"""Parser for account messages."""
from __future__ import annotations

import hashlib
from typing import Any

from ..models import Message
from .common import parse_date, strip_html, text


def _public_message_id(routing_key: str) -> str:
    """Map a portal routing key to a stable non-secret public identifier."""
    return hashlib.sha256(routing_key.encode("utf-8")).hexdigest()[:24]


def parse_messages(
    inbox_payload: Any,
    details_by_key: dict[str, Any] | None,
) -> tuple[Message, ...]:
    """Join inbox metadata with message bodies without exposing routing keys."""
    if not isinstance(inbox_payload, list):
        return ()
    details = details_by_key if isinstance(details_by_key, dict) else {}
    result: list[Message] = []
    for row in inbox_payload:
        if not isinstance(row, dict):
            continue
        routing_key = text(row.get("apiGlobalKey"))
        existing_public_id = text(row.get("id"))
        message_id = _public_message_id(routing_key) if routing_key else existing_public_id
        detail_key = routing_key or existing_public_id
        date = parse_date(row.get("data"))
        if not message_id or date is None:
            continue
        detail = details.get(detail_key)
        detail_row = detail if isinstance(detail, dict) else {}
        body = strip_html(detail_row.get("tresc") or row.get("tresc"))
        has_read_flag = "przeczytana" in row
        result.append(
            Message(
                message_id=message_id,
                date=date,
                sender=text(row.get("korespondenci") or row.get("nadawca")),
                subject=text(row.get("temat")),
                body=body,
                unread=(not bool(row.get("przeczytana"))) if has_read_flag else False,
            )
        )
    return tuple(result)
