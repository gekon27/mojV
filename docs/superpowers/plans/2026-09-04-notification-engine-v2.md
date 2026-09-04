# Notification Engine v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rozszerzyć mojV o deduplikowany, konfigurowalny Notification Engine v2 z historią i opcjonalnym push.

**Architecture:** Czyste reguły wykrywania zmian trafiają do `notification_rules.py`, trwała ograniczona historia do `notification_history.py`, a `notifications.py` odpowiada tylko za orkiestrację i kanały. Options Flow zapisuje ustawienia bez zmiany danych logowania.

**Tech Stack:** Python 3.13, Home Assistant ConfigEntry/OptionsFlow, Store, persistent_notification, event bus, pytest.

**Spec:** `docs/superpowers/specs/2026-09-04-school-hub-notifications-design.md`

## Global Constraints

- Wersja docelowa `0.10.0`.
- LIVE only w produkcji; pierwsza synchronizacja LIVE jest baseline.
- Obsługa 1..N dzieci.
- HTTP first → automatyczny helper fallback bez zmian.
- Maksymalnie 200 rekordów historii na config entry.
- Żaden publiczny payload nie zawiera sekretów/routing IDs.
- Push jest opcjonalny; persistent notification + event bus pozostają podstawą.

---

### Task 1: Czysty model alertu i reguły różnicowe

**Files:**
- Create: `custom_components/mojv/notification_rules.py`
- Test: `tests/test_notification_rules.py`

**Interfaces:**
- Produces: `NotificationCandidate`, `build_change_candidates(previous, current, now)`, `build_time_candidates(snapshot, now, options)`.

- [ ] **Step 1: Write failing tests**

Testy mają wymusić: new grade, changed final/proposed grade, remark vs praise, new message, absence/late, cancelled/replacement/room-time change, new schoolwork, new meeting, new achievement, end-of-lesson reminder, due schoolwork/meeting reminder oraz stabilny `event_id`.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_notification_rules.py`
Expected: FAIL because `notification_rules` does not exist.

- [ ] **Step 3: Minimal implementation**

`NotificationCandidate` jest immutable dataclass z polami `event_id`, `student_id`, `student_name`, `kind`, `priority`, `title`, `message`, `created_at`, `data`.

Event ID budować deterministycznie z typu, ucznia i stabilnej sygnatury domenowej; nie używać sekretów.

- [ ] **Step 4: GREEN**

Run: `pytest -q tests/test_notification_rules.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add notification v2 rules"`

### Task 2: Trwała historia

**Files:**
- Create: `custom_components/mojv/notification_history.py`
- Test: `tests/test_notification_history.py`

**Interfaces:**
- Consumes: `NotificationCandidate`.
- Produces: `NotificationHistory.async_load()`, `async_append(candidate)`, `async_save()`, `as_panel_rows()`.

- [ ] **Step 1: Write failing tests**

Wymusić limit 200, newest-first, deduplikację po `event_id`, bezpieczną serializację i zachowanie po reload Store.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_notification_history.py`
Expected: FAIL because module/class does not exist.

- [ ] **Step 3: Implement minimal history**

Store key pozostaje związany z config entry. Serializowane rekordy zawierają tylko publiczne pola specyfikacji.

- [ ] **Step 4: GREEN**

Run: `pytest -q tests/test_notification_history.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: persist bounded notification history"`

### Task 3: Options Flow

**Files:**
- Modify: `custom_components/mojv/config_flow.py`
- Modify: `custom_components/mojv/const.py`
- Test: `tests/test_notification_options.py`

**Interfaces:**
- Produces options keys for enabled kinds, notify targets, lesson-end minutes, schoolwork lead, meeting lead, quiet hours.

- [ ] **Step 1: Write failing contract tests**

Wymusić `async_get_options_flow`, domyślne wartości 5 min / 24 h / 24 h, brak wymaganych targetów push oraz walidację godzin ciszy.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_notification_options.py`
Expected: FAIL because options flow is missing.

- [ ] **Step 3: Implement minimal OptionsFlow**

Ustawienia zapisują się w `ConfigEntry.options`, nie w `entry.data`. Lista notify targets może być pusta.

- [ ] **Step 4: GREEN**

Run: `pytest -q tests/test_notification_options.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add notification options flow"`

### Task 4: Orkiestracja i kanały

**Files:**
- Modify: `custom_components/mojv/notifications.py`
- Modify: `custom_components/mojv/__init__.py`
- Test: `tests/test_notifications_v2.py`

**Interfaces:**
- Consumes rules/history/options.
- Emits persistent notification and bus event; optional notify service calls.

- [ ] **Step 1: Write failing tests**

Wymusić baseline bez historycznej lawiny, deduplikację po restart, event bus dla każdego kandydata, persistent notification, push tylko do skonfigurowanych targetów, quiet-hours suppress push only oraz odporność na błąd pojedynczego targetu.

- [ ] **Step 2: Run RED**

Run: `pytest -q tests/test_notifications_v2.py`
Expected: FAIL against current manager.

- [ ] **Step 3: Implement manager v2**

Manager przechowuje poprzedni snapshot do różnicowania, ładuje historię i stan seen IDs, wywołuje czyste rules, zapisuje history, emituje kanały. Nie tworzyć nowego pollera portalu.

- [ ] **Step 4: GREEN**

Run: `pytest -q tests/test_notifications_v2.py tests/test_notification_rules.py tests/test_notification_history.py tests/test_notification_options.py`
Expected: PASS.

- [ ] **Step 5: Full Python regression**

Run: `pytest -q tests`
Expected: all PASS.

- [ ] **Step 6: Commit**

`git commit -m "feat: wire notification engine v2"`
