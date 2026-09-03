"""Constants for mojV."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "mojv"
PLATFORMS = ("sensor", "binary_sensor", "calendar")

CONF_MODE = "mode"
CONF_DEMO_STUDENTS = "demo_students"

MODE_DEMO = "demo"
MODE_LIVE = "live"

DEFAULT_DEMO_STUDENTS = 2
MIN_DEMO_STUDENTS = 1
MAX_DEMO_STUDENTS = 8

UPDATE_INTERVAL = timedelta(seconds=30)

ATTENDANCE_PRESENT = "present"
ATTENDANCE_ABSENT = "absent"
ATTENDANCE_EXCUSED = "excused_absence"
ATTENDANCE_LATE = "late"
ATTENDANCE_EXCUSED_LATE = "excused_late"
ATTENDANCE_SCHOOL = "school_activity"
ATTENDANCE_RELEASED = "released"
ATTENDANCE_NOT_RECORDED = "not_recorded"
