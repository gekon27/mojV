"""Build normalized mojV student snapshots from raw school payloads."""
from __future__ import annotations

from dataclasses import replace
from datetime import tzinfo
from typing import Any

from .models import Achievement, Grade, Meeting, Message, SchoolWork, Student, StudentSnapshot
from .parsers.achievements import parse_achievements
from .parsers.attendance import parse_attendance_stats
from .parsers.grades import parse_grades
from .parsers.meetings import parse_meetings
from .parsers.messages import parse_messages
from .parsers.remarks import parse_remarks
from .parsers.schoolwork import parse_schoolwork
from .parsers.timetable import parse_timetable


def _localize(value, timezone: tzinfo | None):  # type: ignore[no-untyped-def]
    if value is not None and timezone is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone)
    return value


def build_student_snapshot(
    *,
    student_id: str,
    name: str,
    class_name: str,
    timetable: Any,
    attendance: Any,
    attendance_subjects: Any = None,
    attendance_summary: Any = None,
    attendance_by_subject: dict[str, Any] | None = None,
    classification_periods: Any = None,
    grades_by_period: dict[str, Any] | None = None,
    remarks: Any = None,
    schoolwork: Any = None,
    schoolwork_details: dict[str, Any] | None = None,
    messages: Any = None,
    message_details: dict[str, Any] | None = None,
    achievements: Any = None,
    meetings: Any = None,
    timezone: tzinfo | None = None,
) -> StudentSnapshot:
    """Normalize all supported live modules for one student."""
    lessons = tuple(
        replace(
            lesson,
            start=_localize(lesson.start, timezone),
            end=_localize(lesson.end, timezone),
        )
        for lesson in parse_timetable(timetable, attendance)
    )

    raw_grades, final_grades = parse_grades(classification_periods, grades_by_period)
    grades: tuple[Grade, ...] = tuple(
        replace(grade, date=_localize(grade.date, timezone)) for grade in raw_grades
    )

    raw_schoolwork = parse_schoolwork(schoolwork, schoolwork_details)
    normalized_schoolwork: tuple[SchoolWork, ...] = tuple(
        replace(item, date=_localize(item.date, timezone)) for item in raw_schoolwork
    )

    raw_remarks = parse_remarks(remarks)
    normalized_remarks = tuple(
        replace(item, date=_localize(item.date, timezone)) for item in raw_remarks
    )

    raw_messages = parse_messages(messages, message_details)
    normalized_messages: tuple[Message, ...] = tuple(
        replace(item, date=_localize(item.date, timezone)) for item in raw_messages
    )

    raw_achievements = parse_achievements(achievements)
    normalized_achievements: tuple[Achievement, ...] = tuple(
        replace(item, date=_localize(item.date, timezone))
        if item.date is not None
        else item
        for item in raw_achievements
    )

    raw_meetings = parse_meetings(meetings)
    normalized_meetings: tuple[Meeting, ...] = tuple(
        replace(item, start=_localize(item.start, timezone)) for item in raw_meetings
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
        remarks=normalized_remarks,
        schoolwork=normalized_schoolwork,
        messages=normalized_messages,
        attendance_stats=parse_attendance_stats(
            attendance_subjects,
            attendance_summary,
            attendance_by_subject,
        ),
        achievements=normalized_achievements,
        meetings=normalized_meetings,
    )
