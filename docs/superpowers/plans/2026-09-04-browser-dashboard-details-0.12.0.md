# mojV 0.12.0 Browser Dashboard and Detail UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove duplicate students from the School Hub payload, expose complete safe schoolwork/information content through click-through details, add clear lesson-state styling, and provide an authenticated full-screen browser dashboard inside Home Assistant.

**Architecture:** Keep `panel.py`/`panel_base.py` as the safe aggregation boundary and deduplicate there before WebSocket serialization leaves the backend. Reuse the existing `mojv/panel` payload and `mojv-school-panel` rendering stack; add focused frontend patches for detail overlays, lesson state semantics and a second Home Assistant custom-panel route rather than forking the School Hub.

**Tech Stack:** Python 3.13, Home Assistant custom integration APIs, `panel_custom`, Home Assistant WebSocket API, vanilla JavaScript custom elements, pytest, GitHub Actions, Hassfest, HACS validation.

**Spec:** `docs/superpowers/specs/2026-09-04-browser-dashboard-details-0.12.0-design.md`

## Global Constraints

- Production data remains LIVE-only; no fabricated portal data in the live path.
- Support 1..N students; never hardcode a child count.
- Preserve HTTP-first authentication with automatic Chromium-helper fallback.
- Dashboard remains inside Home Assistant authentication; do not create an unauthenticated static dashboard page or a second credential store.
- Never send credentials, cookies, session/mailbox/routing keys, parent contact data, full sensitive student profile or raw unsanitized portal HTML to the frontend.
- `apiGlobalKey`, `globalKeySkrzynka`, `mailbox_key` and equivalent routing/session fields remain forbidden.
- Do not copy GPL implementation code; only independently reimplement behavior/endpoints.
- Maintain the reserved-name CI rule already present in the repository.
- Core release target is `0.12.0`; helper version changes only if browser-fallback payload code must change.

---

## File Structure

- `custom_components/mojv/panel_base.py` — WebSocket aggregation, candidate collection and deterministic student deduplication.
- `custom_components/mojv/panel.py` — expanded safe serialization including new safe detail fields and second panel registration constants/exports where needed.
- `custom_components/mojv/models.py` — normalized long-form `ImportantToday.description` field only; schoolwork already has `description`.
- `custom_components/mojv/parsers/extras.py` — whitelist and normalize safe long-form important-today text.
- `custom_components/mojv/frontend/school-panel-details.js` — reusable preview/detail overlay behavior and accessible click/keyboard interactions.
- `custom_components/mojv/frontend/school-panel-lesson-states.js` — lesson temporal-state classifier, badges and CSS hooks.
- `custom_components/mojv/frontend/school-dashboard.js` — full-screen browser panel wrapper that reuses `mojv-school-panel`.
- `custom_components/mojv/frontend/school-panel-hub.js` — imports focused patches and exposes an "Otwórz dashboard" action without duplicating render logic.
- `custom_components/mojv/__init__.py` — no auth changes; setup/unload continues to register/unregister panel surfaces through panel helpers.
- `.github/workflows/validate.yml` — `node --check` every new executable JS module.
- `tests/test_panel_student_dedup.py` — backend dedup behavior.
- `tests/test_detail_payload_contract.py` — safe long-form payload contract.
- `tests/test_detail_frontend_contract.py` — click-through overlay/preview/accessibility contract.
- `tests/test_lesson_state_frontend_contract.py` — temporal-state semantics and text markers.
- `tests/test_browser_dashboard_contract.py` — authenticated second panel route and shared WebSocket contract.

---

### Task 1: Deduplicate students at the WebSocket aggregation boundary

**Files:**
- Modify: `custom_components/mojv/panel_base.py`
- Test: `tests/test_panel_student_dedup.py`

**Interfaces:**
- Produces: `_select_student_rows(candidates: list[tuple[datetime, int, dict[str, Any]]]) -> list[dict[str, Any]]`
- Candidate tuple fields: `(coordinator_updated_at, insertion_index, serialized_student_row)`.
- Winner rule: newer timestamp wins; equal timestamps keep the lower insertion index; output order follows the first occurrence of each student ID.

- [ ] **Step 1: Write failing pure-function tests**

