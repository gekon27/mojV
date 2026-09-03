"""Parser for attendance statistics."""
from __future__ import annotations

from typing import Any

from ..models import AttendanceStat
from .common import text

_CATEGORY_FIELDS = {
    1: "present",
    2: "absent",
    3: "excused",
    4: "late",
    5: "excused_late",
    6: "school_activity",
    7: "released",
}


def _number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _percentage(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _one(subject: str, payload: Any) -> AttendanceStat | None:
    if not isinstance(payload, dict):
        return None
    rows = payload.get("statystyki")
    if not isinstance(rows, list) and payload.get("podsumowanie") is None:
        return None
    counts = {field: 0 for field in _CATEGORY_FIELDS.values()}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                category = int(row.get("kategoriaFrekwencji"))
            except (TypeError, ValueError):
                continue
            field = _CATEGORY_FIELDS.get(category)
            if field:
                counts[field] += _number(row.get("razem"))
    total = sum(counts.values())
    return AttendanceStat(
        subject=subject,
        total=total,
        percentage=_percentage(payload.get("podsumowanie")),
        **counts,
    )


def parse_attendance_stats(
    subjects_payload: Any,
    global_payload: Any,
    by_subject_payload: dict[str, Any] | None,
) -> tuple[AttendanceStat, ...]:
    """Return global statistics first, followed by available subjects."""
    result: list[AttendanceStat] = []
    global_stat = _one("", global_payload)
    if global_stat is not None:
        result.append(global_stat)

    payload_map = by_subject_payload if isinstance(by_subject_payload, dict) else {}
    if not isinstance(subjects_payload, list):
        return tuple(result)
    for subject_row in subjects_payload:
        if not isinstance(subject_row, dict):
            continue
        subject_id = text(subject_row.get("id"))
        subject_name = text(subject_row.get("nazwa") or subject_row.get("przedmiotNazwa"))
        if not subject_id or not subject_name or subject_id == "-1":
            continue
        stat = _one(subject_name, payload_map.get(subject_id))
        if stat is not None:
            result.append(stat)
    return tuple(result)
