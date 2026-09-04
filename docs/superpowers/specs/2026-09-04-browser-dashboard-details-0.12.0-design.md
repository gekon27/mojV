# mojV 0.12.0 — Browser dashboard, detail views and lesson-state UX

Date: 2026-09-04
Status: approved in chat, awaiting written-spec review

## Goal

Release `mojV 0.12.0` will fix duplicate students in School Hub and extend the existing authenticated Home Assistant UI with a browser-focused dashboard, richer click-through detail views and clearer visual lesson states.

The change must preserve the current security boundary, HTTP-first authentication, Chromium helper fallback, support for 1..N children and LIVE-only production data.

## Scope

### 1. Deduplicate students in the panel payload

Current root cause: `websocket_panel_data()` iterates every mojV config entry and appends every coordinator student with `students.extend(...)`. If the same account/student is present in more than one active config entry, the School Hub receives the same student more than once. The screenshot supplied by the user shows the exact symptom: the same two students appear twice in the selector.

The fix belongs in the backend payload layer, not only in JavaScript.

Required behavior:

- deduplicate by stable `student_id` before sending `mojv/panel`,
- if the same student is present in more than one coordinator, keep the row from the coordinator with the newest `updated_at`,
- preserve deterministic ordering,
- never merge fields from two snapshots blindly,
- notification history attached to the winning snapshot must remain consistent with that snapshot,
- frontend code must be able to assume one row per student ID.

This also protects the future browser dashboard and any other client using `mojv/panel` from duplicate rows.

### 2. Authenticated browser dashboard

Add a browser-oriented full-screen school dashboard that reuses the same backend payload and frontend rendering primitives as School Hub.

Security model:

- dashboard stays inside Home Assistant authentication,
- no separate username/password/token store,
- no public static API endpoint,
- no CORS relaxation,
- no direct portal credentials in the browser,
- no session/mailbox/routing keys in payloads.

The dashboard should be usable on desktop, tablet and kiosk-style browser displays. It should expose the same student selector and core data, but optimize the layout for a large browser viewport rather than the sidebar panel container.

Preferred architecture:

- reuse `mojv/panel` WebSocket data,
- reuse shared view/rendering functions instead of duplicating data logic,
- provide a dedicated authenticated Home Assistant route/view for the dashboard,
- keep School Hub and dashboard visually consistent,
- add a clear action from School Hub to open the browser dashboard.

The exact Home Assistant registration API used for the second route must be the supported API available in the target HA version; no unauthenticated `dashboard.html` under the static path.

### 3. Rich click-through details

Lists should stay compact, but complete LIVE content must be accessible by click/tap when the backend already has it.

Affected areas:

- Terminarz,
- zadania domowe,
- sprawdziany / kartkówki / other schoolwork kinds,
- `Ważne dzisiaj`,
- information/alert cards where a longer body exists,
- messages remain unchanged unless they already use the same safe detail component.

Interaction model:

- list/card shows concise summary,
- click or keyboard activation opens a drawer/modal detail view,
- Esc closes it,
- click outside closes it where appropriate,
- focus returns to the triggering item,
- mobile uses a full-width/bottom-sheet style presentation,
- desktop uses a centered modal or right-side drawer.

Displayed fields should include only fields actually available LIVE and safe to expose, for example:

- title,
- kind/type,
- subject,
- due/start date and time,
- teacher/author if available,
- full description/body/content,
- safe online URL if already present and validated,
- category/period/status when meaningful.

No invented text. If the source provides no body, the UI should explicitly show that no additional description is available.

### 4. Terminarz must show content, not only headings

The current compact list is insufficient when an item has a description/body.

Required behavior:

- list row shows title plus a short plain-text preview of the description when available,
- clicking opens the full detail view,
- preview must be safely escaped and length-limited,
- full detail keeps original paragraph breaks where possible,
- rich/HTML portal content must be sanitized or converted to safe text; raw remote HTML is never injected into the DOM.

The same rule applies to homework/test entries.

### 5. Lesson state colors in Plan

Plan views must make temporal state obvious without requiring the user to compare clock times manually.

Required visual states:

- `current`: clearly emphasized; use the existing mojV accent treatment and a visible `Teraz` marker,
- `completed`: visually subdued/greyed compared with upcoming lessons,
- `upcoming`: normal neutral appearance,
- `cancelled`: warning/error treatment with an explicit `Odwołana` label,
- `replacement`: visible badge/indicator,
- room/time/teacher change: visible change badge when the normalized lesson model exposes such information.