```python
from datetime import datetime, timezone

from custom_components.mojv.panel_base import _select_student_rows


def _ts(hour: int) -> datetime:
    return datetime(2026, 9, 4, hour, tzinfo=timezone.utc)


def test_select_student_rows_keeps_one_row_per_student_and_newest_snapshot():
    rows = _select_student_rows([
        (_ts(8), 0, {"id": "s1", "name": "Martyna", "class": "8A", "marker": "old"}),
        (_ts(8), 1, {"id": "s2", "name": "Lucjan", "class": "5C", "marker": "only"}),
        (_ts(9), 2, {"id": "s1", "name": "Martyna", "class": "8A", "marker": "new"}),
    ])
    assert [row["id"] for row in rows] == ["s1", "s2"]
    assert rows[0]["marker"] == "new"


def test_select_student_rows_equal_timestamp_is_stable():
    stamp = _ts(8)
    rows = _select_student_rows([
        (stamp, 0, {"id": "s1", "marker": "first"}),
        (stamp, 1, {"id": "s1", "marker": "second"}),
    ])
    assert rows == [{"id": "s1", "marker": "first"}]
```

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_panel_student_dedup.py`
Expected: import/attribute failure because `_select_student_rows` does not exist.

- [ ] **Step 3: Implement the minimal selector and use it in `websocket_panel_data()`**

```python
def _select_student_rows(
    candidates: list[tuple[datetime, int, dict[str, Any]]],
) -> list[dict[str, Any]]:
    first_order: dict[str, int] = {}
    winners: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for stamp, index, row in candidates:
        student_id = str(row.get("id") or "")
        if not student_id:
            continue
        first_order.setdefault(student_id, index)
        current = winners.get(student_id)
        if current is None or stamp > current[0]:
            winners[student_id] = (stamp, index, row)
    return [
        winners[student_id][2]
        for student_id in sorted(first_order, key=first_order.get)
    ]
```

Change `websocket_panel_data()` from direct `students.extend(...)` to candidate collection using each coordinator's `data.updated_at`, then call `_select_student_rows(candidates)` exactly once before `send_result()`.

- [ ] **Step 4: Run GREEN and regression tests**

Run: `pytest -q tests/test_panel_student_dedup.py tests/test_school_hub_payload.py tests/test_expanded_panel_contract.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `fix: deduplicate School Hub students`

---

### Task 2: Preserve safe long-form information content in normalized models

**Files:**
- Modify: `custom_components/mojv/models.py`
- Modify: `custom_components/mojv/parsers/extras.py`
- Modify: `custom_components/mojv/panel.py`
- Test: `tests/test_detail_payload_contract.py`

**Interfaces:**
- Extend `ImportantToday` with `description: str = ""`.
- `parse_important_today()` maps only safe text from `opis`, `tresc`, `szczegoly` or `podtytul` into `description` using the existing text normalization path.
- Existing `SchoolWork.description` remains the canonical full content for homework/tests/Terminarz.

- [ ] **Step 1: Write RED tests for normalization and serialization**

```python
from custom_components.mojv.parsers.extras import parse_important_today


def test_important_today_preserves_safe_long_description():
    rows = parse_important_today({
        "wazneDzisiaj": [{
            "nazwa": "Wycieczka",
            "przedmiot": "Historia",
            "nazwaZdarzenia": "Informacja",
            "opis": "Zbiórka o 7:45 przy wejściu głównym.",
            "globalKeySkrzynka": "must-not-leak",
        }]
    })
    assert rows[0].description == "Zbiórka o 7:45 przy wejściu głównym."
    assert "must-not-leak" not in repr(rows[0])
```

Add a payload contract asserting `_student_dict(...)` serializes `important_today[].description` and `schoolwork[].description`, while forbidden key names are absent from serialized JSON.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_detail_payload_contract.py`
Expected: FAIL because `ImportantToday` has no `description` and panel serialization omits it.

- [ ] **Step 3: Implement minimal model/parser/payload extension**

```python
@dataclass(frozen=True, slots=True)
class ImportantToday:
    subject: str = ""
    kind: str = ""
    title: str = ""
    description: str = ""
```

In `parse_important_today()` set:

```python
description=text(
    row.get("opis")
    or row.get("tresc")
    or row.get("szczegoly")
    or row.get("podtytul")
),
```

In `panel.py`, serialize only `subject`, `kind`, `title`, `description` for each important-today row.

- [ ] **Step 4: Run GREEN and security regressions**

Run: `pytest -q tests/test_detail_payload_contract.py tests/test_expanded_school_parsers.py tests/test_expanded_panel_contract.py tests/test_helper_protocol.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: expose safe school detail text`

---

### Task 3: Add reusable click-through detail overlay and Terminarz previews

**Files:**
- Create: `custom_components/mojv/frontend/school-panel-details.js`
- Modify: `custom_components/mojv/frontend/school-panel-hub.js`
- Test: `tests/test_detail_frontend_contract.py`

**Interfaces:**
- Adds prototype methods `_detailPreview(value, limit = 120)`, `_openMojvDetail(detail)`, `_closeMojvDetail()`.
- Replaces/extends `_renderSchoolwork(student)` so each row is a `<button type="button" class="mojv-detail-trigger" data-mojv-detail-kind="schoolwork" data-mojv-detail-id="...">` with title, kind, subject/date and escaped preview.
- Important-today cards with non-empty descriptions become detail triggers.
- Overlay is rendered inside the existing shadow root and never uses raw `innerHTML` from remote content; all dynamic values pass through `this._e(...)` and preserved newlines are rendered as escaped text paragraphs.

- [ ] **Step 1: Write RED source-contract tests**

```python
def test_detail_module_exposes_accessible_overlay_contract():
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "_detailPreview" in source
    assert "_openMojvDetail" in source
    assert 'role="dialog"' in source
    assert 'aria-modal="true"' in source
    assert 'event.key === "Escape"' in source
    assert "focus()" in source


