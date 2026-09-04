# School Hub Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rozbudować panel boczny mojV do pełnego School Hub z Pulpitem, Aktywnością i historią Powiadomień.

**Architecture:** Backend rozszerza istniejący WebSocket `mojv/panel` o agregaty i bezpieczną historię. Frontend dodaje trzeci wrapper `school-panel-hub.js`, który importuje `school-panel-live.js` i nie narusza bazowego `school-panel.js`.

**Tech Stack:** Home Assistant WebSocket panel API, vanilla Web Components/JavaScript, pytest contract tests, Node `--check`.

**Spec:** `docs/superpowers/specs/2026-09-04-school-hub-notifications-design.md`

## Global Constraints

- Wersja docelowa `0.10.0`.
- Moduły dynamiczne tylko dla danych LIVE.
- Brak nowego pollera lub logowania z frontendu.
- Frontend ma działać responsywnie desktop/tablet/mobile.
- `school-panel.js` pozostaje bazą; 0.10.0 rozszerza przez `school-panel-hub.js`.
- Panel i historia nie mogą zawierać sekretów/routing IDs.

---

### Task 1: Panel payload + aktywność

**Files:**
- Modify: `custom_components/mojv/panel.py`
- Test: `tests/test_school_hub_payload.py`

**Interfaces:**
- Consumes notification history z managerów `DATA_NOTIFIERS`.
- Produces per-student fields `dashboard`, `activity` and top-level/per-student `notifications` as appropriate.

- [ ] **Step 1: Write failing tests**

Wymusić agregaty: unread messages, latest grade, next schoolwork, next meeting, latest remark/praise, global attendance percentage, latest achievement, oraz timeline posortowany newest-first z typami `grade`, `remark`, `praise`, `message`, `schoolwork`, `meeting`, `achievement`, `attendance`.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_school_hub_payload.py`
Expected: FAIL because new fields are absent.

- [ ] **Step 3: Implement minimal serialization helpers**

Agregaty bazują tylko na `StudentSnapshot` i historii notyfikacji. Nie zwracać surowych routing IDs.

- [ ] **Step 4: GREEN**

Run: `pytest -q tests/test_school_hub_payload.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: expose School Hub panel payload"`

### Task 2: Frontend wrapper School Hub

**Files:**
- Create: `custom_components/mojv/frontend/school-panel-hub.js`
- Modify: `custom_components/mojv/panel.py`
- Modify: `.github/workflows/validate.yml`
- Test: `tests/test_school_hub_frontend.py`

**Interfaces:**
- Imports `./school-panel-live.js`.
- Adds views `dashboard`, `activity`, `notifications` and badge-aware navigation.

- [ ] **Step 1: Write failing frontend contract tests**

Wymusić import wrappera, rejestrację module URL w `panel.py`, widoki Pulpit/Aktywność/Powiadomienia, badge unread/upcoming, brak bezpośrednich `callWS` poza istniejącym refresh flow oraz obecność responsive CSS.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_school_hub_frontend.py`
Expected: FAIL because hub wrapper does not exist.

- [ ] **Step 3: Implement wrapper**

`Pulpit` pokazuje karty agregatów; `Aktywność` łączy typy chronologicznie; `Powiadomienia` pokazują historię z priorytetem i czasem. Na mobile siatka przechodzi do jednej kolumny.

- [ ] **Step 4: Validate JavaScript**

Run:
`node --check custom_components/mojv/frontend/school-panel.js`
`node --check custom_components/mojv/frontend/school-panel-live.js`
`node --check custom_components/mojv/frontend/school-panel-hub.js`
Expected: all exit 0.

- [ ] **Step 5: GREEN**

Run: `pytest -q tests/test_school_hub_frontend.py tests/test_school_hub_payload.py`
Expected: PASS.

- [ ] **Step 6: Commit**

`git commit -m "feat: add School Hub sidebar views"`

### Task 3: Release 0.10.0

**Files:**
- Modify: `custom_components/mojv/manifest.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Test: existing release consistency tests.

- [ ] **Step 1: Update docs/version**

Manifest `0.10.0`; README opisuje School Hub, Notification Engine v2, dostępne typy alertów, Options Flow i brak historycznej lawiny; CHANGELOG dodaje `## [0.10.0] - 2026-09-04`.

- [ ] **Step 2: Full tests**

Run: `pytest -q tests`
Expected: all PASS.

- [ ] **Step 3: Full JS checks**

Run all three `node --check` commands.
Expected: all PASS.

- [ ] **Step 4: CI**

Push branch and require Code quality, Hassfest and HACS GREEN.

- [ ] **Step 5: PR/release**

Create PR to `main`; merge only after PR CI GREEN. Then require main Validate GREEN and Release workflow publishing `v0.10.0`.