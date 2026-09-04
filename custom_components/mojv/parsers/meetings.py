"""Parser for parent meetings and consultations."""
from __future__ import annotations

from typing import Any

from ..models import Meeting
from .common import parse_date, strip_html, text


def parse_meetings(payload: Any) -> tuple[Meeting, ...]:
    if not isinstance(payload, list):
        return ()
    result: list[Meeting] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        meeting_id = text(row.get("id"))
        start = parse_date(row.get("dataCzas") or row.get("data"))
        if not meeting_id or start is None:
            continue
        online_raw = row.get("zebranieOnline") or row.get("link") or ""
        result.append(
            Meeting(
                meeting_id=meeting_id,
                start=start,
                title=text(row.get("tytul") or row.get("nazwa")),
                location=text(row.get("sala") or row.get("miejsce")),
                description=strip_html(row.get("opis")),
                online_url=text(online_raw),
            )
        )
    return tuple(result)
