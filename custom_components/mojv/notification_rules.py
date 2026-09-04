"""Pure notification rules for mojV.

This module must stay independent from Home Assistant delivery services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any

from .models import AccountSnapshot, Lesson, StudentSnapshot


@dataclass(frozen=True, slots=True)
class NotificationCandidate:
    """A public, delivery-agnostic notification candidate."""

    event_id: str
    student_id: str
    student_name: str
    kind: str
    priority: str
    title: str
    message: str
    created_at: datetime
    data: dict[str, Any] = field(default_factory=dict)


def _event_id(kind: str, student_id: str, signature: str) -> str:
    digest = sha256(f"{kind}|{student_id}|{signature}".encode("utf-8")).hexdigest()
    return f"{kind}:{digest[:24]}"


def _candidate(
    snapshot: StudentSnapshot,
    kind: str,
    signature: str,
    now: datetime,
    title: str,
    message: str,
    data: dict[str, Any],
    *,
    priority: str = "normal",
) -> NotificationCandidate:
    student = snapshot.student
    return NotificationCandidate(
        event_id=_event_id(kind, student.student_id, signature),
        student_id=student.student_id,
        student_name=student.name,
        kind=kind,
        priority=priority,
        title=title,
        message=message,
        created_at=now,
        data=data,
    )


def _lesson_identity(lesson: Lesson) -> tuple[str, int, str]:
    return (lesson.start.date().isoformat(), lesson.number, lesson.subject)


def _previous_students(snapshot: AccountSnapshot) -> dict[str, StudentSnapshot]:
    return {item.student.student_id: item for item in snapshot.students}


def build_change_candidates(
    previous: AccountSnapshot | None,
    current: AccountSnapshot,
    now: datetime,
) -> tuple[NotificationCandidate, ...]:
    """Return notifications caused by differences between snapshots.

    A missing previous snapshot is treated as baseline and never emits historical
    records. A student newly appearing in an existing account is also baselined.
    """
    if previous is None:
        return ()

    result: list[NotificationCandidate] = []
    previous_students = _previous_students(previous)

    for snapshot in current.students:
        old = previous_students.get(snapshot.student.student_id)
        if old is None:
            continue
        student_name = snapshot.student.name

        old_grades = {item.grade_id for item in old.grades}
        for grade in snapshot.grades:
            if grade.grade_id in old_grades:
                continue
            result.append(
                _candidate(
                    snapshot,
                    "grade",
                    grade.grade_id,
                    now,
                    f"{student_name}: nowa ocena {grade.value}",
                    f"{grade.subject}: {grade.value} — {grade.description or 'nowy wpis'}",
                    {
                        "subject": grade.subject,
                        "grade": grade.value,
                        "description": grade.description,
                        "category": grade.category,
                        "date": grade.date.isoformat(),
                    },
                )
            )

        old_final = {(item.subject, item.period): item for item in old.final_grades}
        for grade in snapshot.final_grades:
            prior = old_final.get((grade.subject, grade.period))
            if prior is None:
                changed = bool(grade.proposed or grade.final)
            else:
                changed = (grade.proposed, grade.final) != (prior.proposed, prior.final)
            if not changed:
                continue
            value = grade.final or grade.proposed or "—"
            result.append(
                _candidate(
                    snapshot,
                    "final_grade",
                    f"{grade.subject}|{grade.period}|{grade.proposed}|{grade.final}",
                    now,
                    f"{student_name}: zmiana oceny klasyfikacyjnej",
                    f"{grade.subject}: {value}",
                    {
                        "subject": grade.subject,
                        "period": grade.period,
                        "proposed": grade.proposed,
                        "final": grade.final,
                    },
                )
            )

        old_remarks = {item.remark_id for item in old.remarks}
        for remark in snapshot.remarks:
            if remark.remark_id in old_remarks:
                continue
            kind = "praise" if remark.kind in {"positive", "praise"} else "remark"
            title = (
                f"{student_name}: nowa pochwała"
                if kind == "praise"
                else f"{student_name}: nowa uwaga"
            )
            result.append(
                _candidate(
                    snapshot,
                    kind,
                    remark.remark_id,
                    now,
                    title,
                    remark.text,
                    {
                        "text": remark.text,
                        "author": remark.author,
                        "category": remark.category,
                        "points": remark.points,
                        "date": remark.date.isoformat(),
                    },
                    priority="high" if kind == "remark" else "normal",
                )
            )

        old_messages = {item.message_id for item in old.messages}
        for message in snapshot.messages:
            if message.message_id in old_messages:
                continue
            result.append(
                _candidate(
                    snapshot,
                    "message",
                    message.message_id,
                    now,
                    f"{student_name}: nowa wiadomość",
                    f"{message.sender}: {message.subject or 'Bez tematu'}",
                    {
                        "sender": message.sender,
                        "subject": message.subject,
                        "date": message.date.isoformat(),
                        "unread": message.unread,
                    },
                )
            )

        old_schoolwork = {item.work_id for item in old.schoolwork}
        for item in snapshot.schoolwork:
            if item.work_id in old_schoolwork:
                continue
            result.append(
                _candidate(
                    snapshot,
                    "schoolwork_new",
                    item.work_id,
                    now,
                    f"{student_name}: nowy termin",
                    f"{item.subject}: {item.title}",
                    {
                        "subject": item.subject,
                        "title": item.title,
                        "kind": item.kind,
                        "date": item.date.isoformat(),
                    },
                )
            )

        old_achievements = {item.achievement_id for item in old.achievements}
        for item in snapshot.achievements:
            if item.achievement_id in old_achievements:
                continue
            result.append(
                _candidate(
                    snapshot,
                    "achievement",
                    item.achievement_id,
                    now,
                    f"{student_name}: nowe osiągnięcie",
                    item.title,
                    {
                        "title": item.title,
                        "description": item.description,
                        "date": item.date.isoformat() if item.date else None,
                    },
                )
            )

        old_meetings = {item.meeting_id for item in old.meetings}
        for item in snapshot.meetings:
            if item.meeting_id in old_meetings:
                continue
            result.append(
                _candidate(
                    snapshot,
                    "meeting_new",
                    item.meeting_id,
                    now,
                    f"{student_name}: nowe zebranie",
                    item.title or "Zebranie",
                    {
                        "title": item.title,
                        "start": item.start.isoformat(),
                        "location": item.location,
                    },
                )
            )

        old_lessons = {_lesson_identity(item): item for item in old.lessons}
        for lesson in snapshot.lessons:
            prior = old_lessons.get(_lesson_identity(lesson))
            if prior is None:
                continue
            lesson_signature = "|".join(
                (
                    lesson.start.date().isoformat(),
                    str(lesson.number),
                    lesson.subject,
                )
            )
            if lesson.attendance != prior.attendance:
                if lesson.attendance == "absent":
                    result.append(
                        _candidate(
                            snapshot,
                            "absence",
                            lesson_signature,
                            now,
                            f"{student_name}: nieobecność",
                            f"Brak obecności na lekcji: {lesson.subject}.",
                            {
                                "subject": lesson.subject,
                                "lesson_number": lesson.number,
                                "start": lesson.start.isoformat(),
                            },
                            priority="high",
                        )
                    )
                elif lesson.attendance == "late":
                    result.append(
                        _candidate(
                            snapshot,
                            "late",
                            lesson_signature,
                            now,
                            f"{student_name}: spóźnienie",
                            f"Spóźnienie na lekcję: {lesson.subject}.",
                            {
                                "subject": lesson.subject,
                                "lesson_number": lesson.number,
                                "start": lesson.start.isoformat(),
                            },
                            priority="high",
                        )
                    )
            if lesson.cancelled and not prior.cancelled:
                result.append(
                    _candidate(
                        snapshot,
                        "lesson_cancelled",
                        lesson_signature,
                        now,
                        f"{student_name}: odwołana lekcja",
                        f"Odwołano: {lesson.subject}.",
                        {
                            "subject": lesson.subject,
                            "lesson_number": lesson.number,
                            "start": lesson.start.isoformat(),
                        },
                        priority="high",
                    )
                )
            if lesson.replacement and not prior.replacement:
                result.append(
                    _candidate(
                        snapshot,
                        "lesson_replacement",
                        lesson_signature,
                        now,
                        f"{student_name}: zastępstwo",
                        f"Zastępstwo na lekcji: {lesson.subject}.",
                        {
                            "subject": lesson.subject,
                            "lesson_number": lesson.number,
                            "teacher": lesson.teacher,
                            "start": lesson.start.isoformat(),
                        },
                    )
                )
            if (
                lesson.start != prior.start
                or lesson.end != prior.end
                or lesson.room != prior.room
                or lesson.teacher != prior.teacher
            ):
                result.append(
                    _candidate(
                        snapshot,
                        "lesson_changed",
                        (
                            f"{lesson_signature}|{lesson.start.isoformat()}|"
                            f"{lesson.end.isoformat()}|{lesson.room}|{lesson.teacher}"
                        ),
                        now,
                        f"{student_name}: zmiana lekcji",
                        f"{lesson.subject}: zaktualizowano godzinę, salę lub nauczyciela.",
                        {
                            "subject": lesson.subject,
                            "lesson_number": lesson.number,
                            "start": lesson.start.isoformat(),
                            "end": lesson.end.isoformat(),
                            "room": lesson.room,
                            "teacher": lesson.teacher,
                        },
                    )
                )

    return tuple(result)


def build_time_candidates(
    snapshot: StudentSnapshot,
    now: datetime,
    options: dict[str, Any],
) -> tuple[NotificationCandidate, ...]:
    """Return notifications caused only by the current time window."""
    enabled_raw = options.get(
        "notification_types",
        ("lesson_ending", "schoolwork_due", "meeting_due"),
    )
    enabled = set(enabled_raw or ())
    result: list[NotificationCandidate] = []
    student_name = snapshot.student.name

    if "lesson_ending" in enabled:
        threshold = max(0, int(options.get("lesson_end_minutes", 5)))
        for lesson in snapshot.lessons:
            remaining = (lesson.end - now).total_seconds()
            if (
                not lesson.cancelled
                and lesson.start <= now < lesson.end
                and 0 < remaining <= threshold * 60
            ):
                result.append(
                    _candidate(
                        snapshot,
                        "lesson_ending",
                        f"{lesson.start.isoformat()}|{lesson.number}|{lesson.subject}",
                        now,
                        f"{student_name}: lekcja zaraz się kończy",
                        f"{lesson.subject} kończy się za {max(1, int((remaining + 59) // 60))} min.",
                        {
                            "subject": lesson.subject,
                            "lesson_number": lesson.number,
                            "end": lesson.end.isoformat(),
                        },
                        priority="low",
                    )
                )

    if "schoolwork_due" in enabled:
        lead_seconds = max(0, int(options.get("schoolwork_lead_hours", 24))) * 3600
        for item in snapshot.schoolwork:
            delta = (item.date - now).total_seconds()
            if 0 <= delta <= lead_seconds:
                result.append(
                    _candidate(
                        snapshot,
                        "schoolwork_due",
                        item.work_id,
                        now,
                        f"{student_name}: zbliża się termin",
                        f"{item.subject}: {item.title}",
                        {
                            "subject": item.subject,
                            "title": item.title,
                            "kind": item.kind,
                            "date": item.date.isoformat(),
                        },
                        priority="high" if delta <= 6 * 3600 else "normal",
                    )
                )

    if "meeting_due" in enabled:
        lead_seconds = max(0, int(options.get("meeting_lead_hours", 24))) * 3600
        for item in snapshot.meetings:
            delta = (item.start - now).total_seconds()
            if 0 <= delta <= lead_seconds:
                result.append(
                    _candidate(
                        snapshot,
                        "meeting_due",
                        item.meeting_id,
                        now,
                        f"{student_name}: zbliża się zebranie",
                        item.title or "Zebranie",
                        {
                            "title": item.title,
                            "start": item.start.isoformat(),
                            "location": item.location,
                        },
                    )
                )

    return tuple(result)
