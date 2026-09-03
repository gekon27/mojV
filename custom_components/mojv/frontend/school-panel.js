class MojVSchoolPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._data = null;
    this._error = null;
    this._activeStudentId = null;
    this._activeView = "today";
    this._weekOffset = 0;
    this._ticker = null;
    this._refreshing = false;
    this._shellBuilt = false;
    this._lastCurrentKey = null;
  }

  set hass(value) {
    this._hass = value;
    if (this.isConnected && !this._data && !this._refreshing) this._refresh();
  }

  set narrow(value) { this._narrow = value; }
  set panel(value) { this._panel = value; }

  connectedCallback() {
    this._buildShell();
    if (!this._ticker) this._ticker = window.setInterval(() => this._tickClock(), 10000);
    this._tickClock();
    if (this._hass && !this._data && !this._refreshing) this._refresh();
  }

  disconnectedCallback() {
    if (this._ticker) {
      window.clearInterval(this._ticker);
      this._ticker = null;
    }
  }

  _buildShell() {
    if (this._shellBuilt) return;
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="app-shell">
        <header class="topbar">
          <div class="brand-block">
            <img src="/mojv-static/mojv-logo.svg" alt="mojV" class="brand-logo">
            <div class="brand-copy"><span class="eyebrow">mojV</span><h1>Szkoła</h1><p>Plan, obecność i bieżące informacje</p></div>
          </div>
          <div class="top-actions">
            <div class="sync-box"><span id="clock-label">--:--</span><small id="sync-label">Dane jeszcze niepobrane</small></div>
            <button id="refresh" class="icon-button" type="button" aria-label="Odśwież dane" title="Odśwież dane">↻</button>
          </div>
        </header>
        <div id="student-nav" class="student-nav" aria-label="Wybór dziecka"></div>
        <nav id="view-nav" class="view-nav" aria-label="Widok panelu"></nav>
        <main id="view-content" class="view-content" aria-live="polite">
          <section class="empty-state"><strong>Ładowanie mojV…</strong><span>Pobieram dane z Home Assistant.</span></section>
        </main>
      </div>`;

    this.shadowRoot.addEventListener("click", (event) => {
      const target = event.target.closest("button");
      if (!target) return;
      if (target.id === "refresh") return void this._refresh();
      if (target.dataset.student) {
        this._activeStudentId = target.dataset.student;
        this._weekOffset = 0;
        this._lastCurrentKey = null;
        this._renderNavigation();
        this._renderActiveView();
        return;
      }
      if (target.dataset.view) {
        this._activeView = target.dataset.view;
        this._lastCurrentKey = null;
        this._renderNavigation();
        this._renderActiveView();
        return;
      }
      if (target.dataset.week) this._changeWeek(Number(target.dataset.week));
    });
    this._shellBuilt = true;
  }

  async _refresh() {
    if (!this._hass || this._refreshing) return;
    this._refreshing = true;
    this._setRefreshBusy(true);
    try {
      const payload = await this._hass.callWS({ type: "mojv/panel" });
      this._error = null;
      this._applyPayload(payload);
    } catch (error) {
      this._error = String(error);
      const content = this.shadowRoot.querySelector("#view-content");
      if (content) content.innerHTML = `<section class="empty-state error"><strong>Nie udało się odświeżyć panelu</strong><span>${this._e(this._error)}</span></section>`;
    } finally {
      this._refreshing = false;
      this._setRefreshBusy(false);
    }
  }

  _applyPayload(payload) {
    this._data = payload || { students: [] };
    const students = this._data.students || [];
    if (!students.some((student) => student.id === this._activeStudentId)) this._activeStudentId = students[0]?.id || null;
    this._lastCurrentKey = null;
    this._renderSyncLabel();
    this._renderNavigation();
    this._renderActiveView();
  }

  _setRefreshBusy(busy) {
    const button = this.shadowRoot.querySelector("#refresh");
    if (!button) return;
    button.disabled = busy;
    button.classList.toggle("busy", busy);
    button.textContent = busy ? "…" : "↻";
  }

  _renderSyncLabel() {
    const label = this.shadowRoot.querySelector("#sync-label");
    if (label) label.textContent = this._data?.updated_at ? `Dane: ${this._time(this._data.updated_at)}` : "Dane jeszcze niepobrane";
  }

  _activeStudent() {
    const students = this._data?.students || [];
    return students.find((student) => student.id === this._activeStudentId) || students[0] || null;
  }

  _availableViews(student) {
    const views = [["today", "Dzisiaj", "●"], ["schedule", "Plan", "▦"], ["attendance", "Frekwencja", "✓"]];
    if ((student?.grades || []).length) views.push(["grades", "Oceny", "5"]);
    if ((student?.remarks || []).length) views.push(["remarks", "Uwagi", "!"]);
    return views;
  }

  _renderNavigation() {
    const students = this._data?.students || [];
    const studentNav = this.shadowRoot.querySelector("#student-nav");
    const viewNav = this.shadowRoot.querySelector("#view-nav");
    if (!studentNav || !viewNav) return;

    studentNav.innerHTML = students.length > 1 ? students.map((student, index) => {
      const active = student.id === this._activeStudentId;
      const initial = (student.name || `D${index + 1}`).trim().charAt(0).toUpperCase();
      return `<button type="button" class="student-chip ${active ? "active" : ""}" data-student="${this._e(student.id)}" aria-pressed="${active}"><span class="avatar">${this._e(initial)}</span><span class="student-copy"><strong>${this._e(student.name)}</strong><small>${this._e(student.class || "")}</small></span></button>`;
    }).join("") : "";

    const views = this._availableViews(this._activeStudent());
    if (!views.some(([id]) => id === this._activeView)) this._activeView = "today";
    viewNav.innerHTML = views.map(([id, label, icon]) => {
      const active = id === this._activeView;
      return `<button type="button" class="view-tab ${active ? "active" : ""}" data-view="${id}" aria-current="${active ? "page" : "false"}"><span>${icon}</span>${label}</button>`;
    }).join("");
  }

  _renderActiveView() {
    const content = this.shadowRoot.querySelector("#view-content");
    if (!content) return;
    if (this._error) {
      content.innerHTML = `<section class="empty-state error"><strong>Błąd panelu</strong><span>${this._e(this._error)}</span></section>`;
      return;
    }
    const student = this._activeStudent();
    if (!student) {
      content.innerHTML = `<section class="empty-state"><strong>Brak danych ucznia</strong><span>Odśwież panel po uruchomieniu integracji.</span></section>`;
      return;
    }

    if (this._activeView === "schedule") {
      content.innerHTML = this._renderSchedule(student);
      window.requestAnimationFrame(() => this._positionTimeLine());
    } else if (this._activeView === "attendance") content.innerHTML = this._renderAttendance(student);
    else if (this._activeView === "grades") content.innerHTML = this._renderGrades(student);
    else if (this._activeView === "remarks") content.innerHTML = this._renderRemarks(student);
    else {
      content.innerHTML = this._renderToday(student);
      this._lastCurrentKey = this._lessonKey(this._currentLesson(student));
      this._updateTodayLive();
    }
  }

  _renderToday(student) {
    const now = new Date();
    const current = this._currentLesson(student, now);
    const next = this._nextLesson(student, now);
    const lessons = this._todayLessons(student, now);
    const [attendanceText, attendanceClass, attendanceMark] = this._attendance(current?.attendance);
    const alerts = current?.alerts || [];
    const completed = lessons.filter((lesson) => new Date(lesson.end) <= now).length;

    return `<div class="today-layout">
      <section class="hero-card card">
        <div class="card-head"><div><span class="kicker">Dzisiaj</span><h2>${this._e(this._longDate(now))}</h2></div><span class="class-pill">${this._e(student.class || "Uczeń")}</span></div>
        <div class="lesson-hero">
          <div class="lesson-primary"><span class="kicker">Aktualna lekcja</span><h3>${this._e(current?.subject || "Przerwa / brak lekcji")}</h3><div class="lesson-meta">${current ? this._lessonMeta(current) : "Brak trwającej lekcji"}</div>${current?.teacher ? `<div class="teacher-line">${this._e(current.teacher)}</div>` : ""}</div>
          <div id="live-progress" class="progress-ring" style="--progress:${this._progress(current, now) * 3.6}deg"><div><strong id="live-minutes">${current ? this._minutesToEnd(current, now) : "—"}</strong><span>${current ? "min do końca" : "przerwa"}</span></div></div>
        </div>
        <div class="next-card"><div><span class="kicker">Następna</span><strong>${this._e(next?.subject || "Brak kolejnej lekcji")}</strong></div><span>${next ? `${this._time(next.start)}–${this._time(next.end)} · ${this._e(next.room || "bez sali")}` : ""}</span></div>
        <div class="metric-grid">
          <article class="metric ${attendanceClass}"><span>${this._e(attendanceMark)}</span><div><small>Obecność</small><strong>${this._e(current ? attendanceText : "Poza lekcją")}</strong></div></article>
          <article class="metric"><span>№</span><div><small>Lekcja</small><strong>${this._e(current?.number || "—")}</strong></div></article>
          <article class="metric"><span>✓</span><div><small>Postęp dnia</small><strong>${completed}/${lessons.length}</strong></div></article>
        </div>
      </section>
      <section class="card day-card"><div class="section-head"><div><span class="kicker">Plan dnia</span><h2>${lessons.length} lekcji</h2></div><span>${this._e(student.name)}</span></div><div class="timeline-list">${lessons.length ? lessons.map((lesson) => this._todayLessonRow(lesson, current)).join("") : `<div class="mini-empty">Brak lekcji na dziś.</div>`}</div></section>
      <section class="card alerts-card"><div class="section-head"><div><span class="kicker">Bieżące</span><h2>Informacje</h2></div></div>${alerts.length ? `<div class="alert-list">${alerts.map((alert) => `<article class="alert-row"><span>${alert.kind === "absence" ? "×" : alert.kind === "late" ? "!" : "⌛"}</span><div><strong>${this._e(alert.text)}</strong><small>${this._time(now)}</small></div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak bieżących alertów.</div>`}</section>
    </div>`;
  }

  _todayLessonRow(lesson, current) {
    const [text, cls, mark] = this._attendance(lesson.attendance);
    const isCurrent = current && this._lessonKey(current) === this._lessonKey(lesson);
    return `<article class="timeline-row ${isCurrent ? "current" : ""} ${lesson.cancelled ? "cancelled" : ""}"><div class="timeline-time">${this._time(lesson.start)}<small>${this._time(lesson.end)}</small></div><div class="timeline-dot"></div><div class="timeline-copy"><div><strong>${this._e(lesson.subject)}</strong>${lesson.replacement ? `<span class="badge warn">Zastępstwo</span>` : ""}${lesson.cancelled ? `<span class="badge bad">Odwołana</span>` : ""}</div><span>Lekcja ${this._e(lesson.number)} · ${this._e(lesson.room || "bez sali")}${lesson.teacher ? ` · ${this._e(lesson.teacher)}` : ""}</span></div><div class="attendance-dot ${cls}" title="${this._e(text)}">${this._e(mark)}</div></article>`;
  }

  _renderSchedule(student) {
    const days = this._weekDays(student, this._weekOffset);
    const slots = this._scheduleSlots(days);
    const weekStart = this._startOfWeek(this._weekOffset);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 4);

    const rows = slots.map((slot) => {
      const cells = days.map((day) => {
        const lessons = (day.lessons || []).filter((lesson) => {
          const lessonKey = this._slotKey(lesson);
          return lessonKey === slot.key;
        });
        return `<td class="schedule-cell ${day.today && this._weekOffset === 0 ? "today-column" : ""}">${lessons.map((lesson) => this._scheduleLesson(lesson)).join("")}</td>`;
      }).join("");
      return `<tr class="schedule-row" data-start-minute="${slot.startMinute}" data-end-minute="${slot.endMinute}"><th class="time-cell"><strong>${this._minuteLabel(slot.startMinute)}</strong><span>${this._minuteLabel(slot.endMinute)}</span></th>${cells}</tr>`;
    }).join("");

    return `<section class="card schedule-card">
      <div class="schedule-toolbar"><div><span class="kicker">Plan lekcji</span><h2>${this._e(this._dateRange(weekStart, weekEnd))}</h2></div><div class="week-controls" aria-label="Zmiana tygodnia"><button type="button" class="week-button" data-week="-1" ${this._weekOffset <= -1 ? "disabled" : ""}>‹</button><button type="button" class="week-current" data-week="0">${this._weekOffset === 0 ? "Bieżący tydzień" : "Dzisiaj"}</button><button type="button" class="week-button" data-week="1" ${this._weekOffset >= 1 ? "disabled" : ""}>›</button></div></div>
      <div class="schedule-scroll">${slots.length ? `<div class="schedule-canvas"><div id="time-line" class="time-line"><span id="time-line-label">--:--</span></div><table class="schedule-table"><thead><tr><th class="time-head">Godzina</th>${days.map((day) => `<th class="day-head ${day.today && this._weekOffset === 0 ? "today" : ""}"><strong>${this._e(day.shortLabel)}</strong><span>${this._e(this._date(day.date))}</span></th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="mini-empty roomy">Brak planu w wybranym tygodniu.</div>`}</div>
    </section>`;
  }

  _scheduleLesson(lesson) {
    const [text, cls, mark] = this._attendance(lesson.attendance);
    return `<div class="schedule-lesson ${lesson.cancelled ? "cancelled" : ""}" data-start="${this._e(lesson.start)}" data-end="${this._e(lesson.end)}"><div class="schedule-lesson-top"><span class="lesson-number">${this._e(lesson.number)}</span><strong>${this._e(lesson.subject)}</strong><span class="attendance-mini ${cls}" title="${this._e(text)}">${this._e(mark)}</span></div><div class="schedule-lesson-meta">${this._e(lesson.room || "bez sali")}${lesson.teacher ? ` · ${this._e(lesson.teacher)}` : ""}</div><div class="badge-row">${lesson.replacement ? `<span class="badge warn">Zastępstwo</span>` : ""}${lesson.cancelled ? `<span class="badge bad">Odwołana</span>` : ""}</div></div>`;
  }

  _renderAttendance(student) {
    const summary = student.attendance_summary || {};
    const statuses = [["present", "Obecności", "✓", "good"], ["absent", "Nieobecności", "×", "bad"], ["excused_absence", "Usprawiedliwione", "U", "neutral"], ["late", "Spóźnienia", "!", "warn"], ["released", "Zwolnienia", "Z", "neutral"]];
    const events = this._allLessons(student).filter((lesson) => !lesson.cancelled && !["not_recorded", "present"].includes(lesson.attendance)).sort((a, b) => new Date(b.start) - new Date(a.start)).slice(0, 30);
    return `<div class="attendance-layout"><section class="attendance-summary">${statuses.map(([key, label, mark, cls]) => `<article class="summary-card ${cls}"><span>${mark}</span><div><strong>${Number(summary[key] || 0)}</strong><small>${label}</small></div></article>`).join("")}</section><section class="card attendance-list-card"><div class="section-head"><div><span class="kicker">Frekwencja</span><h2>Ostatnie wpisy</h2></div><span>${this._e(student.name)}</span></div>${events.length ? `<div class="attendance-list">${events.map((lesson) => { const [text, cls, mark] = this._attendance(lesson.attendance); return `<article class="attendance-row"><span class="attendance-dot ${cls}">${this._e(mark)}</span><div><strong>${this._e(text)}</strong><span>${this._e(lesson.subject)} · lekcja ${this._e(lesson.number)}</span></div><time>${this._e(this._date(lesson.start, true))}<small>${this._time(lesson.start)}</small></time></article>`; }).join("")}</div>` : `<div class="mini-empty roomy">Brak nieobecności, spóźnień lub zwolnień w pobranym zakresie.</div>`}</section></div>`;
  }

  _renderGrades(student) {
    const grades = [...(student.grades || [])].sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card list-view-card"><div class="section-head"><div><span class="kicker">Oceny</span><h2>Najnowsze wpisy</h2></div><span>${grades.length}</span></div><div class="data-list">${grades.map((grade) => `<article class="data-row"><div class="grade-badge">${this._e(grade.value)}</div><div><strong>${this._e(grade.subject)}</strong><span>${this._e(grade.description || "Bez opisu")}</span></div><time>${this._e(this._date(grade.date, true))}</time></article>`).join("")}</div></section>`;
  }

  _renderRemarks(student) {
    const remarks = [...(student.remarks || [])].sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card list-view-card"><div class="section-head"><div><span class="kicker">Uwagi</span><h2>Ostatnie wpisy</h2></div><span>${remarks.length}</span></div><div class="data-list">${remarks.map((remark) => `<article class="data-row"><div class="remark-badge">!</div><div><strong>${this._e(remark.category || "Informacja")}</strong><span>${this._e(remark.text)}</span><small>${this._e(remark.author || "")}</small></div><time>${this._e(this._date(remark.date, true))}</time></article>`).join("")}</div></section>`;
  }

  _changeWeek(delta) {
    if (delta === 0) this._weekOffset = 0;
    else this._weekOffset = Math.max(-1, Math.min(1, this._weekOffset + delta));
    if (this._activeView === "schedule") this._renderActiveView();
  }

  _weekDays(student, offset) {
    const start = this._startOfWeek(offset);
    const source = new Map((student.week || []).map((day) => [day.date, day]));
    const labels = ["Pon", "Wt", "Śr", "Czw", "Pt"];
    const todayKey = this._dateKey(new Date());
    return labels.map((shortLabel, index) => {
      const date = new Date(start);
      date.setDate(start.getDate() + index);
      const key = this._dateKey(date);
      return { date: key, shortLabel, today: key === todayKey, lessons: source.get(key)?.lessons || [] };
    });
  }

  _scheduleSlots(days) {
    const slots = new Map();
    for (const day of days) {
      for (const lesson of day.lessons || []) {
        const key = this._slotKey(lesson);
        if (!slots.has(key)) {
          slots.set(key, { key, startMinute: this._minuteOfDay(lesson.start), endMinute: this._minuteOfDay(lesson.end) });
        }
      }
    }
    return [...slots.values()].sort((a, b) => a.startMinute - b.startMinute || a.endMinute - b.endMinute);
  }

  _slotKey(lesson) {
    return `${this._minuteOfDay(lesson.start)}|${this._minuteOfDay(lesson.end)}`;
  }

  _startOfWeek(offset = 0) {
    const now = new Date();
    const result = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekday = result.getDay() || 7;
    result.setDate(result.getDate() - weekday + 1 + offset * 7);
    result.setHours(0, 0, 0, 0);
    return result;
  }

  _allLessons(student) {
    const lessons = [];
    const seen = new Set();
    for (const day of student.week || []) {
      for (const lesson of day.lessons || []) {
        const key = this._lessonKey(lesson);
        if (seen.has(key)) continue;
        seen.add(key);
        lessons.push(lesson);
      }
    }
    return lessons.sort((a, b) => new Date(a.start) - new Date(b.start));
  }

  _todayLessons(student, now = new Date()) {
    const key = this._dateKey(now);
    return this._allLessons(student).filter((lesson) => this._dateKey(new Date(lesson.start)) === key);
  }

  _currentLesson(student, now = new Date()) {
    return this._allLessons(student).find((lesson) => !lesson.cancelled && new Date(lesson.start) <= now && now < new Date(lesson.end)) || null;
  }

  _nextLesson(student, now = new Date()) {
    return this._allLessons(student).find((lesson) => !lesson.cancelled && new Date(lesson.start) > now) || null;
  }

  _tickClock() {
    const clock = this.shadowRoot.querySelector("#clock-label");
    if (clock) clock.textContent = this._time(new Date());
    if (!this._data) return;
    if (this._activeView === "today") this._updateTodayLive();
    else if (this._activeView === "schedule") {
      this._updateScheduleCurrentClasses();
      window.requestAnimationFrame(() => this._positionTimeLine());
    }
  }

  _updateTodayLive() {
    const student = this._activeStudent();
    if (!student) return;
    const now = new Date();
    const current = this._currentLesson(student, now);
    const key = this._lessonKey(current);
    if (this._lastCurrentKey !== null && this._lastCurrentKey !== key) {
      this._lastCurrentKey = key;
      this._renderActiveView();
      return;
    }
    this._lastCurrentKey = key;
    const minutes = this.shadowRoot.querySelector("#live-minutes");
    const progress = this.shadowRoot.querySelector("#live-progress");
    if (minutes) minutes.textContent = current ? String(this._minutesToEnd(current, now)) : "—";
    if (progress) progress.style.setProperty("--progress", `${this._progress(current, now) * 3.6}deg`);
  }

  _updateScheduleCurrentClasses() {
    const now = new Date();
    this.shadowRoot.querySelectorAll(".schedule-lesson").forEach((element) => {
      const start = new Date(element.dataset.start);
      const end = new Date(element.dataset.end);
      element.classList.toggle("current", this._weekOffset === 0 && start <= now && now < end);
    });
  }

  _positionTimeLine() {
    const line = this.shadowRoot.querySelector("#time-line");
    if (!line || this._activeView !== "schedule" || this._weekOffset !== 0) {
      if (line) line.style.display = "none";
      return;
    }
    const now = new Date();
    const weekday = now.getDay();
    if (weekday < 1 || weekday > 5) return void (line.style.display = "none");
    const minute = now.getHours() * 60 + now.getMinutes();
    const row = [...this.shadowRoot.querySelectorAll(".schedule-row")].find((candidate) => minute >= Number(candidate.dataset.startMinute) && minute <= Number(candidate.dataset.endMinute));
    if (!row || row.offsetHeight <= 0) return void (line.style.display = "none");
    const start = Number(row.dataset.startMinute);
    const end = Number(row.dataset.endMinute);
    const ratio = end > start ? (minute - start) / (end - start) : 0;
    line.style.top = `${row.offsetTop + Math.max(0, Math.min(1, ratio)) * row.offsetHeight}px`;
    line.style.display = "block";
    const label = this.shadowRoot.querySelector("#time-line-label");
    if (label) label.textContent = this._time(now);
  }

  _lessonKey(lesson) { return lesson ? `${lesson.start || ""}|${lesson.end || ""}|${lesson.number || ""}|${lesson.subject || ""}` : ""; }
  _lessonMeta(lesson) { return `Lekcja ${this._e(lesson.number)} · ${this._time(lesson.start)}–${this._time(lesson.end)} · ${this._e(lesson.room || "bez sali")}`; }
  _minutesToEnd(lesson, now = new Date()) { return lesson ? Math.max(0, Math.ceil((new Date(lesson.end) - now) / 60000)) : 0; }
  _progress(lesson, now = new Date()) {
    if (!lesson) return 0;
    const start = new Date(lesson.start).getTime();
    const end = new Date(lesson.end).getTime();
    return end <= start ? 0 : Math.max(0, Math.min(100, Math.round(((now.getTime() - start) / (end - start)) * 100)));
  }
  _minuteOfDay(value) { const date = new Date(value); return date.getHours() * 60 + date.getMinutes(); }
  _minuteLabel(minute) { return `${String(Math.floor(minute / 60)).padStart(2, "0")}:${String(minute % 60).padStart(2, "0")}`; }

  _attendance(value) {
    const map = { present: ["Obecny", "ok", "✓"], absent: ["Nieobecny", "bad", "×"], excused_absence: ["Usprawiedliwiona", "muted", "U"], late: ["Spóźniony", "warn", "!"], excused_late: ["Spóźnienie uspraw.", "muted", "U"], school_activity: ["Zajęcia szkolne", "ok", "✓"], released: ["Zwolniony", "muted", "Z"], not_recorded: ["Brak wpisu", "muted", "•"], unknown: ["Nieznany", "muted", "?"] };
    return map[value] || [value || "Brak wpisu", "muted", "•"];
  }

  _e(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
  _time(value) { return value ? new Date(value).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) : "—"; }
  _date(value, withYear = false) { return value ? new Date(value).toLocaleDateString("pl-PL", withYear ? { day: "2-digit", month: "2-digit", year: "numeric" } : { day: "2-digit", month: "2-digit" }) : "—"; }
  _dateKey(value) { const date = value instanceof Date ? value : new Date(value); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
  _longDate(value) { const date = value instanceof Date ? value : new Date(value || Date.now()); const text = date.toLocaleDateString("pl-PL", { weekday: "long", day: "numeric", month: "long" }); return text.charAt(0).toUpperCase() + text.slice(1); }
  _dateRange(start, end) { return `${start.toLocaleDateString("pl-PL", { day: "numeric", month: "short" })} – ${end.toLocaleDateString("pl-PL", { day: "numeric", month: "short", year: "numeric" })}`; }

  _styles() {
    return `
      :host{display:block;min-height:100%;color:var(--primary-text-color,#e9eef5);background:var(--primary-background-color,#0b1118);font-family:var(--paper-font-body1_-_font-family,Inter,system-ui,sans-serif);--mv-accent:var(--primary-color,#3f8cff);--mv-card:var(--ha-card-background,var(--card-background-color,#151d27));--mv-soft:var(--secondary-background-color,rgba(127,127,127,.09));--mv-line:var(--divider-color,rgba(127,127,127,.2));--mv-muted:var(--secondary-text-color,#91a0b2);--mv-good:#35b86b;--mv-bad:#e85b61;--mv-warn:#e7a633;--mv-radius:18px}*{box-sizing:border-box}button{font:inherit;color:inherit}.app-shell{max-width:1560px;margin:0 auto;padding:18px 22px 36px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:76px;margin-bottom:12px}.brand-block{display:flex;align-items:center;min-width:0;gap:13px}.brand-logo{width:48px;height:48px;object-fit:contain}.brand-copy{min-width:0}.eyebrow,.kicker{color:var(--mv-accent);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.09em}.brand-copy h1{margin:1px 0 0;font-size:27px;line-height:1;letter-spacing:-.025em}.brand-copy p{margin:6px 0 0;color:var(--mv-muted);font-size:12px}.top-actions{display:flex;align-items:center;gap:12px}.sync-box{text-align:right;display:grid;gap:2px}.sync-box>span{font-size:18px;font-weight:760;font-variant-numeric:tabular-nums}.sync-box small{color:var(--mv-muted);font-size:10px}.icon-button,.week-button,.week-current{min-width:44px;min-height:44px;border:1px solid var(--mv-line);background:var(--mv-card);border-radius:13px;cursor:pointer;transition:.16s}.icon-button:hover,.week-button:hover,.week-current:hover{transform:translateY(-1px);border-color:var(--mv-accent)}button:disabled{opacity:.35;cursor:default;transform:none!important}.student-nav{display:flex;gap:8px;overflow-x:auto;scrollbar-width:thin;margin-bottom:10px}.student-nav:empty{display:none}.student-chip{min-width:170px;min-height:52px;padding:7px 12px;border:1px solid var(--mv-line);border-radius:15px;background:var(--mv-card);display:flex;align-items:center;gap:9px;cursor:pointer;text-align:left}.student-chip.active{border-color:var(--mv-accent);background:color-mix(in srgb,var(--mv-accent) 8%,var(--mv-card))}.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;flex:0 0 auto;background:color-mix(in srgb,var(--mv-accent) 20%,var(--mv-soft));color:var(--mv-accent);font-weight:850}.student-copy strong,.student-copy small{display:block}.student-copy strong{font-size:12px}.student-copy small{margin-top:2px;color:var(--mv-muted);font-size:10px}.view-nav{display:flex;gap:4px;padding:4px;margin-bottom:14px;border:1px solid var(--mv-line);border-radius:15px;background:var(--mv-card);width:max-content;max-width:100%;overflow-x:auto}.view-tab{min-height:40px;padding:0 14px;border:0;border-radius:11px;background:transparent;color:var(--mv-muted);font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:7px;white-space:nowrap}.view-tab.active{color:var(--primary-text-color,#fff);background:color-mix(in srgb,var(--mv-accent) 15%,transparent);box-shadow:inset 0 -2px 0 var(--mv-accent)}.view-tab>span{color:var(--mv-accent)}.view-content{min-height:360px}.card{background:var(--mv-card);border:1px solid var(--mv-line);border-radius:var(--mv-radius);overflow:hidden;box-shadow:0 8px 28px rgba(0,0,0,.08)}.empty-state{min-height:280px;display:grid;place-content:center;justify-items:center;gap:7px;color:var(--mv-muted);text-align:center;border:1px dashed var(--mv-line);border-radius:var(--mv-radius)}.empty-state strong{color:var(--primary-text-color,#fff);font-size:17px}.empty-state.error strong{color:var(--mv-bad)}.mini-empty{color:var(--mv-muted);font-size:12px;padding:14px}.mini-empty.roomy{padding:36px 18px;text-align:center}.class-pill{padding:5px 9px;border-radius:999px;background:var(--mv-soft);color:var(--mv-muted);font-size:10px;font-weight:700}.section-head,.card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:18px 19px;border-bottom:1px solid var(--mv-line)}.section-head h2,.card-head h2{margin:4px 0 0;font-size:18px}.section-head>span{color:var(--mv-muted);font-size:11px}.today-layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(330px,.65fr);grid-template-areas:"hero day" "hero alerts";gap:14px}.hero-card{grid-area:hero}.day-card{grid-area:day}.alerts-card{grid-area:alerts}.lesson-hero{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center;padding:24px 20px 19px}.lesson-primary h3{margin:7px 0 9px;font-size:29px;letter-spacing:-.035em}.lesson-meta,.teacher-line{color:var(--mv-muted);font-size:12px;line-height:1.5}.teacher-line{margin-top:5px}.progress-ring{--progress:0deg;width:124px;height:124px;border-radius:50%;padding:9px;background:conic-gradient(var(--mv-accent) var(--progress),var(--mv-soft) 0)}.progress-ring>div{width:100%;height:100%;border-radius:50%;display:grid;place-content:center;text-align:center;background:var(--mv-card);border:1px solid var(--mv-line)}.progress-ring strong{font-size:31px;line-height:1}.progress-ring span{color:var(--mv-muted);font-size:9px;margin-top:5px}.next-card{margin:0 19px 16px;padding:13px 14px;display:flex;justify-content:space-between;align-items:center;gap:14px;border:1px solid var(--mv-line);border-radius:13px;background:var(--mv-soft)}.next-card strong{display:block;margin-top:4px;font-size:13px}.next-card>span{color:var(--mv-muted);font-size:10px;text-align:right}.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:0 19px 19px}.metric{min-height:64px;padding:10px;display:flex;align-items:center;gap:9px;border:1px solid var(--mv-line);border-radius:13px;background:var(--mv-soft)}.metric>span{width:30px;height:30px;display:grid;place-items:center;border-radius:50%;background:color-mix(in srgb,var(--mv-accent) 14%,transparent);color:var(--mv-accent);font-weight:900}.metric.ok>span{color:var(--mv-good)}.metric.bad>span{color:var(--mv-bad)}.metric.warn>span{color:var(--mv-warn)}.metric small,.metric strong{display:block}.metric small{color:var(--mv-muted);font-size:9px}.metric strong{margin-top:2px;font-size:11px}.timeline-list{padding:7px 14px 13px}.timeline-row{min-height:58px;display:grid;grid-template-columns:48px 12px 1fr 26px;gap:8px;align-items:center;border-bottom:1px solid var(--mv-line)}.timeline-row:last-child{border-bottom:0}.timeline-row.current{background:color-mix(in srgb,var(--mv-accent) 8%,transparent);margin:0 -8px;padding:0 8px;border-radius:10px}.timeline-row.cancelled{opacity:.5}.timeline-time{font-size:10px;font-weight:800}.timeline-time small{display:block;color:var(--mv-muted);font-size:9px}.timeline-dot{width:8px;height:8px;border-radius:50%;background:var(--mv-line)}.timeline-row.current .timeline-dot{background:var(--mv-accent)}.timeline-copy{min-width:0}.timeline-copy>div{display:flex;align-items:center;gap:5px;flex-wrap:wrap}.timeline-copy strong{font-size:11px}.timeline-copy>span{display:block;color:var(--mv-muted);margin-top:3px;font-size:9.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.attendance-dot,.attendance-mini{display:grid;place-items:center;border-radius:50%;font-weight:900}.attendance-dot{width:24px;height:24px;font-size:10px}.attendance-mini{width:20px;height:20px;font-size:9px}.attendance-dot.ok,.attendance-mini.ok{color:var(--mv-good);background:color-mix(in srgb,var(--mv-good) 18%,transparent)}.attendance-dot.bad,.attendance-mini.bad{color:var(--mv-bad);background:color-mix(in srgb,var(--mv-bad) 18%,transparent)}.attendance-dot.warn,.attendance-mini.warn{color:var(--mv-warn);background:color-mix(in srgb,var(--mv-warn) 18%,transparent)}.attendance-dot.muted,.attendance-mini.muted{color:var(--mv-muted);background:var(--mv-soft)}.badge{display:inline-flex;align-items:center;min-height:18px;padding:0 6px;border-radius:999px;font-size:8px;font-weight:800}.badge.warn{background:color-mix(in srgb,var(--mv-warn) 17%,transparent);color:var(--mv-warn)}.badge.bad{background:color-mix(in srgb,var(--mv-bad) 17%,transparent);color:var(--mv-bad)}.alert-list{padding:8px 14px 14px}.alert-row{min-height:54px;display:grid;grid-template-columns:30px 1fr;gap:9px;align-items:center;border-bottom:1px solid var(--mv-line)}.alert-row:last-child{border-bottom:0}.alert-row>span{width:27px;height:27px;border-radius:50%;display:grid;place-items:center;background:var(--mv-soft);color:var(--mv-accent);font-weight:900}.alert-row strong,.alert-row small{display:block}.alert-row strong{font-size:11px}.alert-row small{color:var(--mv-muted);font-size:9px}.schedule-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:17px 18px;border-bottom:1px solid var(--mv-line)}.schedule-toolbar h2{margin:4px 0 0;font-size:18px}.week-controls{display:flex;align-items:center;gap:6px}.week-button{width:44px;padding:0;font-size:24px}.week-current{padding:0 14px;font-size:11px;font-weight:750}.schedule-scroll{width:100%;overflow-x:auto;overscroll-behavior-inline:contain}.schedule-canvas{position:relative;min-width:1040px}.schedule-table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}.schedule-table th,.schedule-table td{border-right:1px solid var(--mv-line);border-bottom:1px solid var(--mv-line)}.schedule-table tr:last-child th,.schedule-table tr:last-child td{border-bottom:0}.schedule-table th:last-child,.schedule-table td:last-child{border-right:0}.time-head,.time-cell{width:84px;min-width:84px;text-align:center;background:color-mix(in srgb,var(--mv-soft) 65%,var(--mv-card))}.time-head{height:52px;color:var(--mv-muted);font-size:9px;text-transform:uppercase}.day-head{height:52px;padding:7px;background:var(--mv-card);text-align:center}.day-head strong,.day-head span{display:block}.day-head strong{font-size:11px}.day-head span{color:var(--mv-muted);margin-top:3px;font-size:9px}.day-head.today{background:color-mix(in srgb,var(--mv-accent) 12%,var(--mv-card));box-shadow:inset 0 -2px 0 var(--mv-accent)}.time-cell{padding:8px 5px;vertical-align:top}.time-cell strong,.time-cell span{display:block}.time-cell strong{font-size:10px}.time-cell span{color:var(--mv-muted);font-size:9px}.schedule-cell{min-height:72px;padding:5px;vertical-align:top;background:var(--mv-card)}.schedule-cell.today-column{background:color-mix(in srgb,var(--mv-accent) 3%,var(--mv-card))}.schedule-lesson{min-height:64px;padding:7px 8px;border:1px solid var(--mv-line);border-radius:10px;background:var(--mv-soft)}.schedule-lesson+.schedule-lesson{margin-top:4px}.schedule-lesson.current{border-color:var(--mv-accent);background:color-mix(in srgb,var(--mv-accent) 13%,var(--mv-soft));box-shadow:inset 3px 0 0 var(--mv-accent)}.schedule-lesson.cancelled{opacity:.48}.schedule-lesson-top{display:grid;grid-template-columns:20px 1fr 20px;gap:5px}.schedule-lesson-top strong{font-size:10.5px}.lesson-number{color:var(--mv-muted);font-size:9px;font-weight:800}.schedule-lesson-meta{color:var(--mv-muted);margin:4px 0 0 25px;font-size:8.5px}.badge-row{margin:4px 0 0 25px;display:flex;gap:4px}.time-line{display:none;position:absolute;z-index:20;left:84px;right:0;height:2px;background:var(--mv-accent);pointer-events:none}.time-line span{position:absolute;left:-73px;top:-10px;width:67px;height:21px;display:grid;place-items:center;border-radius:6px;background:var(--mv-accent);color:white;font-size:9px;font-weight:900}.attendance-layout{display:grid;gap:14px}.attendance-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}.summary-card{min-height:90px;padding:14px;display:flex;align-items:center;gap:12px;border:1px solid var(--mv-line);border-radius:16px;background:var(--mv-card)}.summary-card>span{width:38px;height:38px;display:grid;place-items:center;border-radius:50%;background:var(--mv-soft);font-weight:900}.summary-card.good>span{color:var(--mv-good)}.summary-card.bad>span{color:var(--mv-bad)}.summary-card.warn>span{color:var(--mv-warn)}.summary-card strong,.summary-card small{display:block}.summary-card strong{font-size:24px}.summary-card small{color:var(--mv-muted);font-size:9px}.attendance-list{padding:5px 16px 13px}.attendance-row{min-height:62px;display:grid;grid-template-columns:28px 1fr auto;gap:10px;align-items:center;border-bottom:1px solid var(--mv-line)}.attendance-row:last-child{border-bottom:0}.attendance-row strong,.attendance-row span,.attendance-row time,.attendance-row time small{display:block}.attendance-row strong{font-size:11px}.attendance-row span{color:var(--mv-muted);font-size:9.5px}.attendance-row time{color:var(--mv-muted);text-align:right;font-size:9px}.list-view-card{max-width:980px}.data-list{padding:5px 16px 13px}.data-row{min-height:66px;display:grid;grid-template-columns:42px 1fr auto;gap:11px;align-items:center;border-bottom:1px solid var(--mv-line)}.data-row:last-child{border-bottom:0}.data-row strong,.data-row span,.data-row small{display:block}.data-row strong{font-size:12px}.data-row span,.data-row small{color:var(--mv-muted);font-size:9.5px}.data-row time{color:var(--mv-muted);font-size:9px}.grade-badge,.remark-badge{width:38px;height:38px;display:grid;place-items:center;border-radius:11px;font-weight:900}.grade-badge{color:var(--mv-good);background:color-mix(in srgb,var(--mv-good) 18%,transparent)}.remark-badge{color:var(--mv-warn);background:color-mix(in srgb,var(--mv-warn) 18%,transparent)}
      @media(max-width:1100px){.today-layout{grid-template-columns:1fr 1fr;grid-template-areas:"hero hero" "day alerts"}.attendance-summary{grid-template-columns:repeat(3,1fr)}}
      @media(max-width:760px){.app-shell{padding:10px 10px 26px}.topbar{min-height:64px}.brand-logo{width:40px;height:40px}.brand-copy h1{font-size:22px}.brand-copy p,.sync-box small{display:none}.sync-box>span{font-size:14px}.view-nav{width:100%}.view-tab{flex:1 0 auto;justify-content:center;min-height:44px}.today-layout{grid-template-columns:1fr;grid-template-areas:"hero" "day" "alerts"}.lesson-hero{padding:18px 15px;gap:12px}.lesson-primary h3{font-size:23px}.progress-ring{width:98px;height:98px}.progress-ring strong{font-size:24px}.next-card{margin:0 14px 12px;align-items:flex-start;flex-direction:column}.next-card>span{text-align:left}.metric-grid{padding:0 14px 14px;grid-template-columns:1fr}.schedule-toolbar{padding:14px;align-items:flex-start;flex-direction:column}.week-controls{width:100%}.week-current{flex:1}.attendance-summary{grid-template-columns:repeat(2,1fr)}.summary-card{min-height:72px;padding:10px}.attendance-row{grid-template-columns:28px 1fr}.attendance-row time{grid-column:2;text-align:left}.data-row{grid-template-columns:38px 1fr}.data-row time{grid-column:2}}
      @media(max-width:430px){.brand-block{gap:8px}.brand-logo{width:36px;height:36px}.icon-button{min-width:42px;min-height:42px}.student-chip{min-width:145px}}
    `;
  }
}

if (!customElements.get("mojv-school-panel")) customElements.define("mojv-school-panel", MojVSchoolPanel);
