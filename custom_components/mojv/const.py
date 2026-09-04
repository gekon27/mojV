"""Constants for mojV."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "mojv"
PLATFORMS = (Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR)

CONF_MODE = "mode"
CONF_DEMO_STUDENTS = "demo_students"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_AUTH_BACKEND = "auth_backend"

CONF_NOTIFICATION_TYPES = "notification_types"
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_LESSON_END_MINUTES = "lesson_end_minutes"
CONF_SCHOOLWORK_LEAD_HOURS = "schoolwork_lead_hours"
CONF_MEETING_LEAD_HOURS = "meeting_lead_hours"
CONF_QUIET_HOURS_ENABLED = "quiet_hours_enabled"
CONF_QUIET_HOURS_START = "quiet_hours_start"
CONF_QUIET_HOURS_END = "quiet_hours_end"

MODE_DEMO = "demo"
MODE_LIVE = "live"

AUTH_BACKEND_HTTP = "http"
AUTH_BACKEND_HELPER = "helper"

DEFAULT_DEMO_STUDENTS = 2
MIN_DEMO_STUDENTS = 1
MAX_DEMO_STUDENTS = 8

DEFAULT_LESSON_END_MINUTES = 5
DEFAULT_SCHOOLWORK_LEAD_HOURS = 24
DEFAULT_MEETING_LEAD_HOURS = 24
DEFAULT_QUIET_HOURS_START = "22:00"
DEFAULT_QUIET_HOURS_END = "07:00"

NOTIFICATION_TYPES = (
    "grade",
    "final_grade",
    "remark",
    "praise",
    "message",
    "absence",
    "late",
    "lesson_cancelled",
    "lesson_replacement",
    "lesson_changed",
    "lesson_ending",
    "schoolwork_new",
    "schoolwork_due",
    "meeting_new",
    "meeting_due",
    "achievement",
)
DEFAULT_NOTIFICATION_TYPES = NOTIFICATION_TYPES

DEMO_UPDATE_INTERVAL = timedelta(seconds=30)
LIVE_UPDATE_INTERVAL = timedelta(hours=1)
LIVE_POST_LESSON_DELAY = timedelta(minutes=2)

ATTENDANCE_PRESENT = "present"
ATTENDANCE_ABSENT = "absent"
ATTENDANCE_EXCUSED = "excused_absence"
ATTENDANCE_LATE = "late"
ATTENDANCE_EXCUSED_LATE = "excused_late"
ATTENDANCE_SCHOOL = "school_activity"
ATTENDANCE_RELEASED = "released"
ATTENDANCE_NOT_RECORDED = "not_recorded"
