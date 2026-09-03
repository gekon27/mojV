"""Parsers for classification periods and grades."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import FinalGrade, Grade


def _parse_date(value: Any) -> datetime | None:
    """Parse the date formats currently returned by the school portal."""
    raw = str(value or "").strip()
    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass

    for fmt in (
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _text(value: Any) -> str:
    return str(value or "").strip()


def parse_grades(
    periods_payload: Any,
    grades_by_period: dict[str, Any] | None,
) -> tuple[tuple[Grade, ...], tuple[FinalGrade, ...]]:
    """Convert raw classification/grade payloads into mojV models.

    Malformed rows are intentionally skipped so one damaged entry does not
    invalidate all grades for a student.
    """
    if not isinstance(periods_payload, list):
        return (), ()

    payload_map = grades_by_period if isinstance(grades_by_period, dict) else {}
    grades: list[Grade] = []
    final_grades: list[FinalGrade] = []

    for period in periods_payload:
        if not isinstance(period, dict):
            continue
        period_id = _text(period.get("id"))
        period_number = _text(period.get("numerOkresu"))
        if not period_id or not period_number:
            continue

        payload = payload_map.get(period_id)
        if not isinstance(payload, dict):
            continue
        subjects = payload.get("ocenyPrzedmioty")
        if not isinstance(subjects, list):
            continue

        for subject_row in subjects:
            if not isinstance(subject_row, dict):
                continue
            subject = _text(subject_row.get("przedmiotNazwa")) or "Inne"
            proposed = _text(subject_row.get("proponowanaOcenaOkresowa"))
            final = _text(subject_row.get("ocenaOkresowa"))
            if proposed or final:
                final_grades.append(
                    FinalGrade(
                        subject=subject,
                        proposed=proposed,
                        final=final,
                        period=period_number,
                    )
                )

            columns = subject_row.get("kolumnyOcenyCzastkowe")
            if not isinstance(columns, list):
                continue
            for column_index, column in enumerate(columns):
                if not isinstance(column, dict):
                    continue
                column_id = _text(column.get("idKolumny")) or f"column-{column_index}"
                category = _text(column.get("kategoriaKolumny"))
                column_name = _text(column.get("nazwaKolumny"))
                description = ": ".join(part for part in (category, column_name) if part)
                grade_rows = column.get("oceny")
                if not isinstance(grade_rows, list):
                    continue

                for grade_index, grade_row in enumerate(grade_rows):
                    if not isinstance(grade_row, dict):
                        continue
                    value = _text(grade_row.get("wpis"))
                    date = _parse_date(grade_row.get("dataOceny"))
                    if not value or date is None:
                        continue
                    grade_id = (
                        f"{period_id}:{column_id}:{grade_index}:"
                        f"{date.isoformat()}:{value}"
                    )
                    grades.append(
                        Grade(
                            grade_id=grade_id,
                            subject=subject,
                            value=value,
                            date=date,
                            description=description,
                            category=category,
                            period=period_number,
                        )
                    )

    return tuple(grades), tuple(final_grades)
