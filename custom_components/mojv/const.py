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

MODE_DEMO = "demo"
MODE_LIVE = "live"

AUTH_BACKEND_HTTP = "http"
AUTH_BACKEND_HELPER = "helper"

DEFAULT_DEMO_STUDENTS = 2
MIN_DEMO_STUDENTS = 1
MAX_DEMO_STUDENTS = 8

DEMO_UPDATE_INTERVAL = timedelta(seconds=30)
LIVE_UPDATE_INTERVAL = timedelta(minutes=30)

ATTENDANCE_PRESENT = "present"
ATTENDANCE_ABSENT = "absent"
ATTENDANCE_EXCUSED = "excused_absence"
ATTENDANCE_LATE = "late"
ATTENDANCE_EXCUSED_LATE = "excused_late"
ATTENDANCE_SCHOOL = "school_activity"
ATTENDANCE_RELEASED = "released"
ATTENDANCE_NOT_RECORDED = "not_recorded"