State precedence:

1. cancelled,
2. current,
3. completed,
4. upcoming.

Replacement/change badges are additive and do not replace temporal state.

Apply the same semantics to:

- day plan,
- weekly plan,
- browser dashboard lesson list.

Do not rely on color alone; every exceptional state requires text/icon semantics for accessibility.

### 6. Student selector UX

After backend deduplication:

- exactly one chip per student ID,
- selector remains visible for 2+ children,
- no selector row for a single child,
- active student is preserved across refresh if that student still exists,
- dashboard and School Hub use the same selection semantics.

## Architecture

### Backend

Keep `panel.py` / `panel_base.py` as the safe aggregation boundary.

Add a small pure helper for student-row selection/deduplication so it can be unit tested without Home Assistant WebSocket plumbing. The helper receives candidate rows with source update timestamps and returns one deterministic row per `student_id`.

Do not alter authentication/session protocols for this release.

Schoolwork / important-information payloads may be extended only with fields already present in normalized models or independently parsed from LIVE responses. If source parsers currently discard a safe long-form description, add that field to the normalized model/parser rather than passing raw endpoint dictionaries into the frontend.

### Frontend

Avoid another monolithic file. Keep the existing base/wrapper layering and extract reusable UI primitives where useful:

- detail overlay/drawer renderer,
- plain-text preview helper,
- lesson-state classifier/classes,
- shared dashboard/panel view rendering.

The browser dashboard should reuse the same custom element or shared renderer rather than fork the whole School Hub.

## Data and security boundary

Never send or render:

- `apiGlobalKey`,
- `globalKeySkrzynka`,
- mailbox/session/routing keys,
- credentials,
- cookies,
- parent contact data,
- full sensitive student profile,
- raw unsanitized remote HTML.

All new payload fields must be whitelisted explicitly.

## Error handling

- one bad detail field must not prevent the rest of a student snapshot from rendering,
- missing long-form content results in a neutral `Brak dodatkowej treści` message,
- malformed URLs are rendered as text, not active links,
- duplicate source rows do not cause duplicated UI,
- dashboard failure state mirrors School Hub and offers manual refresh.

## Testing strategy

Use RED→GREEN.

### Backend tests

1. same `student_id` from two coordinators results in one payload row,
2. newer coordinator snapshot wins,
3. different students are preserved,
4. stable ordering is deterministic,
5. no forbidden secrets appear in expanded detail payload,
6. full safe schoolwork/important-information description survives normalization when present.

### Frontend/source-contract tests

1. detail overlay can be opened from Terminarz/homework/test rows,
2. full description is present in the detail renderer,
3. compact preview is length-limited and escaped,
4. raw HTML is never inserted unsanitized,
5. `current/completed/upcoming/cancelled` lesson classes exist,
6. `Teraz` and `Odwołana` text markers exist,
7. replacement/change badges remain additive,
8. dashboard route/component exists and uses `mojv/panel`,
9. student selector does not duplicate identical IDs.

### CI

Maintain:

- Python compile,
- all existing pytest tests,
- new pytest tests,
- `node --check` for every executable frontend module,
- reserved naming check,
- release consistency check,
- Hassfest,
- HACS.

## Acceptance criteria

`0.12.0` is releasable only when all of the following are true:

1. The screenshot scenario with two duplicated children renders each child once.
2. Current lesson, completed lessons and upcoming lessons are visually distinct in Plan.
3. Cancelled/replacement lessons remain unambiguous and accessible without relying on color alone.
4. Terminarz entries with a description show a preview and full content after click.
5. Homework/test entries show full available LIVE content after click.
6. `Ważne dzisiaj` / information entries show full available content after click when such content exists.
7. Browser dashboard is accessible only through authenticated Home Assistant and uses the same safe `mojv/panel` payload.
8. No new sensitive portal/session/profile fields cross the backend/frontend boundary.
9. Existing School Hub views and Notification Engine v2 continue to work.
10. Final branch CI, PR CI, main CI and release workflow are GREEN before completion is claimed.

## Release target

- Core: `mojV 0.12.0`
- Helper: bump only if LIVE browser-fallback payload/parser changes are actually required for the new long-form fields. Do not bump helper merely for frontend/deduplication changes.
