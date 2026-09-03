"""Parser for student achievements."""
from __future__ import annotations

from typing import Any

from ..models import Achievement
from .common import parse_date, strip_html, text


def parse_achievements(payload: Any) -> tuple[Achievement, ...]:
    """Parse achievements while preserving a genuinely missing date as None."""
    if not isinstance(payload, list):
        return ()
    result: list[Achievement] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        achievement_id = text(row.get("id"))
        raw_text = strip_html(row.get("tresc") or row.get("opis"))
        explicit_title = text(row.get("tytul") or row.get("nazwa"))
        title = explicit_title or raw_text
        if not achievement_id or not title:
            continue
        result.append(
            Achievement(
                achievement_id=achievement_id,
                date=parse_date(row.get("data") or row.get("dataCzas")),
                title=title,
                description=raw_text if explicit_title and raw_text != explicit_title else "",
            )
        )
    return tuple(result)
