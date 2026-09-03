"""Parser for account messages."""
from __future__ import annotations

from typing import Any

from ..models import Message
from .common import parse_date, strip_html, text


def parse_messages(
    inbox_payload: Any,
    details_by_key: dict[str, Any] | None,
) -> tuple[Message, ...]:
    """Join inbox metadata with message bodies returned by the detail endpoint."""
    if not isinstance(inbox_payload, list):
        return ()
    details = details_by_key if isinstance(details_by_key, dict) else {}
    result: list[Message] = []
    for row in inbox_payload:
        if not isinstance(row, dict):
            continue
        message_id = text(row.get("apiGlobalKey") or row.get("id"))
        date = parse_date(row.get("data"))
        if not message_id or date is None:
            continue
        detail = details.get(message_id)
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
