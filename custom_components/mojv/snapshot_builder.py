"""Build normalized mojV student snapshots from raw school payloads."""
from __future__ import annotations

from dataclasses import replace
from datetime import tzinfo
from typing import Any

from .models import Grade, SchoolWork, Student, StudentSnapshot
from .parsers.grades import parse_grades
from .parsers.schoolwork import parse_schoolwork
from .parsers.timetable import parse_timetable


def _localize(value, timezone: tzinfo | None):  # type: ignore[no-untyped-def]
    if timezone is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone)
    return value


def build_student_snapshot(
    *,
    student_id: str,
    name: str,
    class_name: str,
    timetable: Any,
    attendance: Any,
    classification_periods: Any = None,
    grades_by_period: dict[str, Any] | None = None,
    schoolwork: Any = None,
    schoolwork_details: dict[str, Any] | None = None,
    timezone: tzinfo | None = None,
) -> StudentSnapshot:
    """Normalize all currently supported live modules for one student."""
    lessons = tuple(
        replace(
            lesson,
            start=_localize(lesson.start, timezone),
            end=_localize(lesson.end, timezone),
        )
        for lesson in parse_timetable(timetable, attendance)
    )

    raw_grades, final_grades = parse_grades(
        classification_periods,
        grades_by_period,
    )
    grades: tuple[Grade, ...] = tuple(
        replace(grade, date=_localize(grade.date, timezone))
        for grade in raw_grades
    )

    raw_schoolwork = parse_schoolwork(schoolwork, schoolwork_details)
    normalized_schoolwork: tuple[SchoolWork, ...] = tuple(
        replace(item, date=_localize(item.date, timezone))
        for item in raw_schoolwork
    )

    return StudentSnapshot(
        student=Student(
            student_id=str(student_id),
            name=str(name),
            class_name=str(class_name),
        ),
        lessons=lessons,
        grades=grades,
        final_grades=final_grades,
        schoolwork=normalized_schoolwork,
    )
