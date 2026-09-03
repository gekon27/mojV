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


@dataclass(frozen=True, slots=True)
class Grade:
    """A single grade entry."""

    grade_id: str
    subject: str
    value: str
    date: datetime
    description: str = ""


@dataclass(frozen=True, slots=True)
class Remark:
    """A school remark or note."""

    remark_id: str
    date: datetime
    text: str
    author: str = ""
    category: str = ""
    points: str = ""


@dataclass(frozen=True, slots=True)
class StudentSnapshot:
    """Current data for one student."""

    student: Student
    lessons: tuple[Lesson, ...]
    grades: tuple[Grade, ...] = ()
    remarks: tuple[Remark, ...] = ()


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Current data for all students."""

    students: tuple[StudentSnapshot, ...]
    updated_at: datetime
