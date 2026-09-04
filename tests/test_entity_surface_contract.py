from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mojv"


def test_sensor_platform_exposes_broad_school_surface() -> None:
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    required = (
        "MojVClassSensor",
        "MojVLatestGradeSensor",
        "MojVGradesCountSensor",
        "MojVFinalGradesSensor",
        "MojVUpcomingSchoolworkSensor",
        "MojVNextSchoolworkSensor",
        "MojVUnreadMessagesSensor",
        "MojVMessagesCountSensor",
        "MojVRemarksCountSensor",
        "MojVPraiseCountSensor",
        "MojVAttendancePercentageSensor",
        "MojVAbsencesCountSensor",
        "MojVLateCountSensor",
        "MojVAchievementsCountSensor",
        "MojVUpcomingMeetingsSensor",
        "MojVNextMeetingSensor",
        "MojVLuckyNumberSensor",
        "MojVImportantTodaySensor",
        "MojVLatestCompletedLessonSensor",
        "MojVNextFreeDaySensor",
        "MojVSchoolInfoSensor",
        "MojVHomeroomTeacherSensor",
        "MojVExcusesSensor",
        "MojVSubjectAttendanceSensor",
        "MojVSubjectGradesSensor",
        "MojVPeriodGradesSensor",
    )
    for name in required:
        assert f"class {name}" in source, name


def test_binary_sensor_platform_exposes_actionable_flags() -> None:
    source = (COMPONENT / "binary_sensor.py").read_text(encoding="utf-8")
    for name in (
        "MojVAbsentNowBinarySensor",
        "MojVLateNowBinarySensor",
        "MojVUnreadMessagesBinarySensor",
        "MojVSchoolworkDueBinarySensor",
        "MojVMeetingDueBinarySensor",
        "MojVImportantTodayBinarySensor",
    ):
        assert f"class {name}" in source, name


def test_calendar_platform_exposes_lessons_schoolwork_and_meetings() -> None:
    source = (COMPONENT / "calendar.py").read_text(encoding="utf-8")
    assert "class MojVSchoolCalendar" in source
    assert "class MojVSchoolworkCalendar" in source
    assert "class MojVMeetingsCalendar" in source


def test_sensitive_student_profile_fields_are_not_part_of_entity_surface() -> None:
    combined = "\n".join(
        (COMPONENT / name).read_text(encoding="utf-8")
        for name in ("sensor.py", "binary_sensor.py", "calendar.py", "panel.py")
    ).lower()
    for forbidden in (
        "pesel",
        "adreszamieszkania",
        "adreszameldowania",
        "imieojca",
        "imiematki",
        "globalkeyskrzynka",
    ):
        assert forbidden not in combined