def test_schoolwork_rows_are_clickable_and_show_description_preview():
    source = DETAILS_JS.read_text(encoding="utf-8")
    assert "mojv-detail-trigger" in source
    assert "item.description" in source
    assert "_detailPreview(item.description" in source
    assert "innerHTML = detail.body" not in source
```

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_detail_frontend_contract.py`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement preview helper and overlay**

Use this behavior:

```javascript
proto._detailPreview = function (value, limit = 120) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  return text.length <= limit ? text : `${text.slice(0, limit - 1).trimEnd()}…`;
};
```

`_openMojvDetail()` must store `this.__mojvDetailReturnFocus = this.shadowRoot.activeElement`, create one overlay node with escaped title/meta/body, focus the close button, and register no global data source. `_closeMojvDetail()` removes the overlay and restores focus when possible.

Patch `_renderSchoolwork()` and the expanded `important_today` dashboard block so compact rows show escaped previews and clicks resolve the corresponding item from the active student's already-loaded payload.

- [ ] **Step 4: Verify GREEN and JS syntax**

Run: `pytest -q tests/test_detail_frontend_contract.py tests/test_school_hub_frontend.py`
Run: `node --check custom_components/mojv/frontend/school-panel-details.js`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add school item detail views`

---

### Task 4: Add explicit temporal lesson-state semantics to day/week plan

**Files:**
- Create: `custom_components/mojv/frontend/school-panel-lesson-states.js`
- Modify: `custom_components/mojv/frontend/school-panel-hub.js`
- Test: `tests/test_lesson_state_frontend_contract.py`

**Interfaces:**
- Adds `_mojvLessonState(lesson, now = new Date()) -> "cancelled" | "current" | "completed" | "upcoming"`.
- Precedence: cancelled > current > completed > upcoming.
- Adds textual marker helper returning `Odwołana`, `Teraz`, `Odbyta`, or empty string.
- Replacement and change badges remain additive.

- [ ] **Step 1: Write RED contract tests**

```python
def test_lesson_state_module_has_all_states_and_accessible_labels():
    source = LESSON_STATES_JS.read_text(encoding="utf-8")
    for token in ("cancelled", "current", "completed", "upcoming"):
        assert token in source
    assert "Teraz" in source
    assert "Odbyta" in source
    assert "Odwołana" in source
    assert "replacement" in source
```

Also assert CSS selectors `.lesson-state-current`, `.lesson-state-completed`, `.lesson-state-upcoming`, `.lesson-state-cancelled` exist and no state is represented only by a color declaration without a text badge path.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_lesson_state_frontend_contract.py`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement classifier and render patch**

```javascript
proto._mojvLessonState = function (lesson, now = new Date()) {
  if (lesson?.cancelled) return "cancelled";
  const start = new Date(lesson.start);
  const end = new Date(lesson.end);
  if (start <= now && now < end) return "current";
  if (end <= now) return "completed";
  return "upcoming";
};
```

Patch day and weekly plan row rendering at their existing render methods, adding `lesson-state-${state}` plus a visible marker. Completed rows must be subdued, current rows emphasized, upcoming neutral and cancelled warning/error. Keep `replacement` badges independent.

- [ ] **Step 4: Verify GREEN and syntax**

