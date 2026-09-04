"""Build normalized mojV student snapshots from raw school payloads."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, tzinfo
from typing import Any

from .models import (
    Achievement,
    AttendanceExcuses,
    CompletedLesson,
    FreeDay,
    Grade,
    Meeting,
    Message,
    SchoolWork,
    Student,
    StudentSnapshot,
)
from .parsers.achievements import parse_achievements
from .parsers.attendance import parse_attendance_stats
from .parsers.extras import (
    parse_completed_lessons,
    parse_excuses,
    parse_free_days,
    parse_homeroom_teachers,
    parse_important_today,
    parse_lucky_number,
    parse_school_info,
    parse_teachers,
)
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
    lucky_number: Any = None,
    free_days: Any = None,
    excuses: Any = None,
    teachers: Any = None,
    school_info: Any = None,
    important_today: Any = None,
    homeroom_teachers: Any = None,
    completed_lessons: Any = None,
    snapshot_time: datetime | None = None,
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
        replace(
            item,
            date=_localize(item.date, timezone),
            created_at=_localize(item.created_at, timezone),
            due_at=_localize(item.due_at, timezone),
        )
        for item in raw_schoolwork
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

    raw_free_days = parse_free_days(free_days)
    normalized_free_days: tuple[FreeDay, ...] = tuple(
        replace(
            item,
            start=_localize(item.start, timezone),
            end=_localize(item.end, timezone),
        )
        for item in raw_free_days
    )

    raw_excuses = parse_excuses(excuses)
    normalized_excuses = AttendanceExcuses(
        active=raw_excuses.active,
        blocked=raw_excuses.blocked,
        entries=tuple(
            replace(item, date=_localize(item.date, timezone))
            for item in raw_excuses.entries
        ),
    )

    raw_completed = parse_completed_lessons(completed_lessons)
    normalized_completed: tuple[CompletedLesson, ...] = tuple(
        replace(item, date=_localize(item.date, timezone)) for item in raw_completed
    )

    effective_time = snapshot_time
    if effective_time is None:
        effective_time = datetime.now(tz=timezone) if timezone is not None else datetime.now()

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
        lucky_number=parse_lucky_number(lucky_number, effective_time),
        free_days=normalized_free_days,
        excuses=normalized_excuses,
        teachers=parse_teachers(teachers),
        school_info=parse_school_info(school_info),
        important_today=parse_important_today(important_today),
        homeroom_teachers=parse_homeroom_teachers(homeroom_teachers),
        completed_lessons=normalized_completed,
    )
