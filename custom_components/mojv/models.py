"""Data models for mojV."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Student:
    """A student attached to the configured school account."""

    student_id: str
    name: str
    class_name: str = ""


@dataclass(frozen=True, slots=True)
class Lesson:
    """A single lesson."""

    number: int
    subject: str
    start: datetime
    end: datetime
    room: str = ""
    teacher: str = ""
    attendance: str = "not_recorded"
    cancelled: bool = False
    replacement: bool = False
    note: str = ""


@dataclass(frozen=True, slots=True)
class Grade:
    """A single partial grade entry."""

    grade_id: str
    subject: str
    value: str
    date: datetime
    description: str = ""
    weight: str = ""
    category: str = ""
    period: str = ""


@dataclass(frozen=True, slots=True)
class FinalGrade:
    """Proposed and final grade for a subject."""

    subject: str
    proposed: str = ""
    final: str = ""
    period: str = ""


@dataclass(frozen=True, slots=True)
class Remark:
    """A school remark, praise or informational note."""

    remark_id: str
    date: datetime
    text: str
    author: str = ""
    category: str = ""
    kind: str = "information"
    points: str = ""


@dataclass(frozen=True, slots=True)
class SchoolWork:
    """Test, quiz, homework or other dated school work."""

    work_id: str
    date: datetime
    subject: str
    title: str
    kind: str = "other"
    description: str = ""


@dataclass(frozen=True, slots=True)
class Message:
    """A message visible to the configured account."""

    message_id: str
    date: datetime
    sender: str
    subject: str
    body: str = ""
    unread: bool = False


@dataclass(frozen=True, slots=True)
class AttendanceStat:
    """Attendance statistics for all lessons or one subject."""

    subject: str = ""
    present: int = 0
    absent: int = 0
    excused: int = 0
    late: int = 0
    excused_late: int = 0
    released: int = 0
    total: int = 0


@dataclass(frozen=True, slots=True)
class Achievement:
    """Student achievement entry."""

    achievement_id: str
    date: datetime
    title: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class Meeting:
    """Parent meeting or consultation."""

    meeting_id: str
    start: datetime
    title: str
    location: str = ""
    description: str = ""


@dataclass(frozen=True, slots=True)
class LuckyNumber:
    """Daily lucky-number information."""

    date: datetime
    value: str


@dataclass(frozen=True, slots=True)
class StudentSnapshot:
    """Current data for one student."""

    student: Student
    lessons: tuple[Lesson, ...]
    grades: tuple[Grade, ...] = ()
    final_grades: tuple[FinalGrade, ...] = ()
    remarks: tuple[Remark, ...] = ()
    schoolwork: tuple[SchoolWork, ...] = ()
    messages: tuple[Message, ...] = ()
    attendance_stats: tuple[AttendanceStat, ...] = ()
    achievements: tuple[Achievement, ...] = ()
    meetings: tuple[Meeting, ...] = ()
    lucky_number: LuckyNumber | None = None


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Current data for all students."""

    students: tuple[StudentSnapshot, ...]
    updated_at: datetime
