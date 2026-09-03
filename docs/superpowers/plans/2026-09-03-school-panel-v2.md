# School Panel v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current full-rerender School panel with a faster application-style panel containing Today, Schedule and Attendance views, local week navigation and a local lesson clock.

**Architecture:** Keep the existing Home Assistant WebSocket data contract and coordinator as the only source of remote data. Refactor `school-panel.js` so its shell and event listeners are created once, state changes render only the active view, and time-dependent UI updates locally every 10 seconds. Add a compact attendance summary to the panel payload to avoid recomputing status aggregates in multiple frontend paths.

**Tech Stack:** Home Assistant custom integration, Python 3.13, vanilla Web Components/JavaScript, CSS Grid/Flex, pytest, Node syntax validation.

**Spec:** `docs/superpowers/specs/2026-09-03-school-panel-v2-design.md`

## Global Constraints

- No new frontend runtime dependencies.
- No credentials, cookies, tokens or session keys may reach the frontend or logs.
- Do not copy JS/CSS implementation from the GPL-3.0 reference repository.
- Week switching for offsets `-1`, `0`, `1` must be local and must not call WebSocket.
- A 10-second local ticker must not call WebSocket.
- Optional modules are hidden when LIVE data is absent.
- Reserved portal naming must not be introduced into project files.

---

### Task 1: Attendance presentation contract

**Files:**
- Modify: `custom_components/mojv/panel.py`
- Create: `tests/test_panel_view_model.py`

**Interfaces:**
- Produces: `_attendance_summary(snapshot) -> dict[str, int]`
- Produces in each student payload: `attendance_summary` with keys `present`, `absent`, `excused_absence`, `late`, `excused_late`, `school_activity`, `released`, `not_recorded`, `unknown`.

- [ ] **Step 1: Write a failing unit test** that loads `models.py` and a pure panel-view helper without importing Home Assistant, or extracts the aggregation into a small pure module if needed. Create lessons with mixed attendance and assert exact counts.
- [ ] **Step 2: Run `pytest -q tests/test_panel_view_model.py`** and confirm RED because the summary helper does not exist.
- [ ] **Step 3: Implement the minimal pure aggregation helper** and wire its result into `_student_dict`.
- [ ] **Step 4: Run `pytest -q tests/test_panel_view_model.py tests/test_logic.py`** and confirm GREEN.
- [ ] **Step 5: Commit** with message `feat: add attendance summary to panel model`.

### Task 2: One-time panel shell and local state

**Files:**
- Replace: `custom_components/mojv/frontend/school-panel.js`
- Create: `tests/test_school_panel_v2.py`

**Interfaces:**
- `MojVSchoolPanel._buildShell()` creates static DOM exactly once.
- `MojVSchoolPanel._applyPayload(payload)` stores data and selects a valid active student.
- `MojVSchoolPanel._renderNavigation()` renders student and view controls only when state changes.
- `MojVSchoolPanel._renderActiveView()` updates only `#view-content`.
- `MojVSchoolPanel._tickClock()` updates time/progress UI without calling `_refresh()`.

- [ ] **Step 1: Write failing structural tests** asserting the source contains `_buildShell`, `_applyPayload`, `_renderActiveView`, a `10000` ms ticker, and does not contain the old `setInterval(() => this._refresh(), 30000)` full-refresh timer.
- [ ] **Step 2: Run `pytest -q tests/test_school_panel_v2.py`** and confirm RED.
- [ ] **Step 3: Implement the one-time shell**, topbar, student selector, view selector, loading/error states, and manual refresh button. Register event listeners only inside `_buildShell()`.
- [ ] **Step 4: Implement `_refresh()`** so only explicit refresh/initialization calls `mojv/panel`; switching student/view must use in-memory payload.
- [ ] **Step 5: Run `node --check custom_components/mojv/frontend/school-panel.js` and `pytest -q tests/test_school_panel_v2.py`** and confirm GREEN.
- [ ] **Step 6: Commit** with message `refactor: build School panel shell once`.

### Task 3: Today, Schedule and Attendance views

**Files:**
- Modify: `custom_components/mojv/frontend/school-panel.js`
- Modify: `tests/test_school_panel_v2.py`

**Interfaces:**
- `_renderToday(student)` renders current/next lesson cards and day overview.
- `_renderSchedule(student)` filters `student.week` using `_weekOffset` and renders Monday-Friday only.
- `_renderAttendance(student)` renders summary tiles and attendance entries from lessons.
- `_changeWeek(delta)` clamps offset to `[-1, 1]` and rerenders locally.
- `_positionTimeLine()` updates current-time marker with `requestAnimationFrame`.

- [ ] **Step 1: Extend failing tests** for local `_weekOffset`, `_changeWeek`, `requestAnimationFrame`, and `attendance_summary` usage.
- [ ] **Step 2: Run the focused tests and confirm RED.**
- [ ] **Step 3: Implement Today view** with current lesson, next lesson, minutes remaining, teacher, room, lesson number, attendance and alerts.
- [ ] **Step 4: Implement Schedule view** as a 5-day time-slot grid with previous/current/next week buttons, current-day/current-lesson states, cancellation/replacement badges and horizontal scrolling contained inside schedule only.
- [ ] **Step 5: Implement local current-time line** for offset `0`; update position every 10 seconds without data requests.
- [ ] **Step 6: Implement Attendance view** with totals and a chronological list of non-empty attendance records.
- [ ] **Step 7: Run `node --check` and focused pytest tests** and confirm GREEN.
- [ ] **Step 8: Commit** with message `feat: add fast Today Schedule and Attendance views`.

### Task 4: Responsive styling and release packaging

**Files:**
- Modify: `custom_components/mojv/frontend/school-panel.js`
- Modify: `custom_components/mojv/manifest.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_version_logging.py` only if release assertions require it.

**Interfaces:**
- Integration release version becomes `0.7.0` because this is a major panel UX change while remaining pre-1.0.

- [ ] **Step 1: Add responsive CSS** using Home Assistant theme variables, restrained mojV accent styling, 44px minimum touch targets, and mobile cards that do not overflow the viewport.
- [ ] **Step 2: Verify only the schedule viewport can scroll horizontally on mobile.**
- [ ] **Step 3: Bump manifest to `0.7.0`, README version references to `HACS 0.7.0`, and add `0.7.0` CHANGELOG entry describing the panel-v2 performance/UX changes.
- [ ] **Step 4: Run full local/static validation:** `python -m compileall -q custom_components/mojv`, `node --check custom_components/mojv/frontend/school-panel.js`, `pytest -q tests`.
- [ ] **Step 5: Push branch CI and require Code quality, Hassfest and HACS to pass.**
- [ ] **Step 6: Fast-forward the exact verified commit to `main`, verify GitHub release `v0.7.0`, and re-check `manifest.json` on `main`.

## Self-review

- Spec coverage: one-time DOM, local ticker, local week switching, Today/Schedule/Attendance, mobile containment and theme-aware styling are covered.
- Stage-2 live modules are intentionally excluded from this plan and will receive a separate plan after Panel v2 is green.
- No new dependency or copied GPL implementation is required.
- All interfaces referenced by later tasks are defined above.
