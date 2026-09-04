"""Sensor platform for mojV."""
from __future__ import annotations

import hashlib
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTENDANCE_NOT_RECORDED, DOMAIN
from .coordinator import MojVCoordinator
from .entity import MojVStudentEntity
from .logic import active_lesson, lessons_today, minutes_to_end, next_lesson
from .models import StudentSnapshot


def _stable_key(value: str) -> str:
    return hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()[:12]


def _global_attendance(snapshot: StudentSnapshot):  # type: ignore[no-untyped-def]
    return next((stat for stat in snapshot.attendance_stats if not stat.subject), None)


def _future_schoolwork(snapshot: StudentSnapshot, now: datetime):  # type: ignore[no-untyped-def]
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return sorted((item for item in snapshot.schoolwork if item.date >= day_start), key=lambda item: item.date)


def _future_meetings(snapshot: StudentSnapshot, now: datetime):  # type: ignore[no-untyped-def]
    return sorted((item for item in snapshot.meetings if item.start >= now), key=lambda item: item.start)


def _future_free_days(snapshot: StudentSnapshot, now: datetime):  # type: ignore[no-untyped-def]
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return sorted((item for item in snapshot.free_days if item.end >= day_start), key=lambda item: item.start)


def _grade_attrs(grade) -> dict:  # type: ignore[no-untyped-def]
    return {
        "value": grade.value,
        "subject": grade.subject,
        "date": grade.date.isoformat(),
        "description": grade.description,
        "category": grade.category,
        "period": grade.period,
        "weight": grade.weight,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up mojV sensors."""
    coordinator: MojVCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [MojVStudentsSensor(coordinator)]
    for snapshot in coordinator.data.students:
        student_id = snapshot.student.student_id
        entities.extend(
            (
                MojVCurrentLessonSensor(coordinator, student_id),
                MojVNextLessonSensor(coordinator, student_id),
                MojVLessonNumberSensor(coordinator, student_id),
                MojVMinutesToEndSensor(coordinator, student_id),
                MojVAttendanceSensor(coordinator, student_id),
                MojVTodayScheduleSensor(coordinator, student_id),
                MojVLastSyncSensor(coordinator, student_id),
                MojVClassSensor(coordinator, student_id),
                MojVLatestGradeSensor(coordinator, student_id),
                MojVGradesCountSensor(coordinator, student_id),
                MojVFinalGradesSensor(coordinator, student_id),
                MojVUpcomingSchoolworkSensor(coordinator, student_id),
                MojVNextSchoolworkSensor(coordinator, student_id),
                MojVUnreadMessagesSensor(coordinator, student_id),
                MojVMessagesCountSensor(coordinator, student_id),
                MojVRemarksCountSensor(coordinator, student_id),
                MojVPraiseCountSensor(coordinator, student_id),
                MojVAttendancePercentageSensor(coordinator, student_id),
                MojVAbsencesCountSensor(coordinator, student_id),
                MojVLateCountSensor(coordinator, student_id),
                MojVAchievementsCountSensor(coordinator, student_id),
                MojVUpcomingMeetingsSensor(coordinator, student_id),
                MojVNextMeetingSensor(coordinator, student_id),
                MojVLuckyNumberSensor(coordinator, student_id),
                MojVImportantTodaySensor(coordinator, student_id),
                MojVLatestCompletedLessonSensor(coordinator, student_id),
                MojVCompletedLessonsSensor(coordinator, student_id),
                MojVNextFreeDaySensor(coordinator, student_id),
                MojVFreeDaysSensor(coordinator, student_id),
                MojVSchoolInfoSensor(coordinator, student_id),
                MojVHomeroomTeacherSensor(coordinator, student_id),
                MojVTeachersSensor(coordinator, student_id),
                MojVExcusesSensor(coordinator, student_id),
            )
        )

        subjects = {
            stat.subject for stat in snapshot.attendance_stats if stat.subject
        } | {grade.subject for grade in snapshot.grades if grade.subject} | {
            grade.subject for grade in snapshot.final_grades if grade.subject
        }
        for subject in sorted(subjects, key=str.casefold):
            entities.append(MojVSubjectAttendanceSensor(coordinator, student_id, subject))
            entities.append(MojVSubjectGradesSensor(coordinator, student_id, subject))

        periods = {grade.period for grade in snapshot.grades if grade.period} | {
            grade.period for grade in snapshot.final_grades if grade.period
        }
        for period in sorted(periods):
            entities.append(MojVPeriodGradesSensor(coordinator, student_id, period))

    async_add_entities(entities)


class MojVStudentsSensor(CoordinatorEntity[MojVCoordinator], SensorEntity):
    """Number of students detected on the account."""

    _attr_name = "mojV uczniowie"
    _attr_icon = "mdi:account-school"

    def __init__(self, coordinator: MojVCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "mojv_students"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.students)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "students": [
                {
                    "id": item.student.student_id,
                    "name": item.student.name,
                    "class": item.student.class_name,
                }
                for item in self.coordinator.data.students
            ]
        }


class _StudentSensor(MojVStudentEntity, SensorEntity):
    key = ""
    label = ""

    def __init__(self, coordinator: MojVCoordinator, student_id: str) -> None:
        super().__init__(coordinator, student_id)
        self._attr_unique_id = f"{student_id}_{self.key}"
        self._attr_name = self.label


class MojVCurrentLessonSensor(_StudentSensor):
    key = "current_lesson"
    label = "Aktualna lekcja"
    _attr_icon = "mdi:book-open-page-variant"

    @property
    def native_value(self) -> str:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.subject if lesson else "Przerwa"

    @property
    def extra_state_attributes(self) -> dict:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        if lesson is None:
            return {"active": False}
        return {
            "active": True,
            "number": lesson.number,
            "start": lesson.start.isoformat(),
            "end": lesson.end.isoformat(),
            "room": lesson.room,
            "teacher": lesson.teacher,
            "attendance": lesson.attendance,
        }


class MojVNextLessonSensor(_StudentSensor):
    key = "next_lesson"
    label = "Następna lekcja"
    _attr_icon = "mdi:book-arrow-right"

    @property
    def native_value(self) -> str:
        lesson = next_lesson(self.student_snapshot, dt_util.now())
        return lesson.subject if lesson else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        lesson = next_lesson(self.student_snapshot, dt_util.now())
        if lesson is None:
            return {}
        return {
            "number": lesson.number,
            "start": lesson.start.isoformat(),
            "end": lesson.end.isoformat(),
            "room": lesson.room,
            "teacher": lesson.teacher,
            "attendance": lesson.attendance,
        }


class MojVLessonNumberSensor(_StudentSensor):
    key = "lesson_number"
    label = "Numer lekcji"
    _attr_icon = "mdi:numeric"

    @property
    def native_value(self) -> int:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.number if lesson else 0


class MojVMinutesToEndSensor(_StudentSensor):
    key = "minutes_to_end"
    label = "Minuty do końca"
    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "min"

    @property
    def native_value(self) -> int:
        now = dt_util.now()
        return minutes_to_end(active_lesson(self.student_snapshot, now), now)


class MojVAttendanceSensor(_StudentSensor):
    key = "attendance"
    label = "Obecność"
    _attr_icon = "mdi:account-check"

    @property
    def native_value(self) -> str:
        lesson = active_lesson(self.student_snapshot, dt_util.now())
        return lesson.attendance if lesson else ATTENDANCE_NOT_RECORDED


class MojVTodayScheduleSensor(_StudentSensor):
    key = "today_schedule"
    label = "Plan dzisiaj"
    _attr_icon = "mdi:calendar-today"

    @property
    def native_value(self) -> int:
        return len(lessons_today(self.student_snapshot, dt_util.now()))

    @property
    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        current = active_lesson(self.student_snapshot, now)
        return {
            "lessons": [
                {
                    "number": lesson.number,
                    "subject": lesson.subject,
                    "start": lesson.start.isoformat(),
                    "end": lesson.end.isoformat(),
                    "room": lesson.room,
                    "teacher": lesson.teacher,
                    "attendance": lesson.attendance,
                    "cancelled": lesson.cancelled,
                    "current": current == lesson,
                }
                for lesson in lessons_today(self.student_snapshot, now)
            ]
        }


class MojVLastSyncSensor(_StudentSensor):
    key = "last_sync"
    label = "Ostatnia synchronizacja"
    _attr_icon = "mdi:cloud-sync"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.updated_at.isoformat()


class MojVClassSensor(_StudentSensor):
    key = "class"
    label = "Klasa"
    _attr_icon = "mdi:google-classroom"

    @property
    def native_value(self) -> str:
        return self.student_snapshot.student.class_name or "Brak"


class MojVLatestGradeSensor(_StudentSensor):
    key = "latest_grade"
    label = "Ostatnia ocena"
    _attr_icon = "mdi:star-circle"

    @property
    def native_value(self) -> str:
        if not self.student_snapshot.grades:
            return "Brak"
        return max(self.student_snapshot.grades, key=lambda item: item.date).value

    @property
    def extra_state_attributes(self) -> dict:
        if not self.student_snapshot.grades:
            return {}
        return _grade_attrs(max(self.student_snapshot.grades, key=lambda item: item.date))


class MojVGradesCountSensor(_StudentSensor):
    key = "grades_count"
    label = "Liczba ocen"
    _attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.grades)


class MojVFinalGradesSensor(_StudentSensor):
    key = "final_grades"
    label = "Oceny okresowe"
    _attr_icon = "mdi:school-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.final_grades)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "grades": [
                {
                    "subject": item.subject,
                    "period": item.period,
                    "proposed": item.proposed,
                    "final": item.final,
                }
                for item in self.student_snapshot.final_grades[:30]
            ]
        }


class MojVUpcomingSchoolworkSensor(_StudentSensor):
    key = "upcoming_schoolwork"
    label = "Nadchodzący terminarz"
    _attr_icon = "mdi:clipboard-text-clock-outline"

    @property
    def native_value(self) -> int:
        return len(_future_schoolwork(self.student_snapshot, dt_util.now()))

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "items": [
                {
                    "date": item.date.isoformat(),
                    "subject": item.subject,
                    "title": item.title,
                    "kind": item.kind,
                }
                for item in _future_schoolwork(self.student_snapshot, dt_util.now())[:10]
            ]
        }


class MojVNextSchoolworkSensor(_StudentSensor):
    key = "next_schoolwork"
    label = "Najbliższy termin"
    _attr_icon = "mdi:clipboard-alert-outline"

    @property
    def native_value(self) -> str:
        items = _future_schoolwork(self.student_snapshot, dt_util.now())
        return (items[0].title or items[0].subject) if items else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        items = _future_schoolwork(self.student_snapshot, dt_util.now())
        if not items:
            return {}
        item = items[0]
        return {
            "date": item.date.isoformat(),
            "subject": item.subject,
            "kind": item.kind,
            "description": item.description,
        }


class MojVUnreadMessagesSensor(_StudentSensor):
    key = "unread_messages"
    label = "Nieprzeczytane wiadomości"
    _attr_icon = "mdi:email-alert-outline"

    @property
    def native_value(self) -> int:
        return sum(1 for item in self.student_snapshot.messages if item.unread)


class MojVMessagesCountSensor(_StudentSensor):
    key = "messages_count"
    label = "Liczba wiadomości"
    _attr_icon = "mdi:email-multiple-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.messages)


class MojVRemarksCountSensor(_StudentSensor):
    key = "remarks_count"
    label = "Liczba uwag"
    _attr_icon = "mdi:message-alert-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.remarks)


class MojVPraiseCountSensor(_StudentSensor):
    key = "praise_count"
    label = "Liczba pochwał"
    _attr_icon = "mdi:thumb-up-outline"

    @property
    def native_value(self) -> int:
        return sum(1 for item in self.student_snapshot.remarks if item.kind == "positive")


class MojVAttendancePercentageSensor(_StudentSensor):
    key = "attendance_percentage"
    label = "Frekwencja"
    _attr_icon = "mdi:percent-outline"
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        stat = _global_attendance(self.student_snapshot)
        return stat.percentage if stat else None


class MojVAbsencesCountSensor(_StudentSensor):
    key = "absences_count"
    label = "Nieobecności"
    _attr_icon = "mdi:account-off-outline"

    @property
    def native_value(self) -> int:
        stat = _global_attendance(self.student_snapshot)
        return stat.absent if stat else 0

    @property
    def extra_state_attributes(self) -> dict:
        stat = _global_attendance(self.student_snapshot)
        return {"excused": stat.excused if stat else 0}


class MojVLateCountSensor(_StudentSensor):
    key = "late_count"
    label = "Spóźnienia"
    _attr_icon = "mdi:clock-alert-outline"

    @property
    def native_value(self) -> int:
        stat = _global_attendance(self.student_snapshot)
        return (stat.late + stat.excused_late) if stat else 0

    @property
    def extra_state_attributes(self) -> dict:
        stat = _global_attendance(self.student_snapshot)
        return {
            "late": stat.late if stat else 0,
            "excused_late": stat.excused_late if stat else 0,
        }


class MojVAchievementsCountSensor(_StudentSensor):
    key = "achievements_count"
    label = "Osiągnięcia"
    _attr_icon = "mdi:trophy-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.achievements)


class MojVUpcomingMeetingsSensor(_StudentSensor):
    key = "upcoming_meetings"
    label = "Nadchodzące zebrania"
    _attr_icon = "mdi:account-group-outline"

    @property
    def native_value(self) -> int:
        return len(_future_meetings(self.student_snapshot, dt_util.now()))


class MojVNextMeetingSensor(_StudentSensor):
    key = "next_meeting"
    label = "Najbliższe zebranie"
    _attr_icon = "mdi:calendar-account-outline"

    @property
    def native_value(self) -> str:
        items = _future_meetings(self.student_snapshot, dt_util.now())
        return (items[0].title or "Zebranie") if items else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        items = _future_meetings(self.student_snapshot, dt_util.now())
        if not items:
            return {}
        item = items[0]
        return {
            "start": item.start.isoformat(),
            "location": item.location,
            "description": item.description,
            "online_url": item.online_url,
        }


class MojVLuckyNumberSensor(_StudentSensor):
    key = "lucky_number"
    label = "Szczęśliwy numerek"
    _attr_icon = "mdi:clover"

    @property
    def native_value(self) -> str:
        item = self.student_snapshot.lucky_number
        return item.value if item else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        item = self.student_snapshot.lucky_number
        return {"date": item.date.isoformat()} if item else {}


class MojVImportantTodaySensor(_StudentSensor):
    key = "important_today"
    label = "Ważne dzisiaj"
    _attr_icon = "mdi:alert-circle-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.important_today)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "items": [
                {"subject": item.subject, "kind": item.kind, "title": item.title}
                for item in self.student_snapshot.important_today[:20]
            ]
        }


class MojVLatestCompletedLessonSensor(_StudentSensor):
    key = "latest_completed_lesson"
    label = "Ostatni zrealizowany temat"
    _attr_icon = "mdi:book-check-outline"

    @property
    def native_value(self) -> str:
        if not self.student_snapshot.completed_lessons:
            return "Brak"
        return max(self.student_snapshot.completed_lessons, key=lambda item: item.date).subject

    @property
    def extra_state_attributes(self) -> dict:
        if not self.student_snapshot.completed_lessons:
            return {}
        item = max(self.student_snapshot.completed_lessons, key=lambda row: row.date)
        return {
            "date": item.date.isoformat(),
            "teacher": item.teacher,
            "topic": item.topic,
            "lesson_number": item.lesson_number,
            "online_url": item.online_url,
        }


class MojVCompletedLessonsSensor(_StudentSensor):
    key = "completed_lessons_count"
    label = "Zrealizowane tematy"
    _attr_icon = "mdi:book-multiple-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.completed_lessons)


class MojVNextFreeDaySensor(_StudentSensor):
    key = "next_free_day"
    label = "Najbliższy dzień wolny"
    _attr_icon = "mdi:calendar-remove-outline"

    @property
    def native_value(self) -> str:
        items = _future_free_days(self.student_snapshot, dt_util.now())
        return items[0].name if items else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        items = _future_free_days(self.student_snapshot, dt_util.now())
        if not items:
            return {}
        item = items[0]
        return {"start": item.start.isoformat(), "end": item.end.isoformat()}


class MojVFreeDaysSensor(_StudentSensor):
    key = "free_days_count"
    label = "Dni wolne"
    _attr_icon = "mdi:calendar-star"

    @property
    def native_value(self) -> int:
        return len(_future_free_days(self.student_snapshot, dt_util.now()))


class MojVSchoolInfoSensor(_StudentSensor):
    key = "school_info"
    label = "Szkoła"
    _attr_icon = "mdi:school"

    @property
    def native_value(self) -> str:
        item = self.student_snapshot.school_info
        return item.name if item else "Brak"

    @property
    def extra_state_attributes(self) -> dict:
        item = self.student_snapshot.school_info
        if item is None:
            return {}
        return {
            "city": item.city,
            "address": item.address,
            "website": item.website,
            "email": item.email,
            "directors": list(item.directors),
        }


class MojVHomeroomTeacherSensor(_StudentSensor):
    key = "homeroom_teacher"
    label = "Wychowawca"
    _attr_icon = "mdi:account-tie-outline"

    @property
    def native_value(self) -> str:
        rows = self.student_snapshot.homeroom_teachers
        if not rows:
            return "Brak"
        primary = next((item for item in rows if item.primary), rows[0])
        return primary.name

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "teachers": [
                {"name": item.name, "primary": item.primary}
                for item in self.student_snapshot.homeroom_teachers
            ]
        }


class MojVTeachersSensor(_StudentSensor):
    key = "teachers_count"
    label = "Nauczyciele"
    _attr_icon = "mdi:account-multiple-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.teachers)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "teachers": [
                {"name": item.name, "subject": item.subject, "homeroom": item.homeroom}
                for item in self.student_snapshot.teachers[:40]
            ]
        }


class MojVExcusesSensor(_StudentSensor):
    key = "excuses"
    label = "Usprawiedliwienia"
    _attr_icon = "mdi:file-check-outline"

    @property
    def native_value(self) -> int:
        return len(self.student_snapshot.excuses.entries)

    @property
    def extra_state_attributes(self) -> dict:
        value = self.student_snapshot.excuses
        return {
            "active": value.active,
            "blocked": value.blocked,
            "entries": [
                {
                    "date": item.date.isoformat(),
                    "lesson_number": item.lesson_number,
                    "status": item.status,
                }
                for item in value.entries[:20]
            ],
        }


class MojVSubjectAttendanceSensor(_StudentSensor):
    """Attendance percentage for one subject."""

    _attr_icon = "mdi:chart-donut"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: MojVCoordinator, student_id: str, subject: str) -> None:
        self.subject = subject
        self.key = f"subject_attendance_{_stable_key(subject)}"
        self.label = f"Frekwencja — {subject}"
        super().__init__(coordinator, student_id)

    @property
    def _stat(self):  # type: ignore[no-untyped-def]
        return next((item for item in self.student_snapshot.attendance_stats if item.subject == self.subject), None)

    @property
    def native_value(self) -> float | None:
        stat = self._stat
        return stat.percentage if stat else None

    @property
    def extra_state_attributes(self) -> dict:
        stat = self._stat
        if stat is None:
            return {"subject": self.subject}
        return {
            "subject": self.subject,
            "present": stat.present,
            "absent": stat.absent,
            "excused": stat.excused,
            "late": stat.late,
            "excused_late": stat.excused_late,
            "school_activity": stat.school_activity,
            "released": stat.released,
            "total": stat.total,
        }


class MojVSubjectGradesSensor(_StudentSensor):
    """Grade count and recent grades for one subject."""

    _attr_icon = "mdi:star-box-multiple-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str, subject: str) -> None:
        self.subject = subject
        self.key = f"subject_grades_{_stable_key(subject)}"
        self.label = f"Oceny — {subject}"
        super().__init__(coordinator, student_id)

    @property
    def _grades(self):  # type: ignore[no-untyped-def]
        return sorted(
            (item for item in self.student_snapshot.grades if item.subject == self.subject),
            key=lambda item: item.date,
            reverse=True,
        )

    @property
    def native_value(self) -> int:
        return len(self._grades)

    @property
    def extra_state_attributes(self) -> dict:
        finals = [
            item for item in self.student_snapshot.final_grades if item.subject == self.subject
        ]
        return {
            "subject": self.subject,
            "latest": _grade_attrs(self._grades[0]) if self._grades else None,
            "recent": [_grade_attrs(item) for item in self._grades[:10]],
            "periodic": [
                {
                    "period": item.period,
                    "proposed": item.proposed,
                    "final": item.final,
                }
                for item in finals
            ],
        }


class MojVPeriodGradesSensor(_StudentSensor):
    """Grade count for one classification period."""

    _attr_icon = "mdi:calendar-range-outline"

    def __init__(self, coordinator: MojVCoordinator, student_id: str, period: str) -> None:
        self.period = period
        self.key = f"period_grades_{_stable_key(period)}"
        self.label = f"Oceny — okres {period}"
        super().__init__(coordinator, student_id)

    @property
    def _grades(self):  # type: ignore[no-untyped-def]
        return sorted(
            (item for item in self.student_snapshot.grades if item.period == self.period),
            key=lambda item: item.date,
            reverse=True,
        )

    @property
    def native_value(self) -> int:
        return len(self._grades)

    @property
    def extra_state_attributes(self) -> dict:
        finals = [
            item for item in self.student_snapshot.final_grades if item.period == self.period
        ]
        return {
            "period": self.period,
            "recent": [_grade_attrs(item) for item in self._grades[:15]],
            "periodic": [
                {
                    "subject": item.subject,
                    "proposed": item.proposed,
                    "final": item.final,
                }
                for item in finals[:30]
            ],
        }
