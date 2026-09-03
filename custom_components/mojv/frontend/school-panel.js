class MojVSchoolPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._data = null;
    this._timer = null;
    this._error = null;
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

  _date(value) {
    if (!value) return "—";
    return new Date(value).toLocaleDateString([], { day: "2-digit", month: "2-digit", year: "numeric" });
  }

  _attendance(value) {
    const map = {
      present: ["Obecny", "ok"],
      absent: ["Nieobecny", "bad"],
      excused_absence: ["Usprawiedliwiona", "muted"],
      late: ["Spóźniony", "warn"],
      excused_late: ["Spóźnienie usprawiedliwione", "muted"],
      school_activity: ["Zajęcia szkolne", "ok"],
      released: ["Zwolniony", "muted"],
      not_recorded: ["Brak wpisu", "muted"],
    };
    return map[value] || [value || "Brak wpisu", "muted"];
  }

  _week(student) {
    const days = student.week || [];
    if (!days.length) return `<div class="empty">Brak planu tygodniowego</div>`;

    return `<div class="week-grid">${days.map((day) => {
      const lessons = (day.lessons || []).map((lesson) => {
        const [, cls] = this._attendance(lesson.attendance);
        const attendanceMark = lesson.attendance === "present" ? "✓" :
          lesson.attendance === "absent" ? "✕" :
          lesson.attendance === "late" ? "!" : "";
        return `<div class="week-lesson ${lesson.current ? "current" : ""} ${lesson.cancelled ? "cancelled" : ""}">
          <div class="week-num">${this._e(lesson.number)}</div>
          <div class="week-main">
            <div class="week-subject">${this._e(lesson.subject)}</div>
            <div class="small">${this._time(lesson.start)}–${this._time(lesson.end)}</div>
            <div class="small">${this._e(lesson.room || "bez sali")}</div>
          </div>
          ${attendanceMark ? `<div class="attendance-dot ${cls}" title="${this._e(this._attendance(lesson.attendance)[0])}">${attendanceMark}</div>` : ""}
        </div>`;
      }).join("");
      return `<div class="day ${day.today ? "today" : ""}">
        <div class="day-head"><strong>${this._e(day.label)}</strong><span>${this._e(day.date.slice(5))}</span></div>
        <div class="day-lessons">${lessons || `<div class="empty compact">Brak lekcji</div>`}</div>
      </div>`;
    }).join("")}</div>`;
  }

  _student(student) {
    const current = student.current;
    const alerts = [];
    if (current?.attendance === "absent") alerts.push(["Nieobecność na trwającej lekcji", "bad"]);
    if (current?.attendance === "late") alerts.push(["Spóźnienie na trwającą lekcję", "warn"]);
    if (current && current.minutes_to_end >= 0 && current.minutes_to_end <= 5) {
      alerts.push([`Koniec lekcji za ${current.minutes_to_end} min`, "info"]);
    }

    const grades = student.grades.length
      ? student.grades.map((grade) => `<div class="item-row">
          <div><strong>${this._e(grade.subject)}</strong><div class="small">${this._date(grade.date)} · ${this._e(grade.description)}</div></div>
          <div class="grade">${this._e(grade.value)}</div>
        </div>`).join("")
      : `<div class="empty">Brak ocen do pokazania</div>`;

    const remarks = student.remarks.length
      ? student.remarks.map((remark) => `<div class="remark">
          <div class="remark-head">${this._e(remark.category || "Uwaga")} · ${this._date(remark.date)}</div>
          <div>${this._e(remark.text)}</div>
          <div class="small">${this._e(remark.author)}</div>
        </div>`).join("")
      : `<div class="empty">Brak uwag do pokazania</div>`;

    const currentBlock = current
      ? `<div class="now-card">
          <div><span class="eyebrow">TERAZ · LEKCJA ${this._e(current.number)}</span><h3>${this._e(current.subject)}</h3>
          <div class="small">${this._time(current.start)}–${this._time(current.end)} · ${this._e(current.room || "bez sali")}</div></div>
          <div class="countdown">${this._e(current.minutes_to_end)}<span> min</span></div>
        </div>`
      : `<div class="now-card"><div><span class="eyebrow">TERAZ</span><h3>Przerwa / brak lekcji</h3></div></div>`;

    const nextBlock = student.next
      ? `<div class="next">Następna: <strong>${this._e(student.next.subject)}</strong> · ${this._time(student.next.start)} · ${this._e(student.next.room || "bez sali")}</div>`
      : `<div class="next">Brak kolejnej lekcji</div>`;

    const alertBlock = alerts.length
      ? `<div class="alerts">${alerts.map(([text, cls]) => `<div class="alert ${cls}">${this._e(text)}</div>`).join("")}</div>`
      : "";

    return `<section class="student-card">
      <header class="student-head"><div><h2>${this._e(student.name)}</h2><span>${this._e(student.class)}</span></div></header>
      <div class="section-title">Pełny plan lekcji</div>
      <div class="week-wrap">${this._week(student)}</div>
      <div class="below">
        ${alertBlock}
        ${currentBlock}
        ${nextBlock}
        <div class="two-cols">
          <div><div class="section-title">Oceny</div><div class="list">${grades}</div></div>
          <div><div class="section-title">Uwagi</div><div class="list">${remarks}</div></div>
        </div>
      </div>
    </section>`;
  }

  _render() {
    const students = this._data?.students || [];
    const body = this._error
      ? `<div class="message bad-text">Błąd panelu: ${this._e(this._error)}</div>`
      : students.length
        ? `<div class="students">${students.map((s) => this._student(s)).join("")}</div>`
        : `<div class="message">Ładowanie danych mojV…</div>`;

    this.shadowRoot.innerHTML = `<style>
      :host { display:block; min-height:100%; background:var(--primary-background-color); color:var(--primary-text-color); font-family:var(--paper-font-body1_-_font-family, sans-serif); }
      * { box-sizing:border-box; }
      .page { max-width:1800px; margin:0 auto; padding:20px; }
      .top { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:18px; }
      .top h1 { margin:0; font-size:28px; }
      .sync { color:var(--secondary-text-color); font-size:12px; }
      button { border:0; border-radius:10px; padding:10px 14px; background:var(--primary-color); color:white; cursor:pointer; }
      .students { display:grid; grid-template-columns:repeat(auto-fit,minmax(620px,1fr)); gap:18px; align-items:start; }
      .student-card { background:var(--card-background-color); border-radius:16px; box-shadow:var(--ha-card-box-shadow); overflow:hidden; border:1px solid var(--divider-color); }
      .student-head { padding:18px 20px 12px; }
      .student-head h2 { margin:0; font-size:22px; }
      .student-head span { color:var(--secondary-text-color); }
      .section-title { padding:12px 20px 8px; text-transform:uppercase; font-size:11px; letter-spacing:.12em; color:var(--secondary-text-color); font-weight:700; }
      .week-wrap { padding:0 12px 14px; overflow-x:auto; }
      .week-grid { display:grid; grid-template-columns:repeat(5,minmax(145px,1fr)); gap:8px; min-width:760px; }
      .day { border:1px solid var(--divider-color); border-radius:12px; overflow:hidden; background:var(--secondary-background-color); }
      .day.today { border-color:var(--primary-color); box-shadow:0 0 0 1px var(--primary-color) inset; }
      .day-head { padding:9px 10px; display:flex; justify-content:space-between; gap:5px; background:color-mix(in srgb,var(--primary-color) 7%,transparent); font-size:12px; }
      .day.today .day-head { background:color-mix(in srgb,var(--primary-color) 17%,transparent); }
      .day-head span { color:var(--secondary-text-color); }
      .day-lessons { padding:5px; display:grid; gap:4px; }
      .week-lesson { display:grid; grid-template-columns:22px 1fr 20px; gap:5px; padding:7px 5px; border-radius:8px; align-items:start; }
      .week-lesson.current { background:color-mix(in srgb,var(--primary-color) 18%,transparent); outline:1px solid var(--primary-color); }
      .week-lesson.cancelled { opacity:.5; text-decoration:line-through; }
      .week-num { color:var(--primary-color); font-weight:800; text-align:center; }
      .week-subject { font-weight:700; font-size:12px; line-height:1.2; }
      .attendance-dot { width:20px; height:20px; border-radius:50%; display:grid; place-items:center; font-size:11px; font-weight:800; }
      .meta,.teacher,.small { color:var(--secondary-text-color); font-size:11px; margin-top:2px; }
      .ok { background:rgba(46,125,50,.15); color:var(--success-color,#2e7d32); }
      .bad { background:rgba(211,47,47,.15); color:var(--error-color,#d32f2f); }
      .warn { background:rgba(245,124,0,.15); color:#ef6c00; }
      .muted { background:var(--secondary-background-color); color:var(--secondary-text-color); }
      .below { border-top:1px solid var(--divider-color); padding-bottom:14px; }
      .alerts { padding:14px 20px 0; display:grid; gap:8px; }
      .alert { padding:10px 12px; border-radius:10px; font-weight:700; }
      .alert.bad { background:rgba(211,47,47,.12); border-left:4px solid var(--error-color,#d32f2f); }
      .alert.warn { background:rgba(245,124,0,.12); border-left:4px solid #ef6c00; }
      .alert.info { background:rgba(3,169,244,.12); border-left:4px solid #039be5; }
      .now-card { margin:14px 20px 6px; padding:16px; border-radius:12px; background:var(--secondary-background-color); display:flex; justify-content:space-between; align-items:center; gap:12px; }
      .now-card h3 { margin:4px 0; font-size:20px; }
      .eyebrow { font-size:10px; letter-spacing:.12em; color:var(--secondary-text-color); }
      .countdown { font-size:34px; font-weight:800; color:var(--primary-color); white-space:nowrap; }
      .countdown span { font-size:12px; font-weight:500; color:var(--secondary-text-color); }
      .next { margin:0 20px 8px; color:var(--secondary-text-color); }
      .two-cols { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
      .list { padding:0 20px; display:grid; gap:8px; }
      .item-row,.remark { padding:11px 12px; border-radius:10px; background:var(--secondary-background-color); }
      .item-row { display:flex; justify-content:space-between; align-items:center; gap:12px; }
      .grade { font-size:24px; font-weight:800; color:var(--primary-color); }
      .remark-head { font-size:11px; font-weight:700; color:var(--secondary-text-color); margin-bottom:5px; text-transform:uppercase; }
      .empty,.message { padding:18px 20px; color:var(--secondary-text-color); }
      .empty.compact { padding:8px; font-size:11px; }
      .bad-text { color:var(--error-color,#d32f2f); }
      @media(max-width:760px) { .page{padding:10px}.students{grid-template-columns:1fr}.two-cols{grid-template-columns:1fr}.top h1{font-size:23px}.week-wrap{padding-left:8px;padding-right:8px} }
    </style>
    <div class="page">
      <div class="top"><div><h1>Szkoła</h1><div class="sync">${this._data?.updated_at ? `Aktualizacja: ${this._time(this._data.updated_at)}` : ""}</div></div><button id="refresh">Odśwież</button></div>
      ${body}
    </div>`;
    this.shadowRoot.querySelector("#refresh")?.addEventListener("click", () => this._refresh());
  }
}

if (!customElements.get("mojv-school-panel")) {
  customElements.define("mojv-school-panel", MojVSchoolPanel);
}
