"""Pure student-row selection helpers for mojV panel payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Any


def select_student_rows(
    candidates: list[tuple[datetime, int, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Return one deterministic newest row for each stable student ID."""
    first_order: dict[str, int] = {}
    winners: dict[str, tuple[datetime, int, dict[str, Any]]] = {}

    for stamp, index, row in candidates:
        student_id = str(row.get("id") or "")
        if not student_id:
            continue
        first_order.setdefault(student_id, index)
        current = winners.get(student_id)
        if current is None or stamp > current[0]:
            winners[student_id] = (stamp, index, row)

    return [
        winners[student_id][2]
        for student_id in sorted(first_order, key=first_order.get)
    ]