Run: `pytest -q tests/test_lesson_state_frontend_contract.py tests/test_school_hub_frontend.py`
Run: `node --check custom_components/mojv/frontend/school-panel-lesson-states.js`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: distinguish lesson states in plan`

---

### Task 5: Register an authenticated full-screen browser dashboard route

**Files:**
- Create: `custom_components/mojv/frontend/school-dashboard.js`
- Modify: `custom_components/mojv/panel_base.py`
- Modify: `custom_components/mojv/panel.py`
- Modify: `custom_components/mojv/frontend/school-panel-hub.js`
- Test: `tests/test_browser_dashboard_contract.py`

**Interfaces:**
- Dashboard URL path: `mojv-dashboard`.
- Dashboard custom element: `mojv-school-dashboard`.
- Dashboard module: `/mojv-static/school-dashboard.js`.
- Dashboard wrapper reuses `<mojv-school-panel>` and forwards `hass`, `narrow` and panel config; it does not call the portal directly.
- The inner panel continues to obtain data only through `mojv/panel`.

- [ ] **Step 1: Write RED backend/frontend route tests**

```python
def test_browser_dashboard_is_second_authenticated_custom_panel():
    source = PANEL_SOURCE.read_text(encoding="utf-8")
    assert 'DASHBOARD_URL_PATH = "mojv-dashboard"' in source
    assert 'DASHBOARD_ELEMENT = "mojv-school-dashboard"' in source
    assert 'module_url=f"{PANEL_STATIC_URL}/school-dashboard.js"' in source
    assert "async_register_panel" in source


def test_dashboard_reuses_school_panel_and_websocket_payload():
    source = DASHBOARD_JS.read_text(encoding="utf-8")
    assert 'import "./school-panel-hub.js"' in source
    assert 'document.createElement("mojv-school-panel")' in source
    assert "mojv/panel" not in source  # the reused inner panel owns data fetching
```

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_browser_dashboard_contract.py`
Expected: FAIL because constants/module/registration do not exist.

- [ ] **Step 3: Implement second Home Assistant custom panel registration**

Register `school` and `mojv-dashboard` through `panel_custom.async_register_panel(...)`. The second panel uses `module_url=f"{PANEL_STATIC_URL}/school-dashboard.js"`, `frontend_url_path=DASHBOARD_URL_PATH`, `webcomponent_name=DASHBOARD_ELEMENT`, `require_admin=False`, and remains covered by Home Assistant frontend authentication. Do not serve a standalone HTML page.

`school-dashboard.js` must create one `<mojv-school-panel>`, forward `hass`, `narrow=false`, and `panel`, and size it to `100%` width/min-height. Add an `Otwórz dashboard` link/button in the existing School Hub top action area pointing to `/mojv-dashboard`.

- [ ] **Step 4: Verify GREEN and Home Assistant registration contracts**

Run: `pytest -q tests/test_browser_dashboard_contract.py tests/test_panel_live_data_contract.py tests/test_school_hub_frontend.py`
Run: `node --check custom_components/mojv/frontend/school-dashboard.js`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add authenticated browser school dashboard`

---

### Task 6: CI coverage, release metadata and full verification

**Files:**
- Modify: `.github/workflows/validate.yml`
- Modify: `custom_components/mojv/manifest.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Test: existing version/repository split contracts

**Interfaces:**
- `manifest.json` version becomes `0.12.0` only after functional tasks are GREEN.
- `validate.yml` checks syntax for `school-panel-details.js`, `school-panel-lesson-states.js`, `school-dashboard.js` in addition to existing frontend modules.
- Helper version remains `0.1.9` unless Task 2 reveals browser-fallback parity requires helper runtime changes.

- [ ] **Step 1: Add RED CI source-contract assertions if current tests do not cover new JS checks**

Add assertions to the existing frontend CI contract test that every executable module appears in `node --check` commands.

- [ ] **Step 2: Run RED and then update workflow**

Run the focused CI-contract test; verify it fails on missing new checks. Add exactly these commands to the JavaScript validation step:

```bash
node --check custom_components/mojv/frontend/school-panel-details.js
node --check custom_components/mojv/frontend/school-panel-lesson-states.js
node --check custom_components/mojv/frontend/school-dashboard.js
```

- [ ] **Step 3: Run complete branch verification before version bump**

Run/observe GitHub Validate for the branch. Required GREEN: Python compile, all pytest tests, all frontend `node --check`, release consistency at the pre-release version, reserved naming, Hassfest and HACS.

- [ ] **Step 4: Update release metadata atomically**

Set manifest to `0.12.0`; prepend `## [0.12.0] - 2026-09-04` changelog entry covering deduplication, detail views, lesson state colors/labels and authenticated browser dashboard; update README HACS version and user-facing feature list. Do not claim live-account verification.

- [ ] **Step 5: Run final branch CI, PR CI, merge and main CI**

Required evidence before completion claim:

- final branch Validate = success,
- PR Validate = success,
- squash merge only with unchanged expected head SHA,
- final `main` Validate = success,
- Release workflow = success,
- tag `v0.12.0` points to final `main` commit,
- public GitHub Release `mojV 0.12.0` exists and is not draft/prerelease.

- [ ] **Step 6: Commit release metadata**

Commit message: `release: prepare mojV 0.12.0`
