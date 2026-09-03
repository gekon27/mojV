class MojVSchoolPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._data = null;
    this._timer = null;
    this._error = null;
    this._activeStudentId = null;
  }

  set hass(value) {
    this._hass = value;
    if (!this._data) this._refresh();
  }

  set narrow(value) { this._narrow = value; }
  set panel(value) { this._panel = value; }

  connectedCallback() {
    this._render();
    this._timer = window.setInterval(() => this._refresh(), 30000);
    this._refresh();
  }

  disconnectedCallback() {
    if (this._timer) window.clearInterval(this._timer);
  }

  async _refresh() {
    if (!this._hass) return;
    try {
      this._data = await this._hass.callWS({ type: "mojv/panel" });
      const students = this._data?.students || [];
      if (!students.some((student) => student.id === this._activeStudentId)) {
        this._activeStudentId = students[0]?.id || null;
      }
      this._error = null;
    } catch (error) {
      this._error = String(error);
    }
    this._render();
  }

  _e(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _time(value) {
    if (!value) return "—";
    return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  _date(value, withYear = false) {
    if (!value) return "—";
    return new Date(value).toLocaleDateString([], withYear
      ? { day: "2-digit", month: "2-digit", year: "numeric" }
      : { day: "2-digit", month: "2-digit" });
  }

  _longDate(value) {
    const date = value ? new Date(value) : new Date();
    const text = date.toLocaleDateString("pl-PL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  _attendance(value) {
    const map = {
      present: ["Obecny", "ok", "✓"],
      absent: ["Nieobecny", "bad", "×"],
      excused_absence: ["Usprawiedliwiona", "muted", "U"],
      late: ["Spóźniony", "warn", "!"],
      excused_late: ["Spóźnienie uspraw.", "muted", "U"],
      school_activity: ["Zajęcia szkolne", "ok", "✓"],
      released: ["Zwolniony", "muted", "Z"],
      not_recorded: ["Brak wpisu", "muted", "•"],
      unknown: ["Nieznany", "muted", "?"],
    };
    return map[value] || [value || "Brak wpisu", "muted", "•"];
  }

  _studentTabs(students) {
    if (students.length < 2) return "";
    return `<nav class="student-tabs" aria-label="Wybór dziecka">
      ${students.map((student, index) => `
        <button class="student-tab ${student.id === this._activeStudentId ? "active" : ""}"
                data-student="${this._e(student.id)}"
                aria-pressed="${student.id === this._activeStudentId}">
          <span class="avatar">${this._e((student.name || `D${index + 1}`).trim().charAt(0).toUpperCase())}</span>
          <span><strong>${this._e(student.name)}</strong><small>${this._e(student.class || "")}</small></span>
        </button>`).join("")}
    </nav>`;
  }

  _week(student) {
    const days = (student.week || []).filter((day) => {
      const weekday = new Date(`${day.date}T12:00:00`).getDay();
      return weekday >= 1 && weekday <= 5;
    });
    if (!days.length) return `<div class="empty">Brak planu tygodniowego</div>`;

    return `<div class="week-grid">${days.map((day) => {
      const lessons = (day.lessons || []).map((lesson) => {
        const [attendanceText, attendanceClass, attendanceMark] = this._attendance(lesson.attendance);
        const change = lesson.cancelled ? "Odwołana" : lesson.replacement ? "Zastępstwo" : "";
        return `<div class="week-lesson ${lesson.current ? "current" : ""} ${lesson.cancelled ? "cancelled" : ""}">
          <div class="week-number">${this._e(lesson.number)}</div>
          <div class="week-main">
            <div class="week-subject">${this._e(lesson.subject)}</div>
            <div class="week-meta">${this._time(lesson.start)}–${this._time(lesson.end)} · ${this._e(lesson.room || "bez sali")}</div>
            ${change ? `<div class="change">${this._e(change)}</div>` : ""}
          </div>
          <div class="attendance-mark ${attendanceClass}" title="${this._e(attendanceText)}">${this._e(attendanceMark)}</div>
        </div>`;
      }).join("");
      return `<section class="day ${day.today ? "today" : ""}">
        <header class="day-head">
          <strong>${this._e(day.label)}</strong>
          <span>${this._e(this._date(day.date))}</span>
        </header>
        <div class="day-lessons">${lessons || `<div class="empty compact">Brak lekcji</div>`}</div>
      </section>`;
    }).join("")}</div>`;
  }

  _progressRing(current) {
    if (!current) {
      return `<div class="progress-ring idle"><div><strong>—</strong><span>przerwa</span></div></div>`;
    }
    const progress = Math.max(0, Math.min(100, Number(current.progress_pct || 0)));
    return `<div class="progress-ring" style="--progress:${progress * 3.6}deg">
      <div><strong>${this._e(current.minutes_to_end)}</strong><span>min do końca</span></div>
    </div>`;
  }

  _today(student) {
    const current = student.current;
    const next = student.next;
    const [attendanceText, attendanceClass, attendanceMark] = this._attendance(current?.attendance);

    return `<section class="panel-card today-card">
      <div class="card-title">Dzisiaj <span>${this._e(this._longDate(this._data?.now))}</span></div>
      <div class="now-row">
        <div class="now-copy">
          <span class="section-label">Aktualna lekcja</span>
          <h2>${this._e(current?.subject || "Przerwa / brak lekcji")}</h2>
          ${current ? `<div class="lesson-line"><strong>Lekcja ${this._e(current.number)}</strong><span>${this._time(current.start)}–${this._time(current.end)}</span><span>${this._e(current.room || "bez sali")}</span></div>` : ""}
          ${current?.teacher ? `<div class="teacher">Nauczyciel: ${this._e(current.teacher)}</div>` : ""}
        </div>
        ${this._progressRing(current)}
      </div>
      <div class="next-row">
        <span class="section-label">Następna lekcja</span>
        ${next
          ? `<div class="next-main"><strong>${this._e(next.subject)}</strong><span>${this._time(next.start)}–${this._time(next.end)} · ${this._e(next.room || "bez sali")}</span></div>`
          : `<div class="next-main"><strong>Brak kolejnej lekcji</strong></div>`}
      </div>
      <div class="status-strip">
        <div class="status-tile ${attendanceClass}"><span>${this._e(attendanceMark)}</span><div><small>Obecność</small><strong>${this._e(current ? attendanceText : "Poza lekcją")}</strong></div></div>
        <div class="status-tile neutral"><span>№</span><div><small>Numer lekcji</small><strong>${this._e(current?.number || "—")}</strong></div></div>
        <div class="status-tile neutral"><span>⌁</span><div><small>Dziś lekcji</small><strong>${this._e((student.lessons || []).length)}</strong></div></div>
      </div>
    </section>`;
  }

  _activity(student) {
    const items = [];
    for (const alert of student.current?.alerts || []) {
      const kindMap = {
        absence: ["bad", "×", "Nieobecność"],
        late: ["warn", "!", "Spóźnienie"],
        ending: ["info", "⌛", "Koniec lekcji"],
      };
      const [cls, mark, title] = kindMap[alert.kind] || ["info", "i", "Informacja"];
      items.push({ cls, mark, title, text: alert.text, time: this._time(this._data?.now) });
    }

    for (const grade of (student.grades || []).slice(0, 2)) {
      items.push({
        cls: "ok",
        mark: "✓",
        title: `Nowa ocena · ${grade.value}`,
        text: `${grade.subject}${grade.description ? ` — ${grade.description}` : ""}`,
        time: this._date(grade.date),
      });
    }

    for (const remark of (student.remarks || []).slice(0, 2)) {
      items.push({
        cls: "info",
        mark: "✦",
        title: remark.category || "Uwaga",
        text: remark.text,
        time: this._date(remark.date),
      });
    }

    if (!items.length) {
      return `<section class="panel-card activity-card"><div class="card-title">Powiadomienia</div><div class="empty">Brak nowych informacji</div></section>`;
    }

    return `<section class="panel-card activity-card">
      <div class="card-title">Powiadomienia <span>${items.length}</span></div>
      <div class="activity-list">${items.slice(0, 5).map((item) => `
        <div class="activity-row">
          <div class="activity-icon ${item.cls}">${this._e(item.mark)}</div>
          <div class="activity-copy"><strong>${this._e(item.title)}</strong><span>${this._e(item.text)}</span></div>
          <time>${this._e(item.time)}</time>
        </div>`).join("")}</div>
    </section>`;
  }

  _grades(student) {
    const grades = (student.grades || []).slice(0, 6);
    return `<section class="panel-card list-card">
      <div class="card-title">Oceny — ostatnie</div>
      ${grades.length ? `<div class="compact-list">${grades.map((grade) => `
        <div class="compact-row">
          <div><strong>${this._e(grade.subject)}</strong><span>${this._e(grade.description || "")}</span></div>
          <div class="grade-value">${this._e(grade.value)}</div>
          <time>${this._e(this._date(grade.date))}</time>
        </div>`).join("")}</div>` : `<div class="empty">Brak ocen do pokazania</div>`}
    </section>`;
  }

  _remarks(student) {
    const remarks = (student.remarks || []).slice(0, 5);
    return `<section class="panel-card list-card">
      <div class="card-title">Uwagi — ostatnie</div>
      ${remarks.length ? `<div class="compact-list">${remarks.map((remark) => `
        <div class="remark-row">
          <span class="remark-dot ${String(remark.points || "").startsWith("-") ? "bad" : "info"}"></span>
          <div><strong>${this._e(remark.category || "Uwaga")}</strong><span>${this._e(remark.text)}</span><small>${this._e(remark.author || "")}</small></div>
          <time>${this._e(this._date(remark.date))}</time>
        </div>`).join("")}</div>` : `<div class="empty">Brak uwag do pokazania</div>`}
    </section>`;
  }

  _studentView(student) {
    return `<div class="dashboard">
      <section class="schedule-card panel-card">
        <div class="card-title">Plan lekcji — cały tydzień <span>${this._e(student.class || "")}</span></div>
        <div class="week-wrap">${this._week(student)}</div>
      </section>
      <div class="middle-grid">
        ${this._today(student)}
        ${this._activity(student)}
      </div>
      <div class="lower-grid">
        ${this._grades(student)}
        ${this._remarks(student)}
      </div>
    </div>`;
  }

  _bindEvents() {
    this.shadowRoot.querySelector("#refresh")?.addEventListener("click", () => this._refresh());
    this.shadowRoot.querySelectorAll("[data-student]").forEach((button) => {
      button.addEventListener("click", () => {
        this._activeStudentId = button.dataset.student;
        this._render();
      });
    });
  }

  _render() {
    const students = this._data?.students || [];
    const activeStudent = students.find((student) => student.id === this._activeStudentId) || students[0];
    const body = this._error
      ? `<div class="message error-message">Błąd panelu: ${this._e(this._error)}</div>`
      : activeStudent
        ? this._studentView(activeStudent)
        : `<div class="message">Ładowanie danych mojV…</div>`;

    this.shadowRoot.innerHTML = `<style>
      :host {
        display:block;
        min-height:100%;
        color:#f5f8fc;
        background:
          radial-gradient(circle at 12% -20%, rgba(36,130,255,.16), transparent 34%),
          linear-gradient(180deg,#06111c 0%,#081521 52%,#07111a 100%);
        font-family:var(--paper-font-body1_-_font-family, Inter, system-ui, sans-serif);
        --accent:#2d8cff;
        --surface:#0f1b27;
        --surface-2:#132231;
        --surface-3:#182938;
        --line:rgba(255,255,255,.085);
        --muted:#94a3b5;
        --success:#53d769;
        --danger:#ff5f5f;
        --warning:#ffad32;
        --info:#42a5ff;
      }
      * { box-sizing:border-box; }
      button { font:inherit; }
      .shell { max-width:1660px; margin:0 auto; padding:20px 24px 34px; }
      .topbar { min-height:70px; display:flex; align-items:center; justify-content:space-between; gap:20px; }
      .brand { display:flex; align-items:center; gap:14px; min-width:0; }
      .brand img { width:46px; height:46px; object-fit:contain; filter:drop-shadow(0 8px 18px rgba(34,132,255,.18)); }
      .brand-copy { min-width:0; }
      .brand-copy h1 { margin:0; font-size:27px; font-weight:780; letter-spacing:-.02em; }
      .brand-copy div { margin-top:3px; color:var(--muted); font-size:12px; }
      .top-actions { display:flex; align-items:center; gap:12px; color:var(--muted); font-size:12px; white-space:nowrap; }
      .refresh { width:38px; height:38px; display:grid; place-items:center; border:1px solid var(--line); border-radius:11px; background:var(--surface); color:#dbe8f8; cursor:pointer; transition:.18s ease; }
      .refresh:hover { border-color:rgba(45,140,255,.5); transform:translateY(-1px); }
      .student-tabs { display:flex; gap:8px; margin:4px 0 16px; padding:5px; border:1px solid var(--line); border-radius:14px; background:rgba(15,27,39,.88); overflow-x:auto; }
      .student-tab { min-width:180px; border:0; color:#cdd8e6; background:transparent; border-radius:10px; padding:9px 12px; display:flex; align-items:center; gap:9px; text-align:left; cursor:pointer; position:relative; }
      .student-tab::after { content:""; position:absolute; left:12px; right:12px; bottom:-5px; height:2px; border-radius:2px; background:transparent; }
      .student-tab.active { color:white; background:rgba(45,140,255,.08); }
      .student-tab.active::after { background:var(--accent); box-shadow:0 0 16px rgba(45,140,255,.65); }
      .student-tab small { display:block; color:var(--muted); margin-top:2px; font-size:10px; }
      .avatar { width:28px; height:28px; flex:0 0 auto; display:grid; place-items:center; border-radius:50%; color:#d7e9ff; background:linear-gradient(145deg,#1e75d9,#114378); font-weight:800; font-size:12px; }
      .dashboard { display:grid; gap:14px; }
      .panel-card { border:1px solid var(--line); background:linear-gradient(180deg,rgba(17,31,44,.98),rgba(12,24,35,.98)); border-radius:15px; box-shadow:0 18px 45px rgba(0,0,0,.18); overflow:hidden; }
      .card-title { min-height:49px; padding:14px 17px; display:flex; justify-content:space-between; align-items:center; gap:12px; border-bottom:1px solid var(--line); font-size:15px; font-weight:750; }
      .card-title span { color:var(--muted); font-size:11px; font-weight:550; }
      .week-wrap { padding:10px; overflow:auto; }
      .week-grid { display:grid; grid-template-columns:repeat(5,minmax(190px,1fr)); gap:7px; min-width:1010px; }
      .day { border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#0d1924; }
      .day.today { border-color:rgba(45,140,255,.85); box-shadow:0 0 0 1px rgba(45,140,255,.24) inset; }
      .day-head { height:40px; padding:0 11px; display:flex; align-items:center; justify-content:space-between; gap:8px; background:#142331; font-size:11px; }
      .day.today .day-head { background:linear-gradient(180deg,#2789ee,#1b70c7); color:white; }
      .day-head span { color:#93a6bb; }
      .day.today .day-head span { color:#e9f4ff; }
      .day-lessons { padding:5px; display:grid; gap:3px; }
      .week-lesson { min-height:56px; padding:7px 6px; display:grid; grid-template-columns:22px 1fr 20px; gap:6px; align-items:start; border-radius:8px; border:1px solid transparent; }
      .week-lesson:hover { background:#122230; }
      .week-lesson.current { background:linear-gradient(90deg,rgba(45,140,255,.24),rgba(45,140,255,.08)); border-color:rgba(45,140,255,.62); }
      .week-lesson.cancelled { opacity:.47; text-decoration:line-through; }
      .week-number { color:#a7bbcf; font-weight:720; font-size:11px; padding-top:1px; }
      .week-subject { font-weight:700; font-size:11px; line-height:1.28; }
      .week-meta { color:var(--muted); font-size:9.5px; margin-top:4px; line-height:1.35; }
      .change { margin-top:4px; color:var(--warning); font-size:9px; font-weight:700; }
      .attendance-mark { width:20px; height:20px; border-radius:50%; display:grid; place-items:center; font-size:10px; font-weight:900; }
      .middle-grid { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(380px,.95fr); gap:14px; }
      .today-card { min-height:350px; }
      .now-row { padding:19px; display:flex; justify-content:space-between; align-items:center; gap:22px; }
      .now-copy { min-width:0; }
      .section-label { color:var(--accent); font-size:11px; font-weight:720; }
      .now-copy h2 { margin:8px 0 11px; font-size:24px; letter-spacing:-.025em; }
      .lesson-line { display:flex; flex-wrap:wrap; align-items:center; gap:7px 12px; color:#afbdcc; font-size:11px; }
      .lesson-line strong { padding:4px 8px; border-radius:999px; background:rgba(255,255,255,.06); color:#e7edf5; font-size:10px; }
      .teacher { margin-top:8px; color:var(--muted); font-size:11px; }
      .progress-ring { --progress:0deg; width:116px; height:116px; flex:0 0 auto; border-radius:50%; padding:9px; background:conic-gradient(var(--accent) var(--progress),rgba(255,255,255,.07) 0); box-shadow:0 0 24px rgba(45,140,255,.12); }
      .progress-ring > div { width:100%; height:100%; border-radius:50%; display:grid; place-content:center; text-align:center; background:#0f1d29; border:1px solid rgba(255,255,255,.05); }
      .progress-ring strong { font-size:31px; line-height:1; }
      .progress-ring span { display:block; color:var(--muted); margin-top:6px; font-size:9px; }
      .progress-ring.idle { background:rgba(255,255,255,.06); }
      .next-row { margin:0 19px; padding:13px 14px; border:1px solid var(--line); border-radius:11px; background:#101e2a; }
      .next-main { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-top:7px; }
      .next-main span { color:var(--muted); font-size:10px; text-align:right; }
      .status-strip { padding:12px 19px 18px; display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
      .status-tile { min-height:62px; padding:9px 10px; border-radius:10px; border:1px solid var(--line); display:flex; align-items:center; gap:8px; background:#101d29; }
      .status-tile > span { width:26px; height:26px; display:grid; place-items:center; border-radius:50%; font-weight:900; }
      .status-tile small { display:block; color:var(--muted); font-size:9px; margin-bottom:2px; }
      .status-tile strong { font-size:11px; }
      .status-tile.ok > span { color:#07130a; background:var(--success); }
      .status-tile.bad > span { color:white; background:var(--danger); }
      .status-tile.warn > span { color:#1c1200; background:var(--warning); }
      .status-tile.muted > span,.status-tile.neutral > span { color:#dce6ef; background:#263848; }
      .activity-list { padding:4px 14px 12px; }
      .activity-row { min-height:62px; display:grid; grid-template-columns:34px 1fr auto; gap:10px; align-items:center; border-bottom:1px solid var(--line); }
      .activity-row:last-child { border-bottom:0; }
      .activity-icon { width:30px; height:30px; display:grid; place-items:center; border-radius:50%; font-weight:900; }
      .activity-icon.bad { background:var(--danger); color:white; }
      .activity-icon.warn { background:var(--warning); color:#211400; }
      .activity-icon.ok { background:#2c943b; color:white; }
      .activity-icon.info { background:#276fc3; color:white; }
      .activity-copy { min-width:0; }
      .activity-copy strong { display:block; font-size:11px; }
      .activity-copy span { display:block; color:var(--muted); margin-top:3px; font-size:9.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .activity-row time,.compact-row time,.remark-row time { color:#8394a6; font-size:9px; white-space:nowrap; }
      .lower-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
      .compact-list { padding:4px 14px 11px; }
      .compact-row { min-height:50px; display:grid; grid-template-columns:1fr 42px 44px; gap:10px; align-items:center; border-bottom:1px solid var(--line); }
      .compact-row:last-child,.remark-row:last-child { border-bottom:0; }
      .compact-row strong,.remark-row strong { display:block; font-size:11px; }
      .compact-row span,.remark-row span,.remark-row small { display:block; color:var(--muted); margin-top:2px; font-size:9.5px; }
      .grade-value { width:31px; height:31px; display:grid; place-items:center; border-radius:50%; background:#48620f; color:#dfff59; font-weight:850; }
      .remark-row { min-height:58px; display:grid; grid-template-columns:10px 1fr 44px; gap:9px; align-items:center; border-bottom:1px solid var(--line); }
      .remark-dot { width:7px; height:7px; border-radius:50%; background:var(--info); }
      .remark-dot.bad { background:var(--danger); }
      .empty,.message { padding:24px; color:var(--muted); }
      .empty.compact { padding:9px; font-size:10px; }
      .error-message { color:#ffb0b0; }
      @media(max-width:1100px) {
        .middle-grid { grid-template-columns:1fr; }
        .activity-card { min-height:auto; }
      }
      @media(max-width:760px) {
        .shell { padding:10px 10px 24px; }
        .topbar { min-height:62px; }
        .brand img { width:38px; height:38px; }
        .brand-copy h1 { font-size:22px; }
        .top-actions .sync-label { display:none; }
        .student-tab { min-width:150px; padding:8px; }
        .week-grid { min-width:910px; grid-template-columns:repeat(5,174px); }
        .lower-grid { grid-template-columns:1fr; }
        .now-row { align-items:flex-start; padding:15px; }
        .now-copy h2 { font-size:20px; }
        .progress-ring { width:94px; height:94px; padding:7px; }
        .progress-ring strong { font-size:26px; }
        .next-row { margin:0 15px; }
        .status-strip { padding:10px 15px 15px; grid-template-columns:1fr; }
        .status-tile { min-height:52px; }
      }
      @media(max-width:480px) {
        .now-row { display:grid; grid-template-columns:1fr auto; gap:10px; }
        .lesson-line { display:grid; gap:4px; }
        .next-main { align-items:flex-start; flex-direction:column; }
        .next-main span { text-align:left; }
      }
    </style>
    <div class="shell">
      <header class="topbar">
        <div class="brand">
          <img src="/mojv-static/mojv-logo.svg" alt="mojV">
          <div class="brand-copy"><h1>Szkoła</h1><div>mojV · plan, obecność i bieżące informacje</div></div>
        </div>
        <div class="top-actions">
          <span class="sync-label">Ostatnia aktualizacja: ${this._data?.updated_at ? this._time(this._data.updated_at) : "—"}</span>
          <button class="refresh" id="refresh" title="Odśwież" aria-label="Odśwież">↻</button>
        </div>
      </header>
      ${this._studentTabs(students)}
      ${body}
    </div>`;
    this._bindEvents();
  }
}

if (!customElements.get("mojv-school-panel")) {
  customElements.define("mojv-school-panel", MojVSchoolPanel);
}
