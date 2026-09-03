from pathlib import Path

PANEL = Path("custom_components/mojv/frontend/school-panel.js")


def _source() -> str:
    return PANEL.read_text(encoding="utf-8")


def test_panel_builds_shell_once_and_has_selective_render_pipeline() -> None:
    source = _source()
    assert "_buildShell()" in source
    assert "_applyPayload(payload)" in source
    assert "_renderNavigation()" in source
    assert "_renderActiveView()" in source


def test_panel_uses_local_ten_second_clock_without_old_full_refresh_timer() -> None:
    source = _source()
    assert "10000" in source
    assert "_tickClock()" in source
    assert "setInterval(() => this._refresh(), 30000)" not in source


def test_switching_student_and_view_is_local_state() -> None:
    source = _source()
    assert "data-student" in source
    assert "data-view" in source
    assert "this._activeStudentId" in source
    assert "this._activeView" in source


def test_schedule_navigation_and_time_line_are_local() -> None:
    source = _source()
    assert "_changeWeek(delta)" in source
    assert "this._weekOffset" in source
    assert "requestAnimationFrame" in source
    assert "_positionTimeLine()" in source


def test_schedule_groups_equal_clock_slots_across_different_dates() -> None:
    source = _source()
    assert "_slotKey(lesson)" in source
    assert "lessonKey === slot.key" in source


def test_attendance_view_uses_backend_summary() -> None:
    source = _source()
    assert "student.attendance_summary" in source
    assert "_renderAttendance(student)" in source
