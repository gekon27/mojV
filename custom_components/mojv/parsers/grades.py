"""Grade payload parsing."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from ..models import FinalGrade, Grade


def parse_grades(
    payload: Any,
    *,
    period: str = "",
) -> tuple[tuple[Grade, ...], tuple[FinalGrade, ...]]:
    """Parse partial, proposed and final grades from one classification period."""
    subjects = _subjects(payload)
    grades: list[Grade] = []
    finals: list[FinalGrade] = []

    for subject_row in subjects:
        subject = str(subject_row.get("przedmiotNazwa") or "Inne").strip()
        proposed = str(subject_row.get("proponowanaOcenaOkresowa") or "").strip()
        final = str(subject_row.get("ocenaOkresowa") or "").strip()
        if proposed or final:
            finals.append(
                FinalGrade(
                    subject=subject,
                    proposed=proposed,
                    final=final,
                    period=period,
                )
            )

        for column in subject_row.get("kolumnyOcenyCzastkowe") or ():
            if not isinstance(column, dict):
                continue
            column_id = str(column.get("idKolumny") or "")
            category = str(column.get("kategoriaKolumny") or "").strip()
            column_name = str(column.get("nazwaKolumny") or "").strip()
            description = ": ".join(part for part in (category, column_name) if part)
            weight = str(
                column.get("waga")
                or column.get("wagaOceny")
                or column.get("wagaKolumny")
                or ""
            ).strip()

            for grade_row in column.get("oceny") or ():
                if not isinstance(grade_row, dict):
                    continue
                value = str(grade_row.get("wpis") or "").strip()
                if not value:
                    continue
                grade_date = _parse_datetime(grade_row.get("dataOceny"))
                if grade_date is None:
                    continue
                explicit_id = str(
                    grade_row.get("idOcena")
                    or grade_row.get("id")
                    or grade_row.get("idWpisu")
                    or ""
                ).strip()
                grade_id = explicit_id or _stable_id(
                    subject,
                    column_id,
                    value,
                    grade_date.isoformat(),
                    description,
                    period,
                )
                grades.append(
                    Grade(
                        grade_id=grade_id,
                        subject=subject,
                        value=value,
                        date=grade_date,
                        description=description,
                        weight=weight,
                        category=category,
                        period=period,
                    )
                )

    grades.sort(key=lambda item: item.date, reverse=True)
    finals.sort(key=lambda item: item.subject.casefold())
    return tuple(grades), tuple(finals)


def merge_grade_periods(
    payloads: dict[str, Any],
) -> tuple[tuple[Grade, ...], tuple[FinalGrade, ...]]:
    """Parse and combine multiple classification periods."""
    grades: dict[str, Grade] = {}
    finals: dict[tuple[str, str], FinalGrade] = {}
    for period, payload in payloads.items():
        parsed_grades, parsed_finals = parse_grades(payload, period=str(period))
        grades.update({item.grade_id: item for item in parsed_grades})
        finals.update({(item.period, item.subject): item for item in parsed_finals})
    return (
        tuple(sorted(grades.values(), key=lambda item: item.date, reverse=True)),
        tuple(
            sorted(
                finals.values(),
                key=lambda item: (item.period, item.subject.casefold()),
            )
        ),
    )


def _subjects(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get("ocenyPrzedmioty")
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.fromisoformat(text[:10])
        except ValueError:
            return None


def _stable_id(*parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return "grade-" + hashlib.sha256(raw).hexdigest()[:24]
