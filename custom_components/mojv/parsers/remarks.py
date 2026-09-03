"""Parser for school remarks and praises."""
from __future__ import annotations

from typing import Any

from ..models import Remark
from .common import parse_date, strip_html, text


def _kind(row: dict[str, Any], content: str) -> str:
    explicit = " ".join(
        text(row.get(key)).lower()
        for key in ("typ", "rodzaj", "kategoria")
        if row.get(key) is not None
    )
    combined = f"{explicit} {content.lower()}"
    if any(marker in combined for marker in ("pozytyw", "pochwa", "plus")):
        return "positive"
    if any(marker in combined for marker in ("negatyw", "uwaga", "minus")):
        return "negative"
    return "information"


def parse_remarks(payload: Any) -> tuple[Remark, ...]:
    """Convert raw remark rows without inventing missing dates or content."""
    if not isinstance(payload, list):
        return ()
    result: list[Remark] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        remark_id = text(row.get("id"))
        date = parse_date(row.get("data") or row.get("dataUwagi"))
        content = strip_html(row.get("tresc") or row.get("opis"))
        if not remark_id or date is None or not content:
            continue
        result.append(
            Remark(
                remark_id=remark_id,
                date=date,
                text=content,
                author=text(row.get("autor") or row.get("nauczyciel")),
                category=text(row.get("kategoria")),
                kind=_kind(row, content),
                points=text(row.get("liczbaPunktow") or row.get("punkty")),
            )
        )
    return tuple(result)
