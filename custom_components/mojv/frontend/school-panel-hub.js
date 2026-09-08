import "./school-panel-hub-base.js?v=0.15.14";
import "./school-panel-details.js?v=0.15.14";
import "./school-panel-lesson-states.js?v=0.15.14";
import "./school-panel-custom-schedule.js?v=0.15.14";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvExpandedSchoolHubPatched) {
  proto.__mojvExpandedSchoolHubPatched = true;

  const baseConnectedCallback = proto.connectedCallback;
  const baseAvailableViews = proto._availableViews;
  const baseRenderActiveView = proto._renderActiveView;
  const baseRenderDashboard = proto._renderDashboard;
  const baseRenderMessages = proto._renderMessages;
  const baseRenderAttendance = proto._renderAttendance;
  const baseRenderAttendanceStats = proto._renderAttendanceStats;
  const baseStyles = proto._styles;

  proto._mojvEnsureView = function (views, view, afterId = "") {
    if (views.some(([id]) => id === view[0])) return views;
    const index = afterId ? views.findIndex(([id]) => id === afterId) : -1;
    if (index >= 0) views.splice(index + 1, 0, view);
    else views.push(view);
    return views;
  };

  proto.connectedCallback = function () {
    const result = baseConnectedCallback.call(this);
    if (this._topicsSortDirection !== "asc" && this._topicsSortDirection !== "desc") {
      this._topicsSortDirection = "desc";
    }
    if (!this.__mojvUsabilityEventsBound) {
      this.__mojvUsabilityEventsBound = true;
      this.shadowRoot.addEventListener("click", (event) => {
        const printButton = event.target.closest?.("[data-mojv-print]");
        if (printButton) {
          event.preventDefault();
          this._printPanel(printButton.dataset.mojvPrint);
          return;
        }
        const customizeButton = event.target.closest?.("[data-mojv-customize-modules]");
        if (customizeButton) {
          event.preventDefault();
          this._mojvOpenModuleSettings();
          return;
        }
        const scheduleExtras = event.target.closest?.("[data-mojv-toggle-schedule-extras]");
        if (scheduleExtras) {
          event.preventDefault();
          this.shadowRoot.querySelector("[data-mojv-schedule-extras]")?.classList.toggle("open");
          return;
        }
        const deleteTemplate = event.target.closest?.("[data-mojv-delete-template]");
        if (deleteTemplate) {
          event.preventDefault();
          this._mojvDeleteCommunicationTemplate(deleteTemplate.dataset.mojvDeleteTemplate);
          return;
        }
        const replyButton = event.target.closest?.("[data-mojv-reply-message]");
        if (replyButton) {
          event.preventDefault();
          this._mojvOpenReplyDialog(replyButton.dataset.mojvReplyMessage);
          return;
        }
        const sortButton = event.target.closest?.("[data-topics-sort]");
        if (sortButton) {
          event.preventDefault();
          this._topicsSortDirection = this._topicsSortDirection === "asc" ? "desc" : "asc";
          if (this._activeView === "topics") this._renderActiveView();
        }
      });
      this.shadowRoot.addEventListener("submit", async (event) => {
        if (!(event.target instanceof HTMLFormElement) || event.target.dataset.mojvCommunicationTemplate !== "true") return;
        event.preventDefault();
        const form = event.target;
        const submit = form.querySelector("button[type=submit]");
        if (submit) submit.disabled = true;
        try {
          const values = new FormData(form);
          await this._hass.callWS({ type: "mojv/communication_templates", action: "add", template: {
            student_id: this._activeStudentId || "",
            kind: String(values.get("kind") || "excuse"),
            name: String(values.get("name") || ""),
            body: String(values.get("body") || ""),
          }});
          form.reset();
          await this._refresh();
        } catch (error) {
          const errorBox = form.querySelector("[data-mojv-template-error]");
          if (errorBox) errorBox.textContent = `Nie zapisano: ${String(error)}`;
        } finally {
          if (submit) submit.disabled = false;
        }
      });
      this.shadowRoot.addEventListener("submit", async (event) => {
        if (!(event.target instanceof HTMLFormElement) || event.target.dataset.mojvSendReply !== "true") return;
        event.preventDefault();
        const form = event.target;
        const body = String(new FormData(form).get("body") || "").trim();
        const messageId = String(form.dataset.mojvMessageId || "");
        const confirmed = form.querySelector("input[name=confirmed]")?.checked;
        const errorBox = form.querySelector("[data-mojv-send-error]");
        if (!body || !messageId || !confirmed) {
          if (errorBox) errorBox.textContent = "Wpisz treść i zaznacz potwierdzenie.";
          return;
        }
        if (!window.confirm("Wysłać tę odpowiedź do szkoły? Tej operacji nie można cofnąć.")) return;
        const submit = form.querySelector("button[type=submit]");
        if (submit) submit.disabled = true;
        try {
          await this._hass.callWS({ type: "mojv/send_reply", student_id: this._activeStudentId || "", message_id: messageId, body, confirmed: true });
          this._closeMojvReplyDialog();
          await this._refresh();
        } catch (error) {
          if (errorBox) errorBox.textContent = `Nie wysłano: ${String(error)}`;
        } finally {
          if (submit) submit.disabled = false;
        }
      });
    }
    return result;
  };

  proto._availableViews = function (student) {
    const views = baseAvailableViews.call(this, student).filter(([id]) => !["info", "topics"].includes(id));

    this._mojvEnsureView(views, ["grades", "Oceny", "5"], "attendance");
    this._mojvEnsureView(views, ["messages", "Wiadomości", "✉"], "schoolwork");
    this._mojvEnsureView(views, ["meetings", "Zebrania", "◷"], "messages");
    this._mojvEnsureView(views, ["remarks", "Uwagi", "!"], "meetings");
    this._mojvEnsureView(views, ["praises", "Pochwały", "★"], "remarks");
    this._mojvEnsureView(views, ["workspace", "Mój widok", "▣"], "praises");
    this._mojvEnsureView(views, ["communication", "Korespondencja", "✎"], "messages");

    const hasInfo = Boolean(
      student?.school_info ||
      (student?.teachers || []).length ||
      (student?.homeroom_teachers || []).length ||
      (student?.free_days || []).length ||
      student?.excuses?.active ||
      student?.excuses?.blocked ||
      (student?.excuses?.entries || []).length
    );
    if ((student?.completed_lessons || []).length) {
      views.push(["topics", "Tematy", "≡"]);
    }
    if (hasInfo) {
      views.push(["info", "Informacje", "ⓘ"]);
    }
    return views;
  };

  proto._renderMessages = function (student) {
    const rows = [...(student?.messages || [])].sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card list-view-card" data-view="messages"><div class="section-head"><div><span class="kicker">Wiadomości</span><h2>Skrzynka</h2></div><span>${rows.length}</span></div>${rows.length ? `<div class="data-list">${rows.map((item) => `<article class="data-row"><span class="remark-badge">✉</span><div><strong>${this._e(item.subject || "Bez tematu")}</strong><span>${this._e(item.sender || "")}</span><small>${this._e(item.body || "")}</small></div><div class="message-actions"><time>${this._e(this._date(item.date, true))}</time><button type="button" class="mojv-print-button" data-mojv-reply-message="${this._e(item.id)}">Odpowiedz</button></div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak wiadomości.</div>`}</section>`;
  };

  proto._renderAttendance = function (student) {
    const base = baseRenderAttendance ? baseRenderAttendance.call(this, student) : "";
    const legend = [
      ["O", "Obecność", "ok"], ["N", "Nieobecność", "bad"], ["NU", "Nieobecność usprawiedliwiona", "muted"],
      ["NS", "Nieobecność z przyczyn szkolnych", "ok"], ["S", "Spóźnienie", "warn"], ["SU", "Spóźnienie usprawiedliwione", "muted"],
      ["Z", "Zwolnienie", "muted"], ["UW", "Usprawiedliwienie oczekuje na zatwierdzenie", "warn"], ["UZ", "Usprawiedliwienie zatwierdzone", "ok"], ["UO", "Usprawiedliwienie odrzucone", "bad"],
    ];
    return `<div class="mojv-print-toolbar"><button type="button" class="mojv-print-button" data-mojv-print="statistics">Drukuj statystyki</button></div>${base}<section class="attendance-legend" aria-label="Legenda frekwencji"><span>Legenda</span>${legend.map(([code, label, state]) => `<button type="button" class="attendance-legend-dot ${state}" title="${this._e(label)}" aria-label="${this._e(label)}">${code}</button>`).join("")}</section>`;
  };

  proto._renderAttendanceStats = function (student) {
    const base = baseRenderAttendanceStats ? baseRenderAttendanceStats.call(this, student) : "";
    return `<div class="mojv-print-toolbar"><button type="button" class="mojv-print-button" data-mojv-print="attendance-stats">Drukuj statystyki</button></div>${base}`;
  };

  proto._renderActiveView = function () {
    const content = this.shadowRoot.querySelector("#view-content");
    const student = this._activeStudent();
    if (!content || !student || this._error) return baseRenderActiveView.call(this);
    this._mojvApplyDisplaySettings();

    switch (this._activeView) {
      case "info":
        content.innerHTML = this._renderSchoolInfo(student);
        return;
      case "topics":
        content.innerHTML = this._renderCompletedTopics(student);
        return;
      case "communication":
        content.innerHTML = this._renderCommunication(student);
        return;
      case "praises":
        content.innerHTML = this._renderPraises(student);
        return;
      case "workspace":
        content.innerHTML = this._renderWorkspace();
        return;
      default:
        return baseRenderActiveView.call(this);
    }
  };

  proto._renderDashboardForStudent = function (student) {
    const base = baseRenderDashboard.call(this, student);
    const dashboard = student?.dashboard || {};
    const lucky_number = dashboard.lucky_number;
    const important_today = dashboard.important_today || [];
    const next_free_day = dashboard.next_free_day;
    if (!lucky_number && !important_today.length && !next_free_day) return base;

    const important = important_today.length
      ? `<div class="expanded-important-list">${important_today.map((item, index) => {
        const preview = this._detailPreview(item.description, 120);
        return `<button type="button" class="expanded-important-row mojv-detail-trigger" data-mojv-detail-kind="important" data-mojv-detail-index="${index}" aria-label="Pokaż szczegóły: ${this._e(item.title || item.kind || "Ważne")}"><strong>${this._e(item.title || item.kind || "Ważne")}</strong>${item.subject ? `<span>${this._e(item.subject)}</span>` : ""}${preview ? `<small>${this._e(preview)}</small>` : ""}</button>`;
      }).join("")}</div>`
      : `<span class="expanded-muted">Brak dodatkowych wpisów na dziś.</span>`;
    const extra = `<section class="card expanded-today-card">
      <div class="section-head"><div><span class="kicker">Dzisiaj</span><h2>Ważne informacje</h2></div></div>
      <div class="expanded-today-grid">
        <div><small>Szczęśliwy numerek</small><strong>${this._e(lucky_number?.value || "—")}</strong>${lucky_number?.date ? `<span>${this._e(this._date(lucky_number.date, true))}</span>` : ""}</div>
        <div><small>Najbliższy dzień wolny</small><strong>${this._e(next_free_day?.name || "—")}</strong>${next_free_day?.start ? `<span>${this._e(this._date(next_free_day.start, true))}</span>` : ""}</div>
      </div>
      ${important}
    </section>`;
    return base.replace(/<\/div>\s*$/, `${extra}</div>`);
  };

  proto._mojvModuleKeys = function () {
    return ["agenda", "grades", "schoolwork", "attendance", "important", "messages", "notifications", "meetings", "praises", "remarks", "announcements", "meal", "duties"];
  };

  proto._mojvVisibleModules = function () {
    try {
      const stored = JSON.parse(localStorage.getItem("mojv.visible_modules") || "null");
      if (Array.isArray(stored)) return new Set(stored);
    } catch (_error) { /* use the complete default layout */ }
    return new Set(this._mojvModuleKeys());
  };

  proto._mojvSaveVisibleModules = function (enabled) {
    localStorage.setItem("mojv.visible_modules", JSON.stringify([...enabled]));
  };

  proto._mojvDisplaySettings = function () {
    try { return JSON.parse(localStorage.getItem("mojv.display_settings") || "{}") || {}; } catch (_error) { return {}; }
  };

  proto._mojvApplyDisplaySettings = function () {
    const settings = this._mojvDisplaySettings();
    const student = this._activeStudent();
    const theme = settings.themes?.[student?.id] || "system";
    const scale = Number(settings.fontScale) || 1.12;
    this.style.setProperty("--mojv-font-scale", String(Math.min(1.45, Math.max(0.9, scale))));
    this.dataset.mojvTheme = theme;
  };

  proto._mojvGradeSummary = function (student) {
    const buckets = new Map();
    for (const grade of student.grades || []) {
      const value = Number(String(grade.value || "").replace(",", ".").match(/[1-6](?:\.\d+)?/)?.[0]);
      if (!Number.isFinite(value)) continue;
      const weight = Math.max(1, Number(String(grade.weight || "").replace(",", ".")) || 1);
      const row = buckets.get(grade.subject) || { subject: grade.subject, sum: 0, weight: 0, newest: 0, marks: [] };
      row.sum += value * weight;
      row.weight += weight;
      const dated = new Date(grade.date).getTime();
      row.newest = Math.max(row.newest, Number.isFinite(dated) ? dated : 0);
      row.marks.push({ value, date: Number.isFinite(dated) ? dated : 0 });
      buckets.set(grade.subject, row);
    }
    return [...buckets.values()].map((row) => {
      const marks = row.marks.sort((a, b) => a.date - b.date);
      const change = marks.length >= 2 ? marks.at(-1).value - marks.at(-2).value : 0;
      return { ...row, average: row.sum / row.weight, trend: change > 0 ? "up" : change < 0 ? "down" : "flat" };
    }).sort((a, b) => a.average - b.average || b.newest - a.newest);
  };

  proto._mojvAgendaRows = function (student) {
    const now = this._dayStart(new Date());
    const limit = new Date(now); limit.setDate(limit.getDate() + 7);
    const rows = [];
    for (const day of this._weekDays(student, 0)) {
      for (const lesson of [...(day.lessons || []), ...this._customLessonsForDay(student, day.date)]) {
        const start = new Date(lesson.start);
        if (start >= now && start < limit) rows.push({ date: start, kind: lesson.custom ? "Własne zajęcia" : "Lekcja", title: lesson.subject, detail: `${this._time(lesson.start)}–${this._time(lesson.end)}${lesson.room ? ` · ${lesson.room}` : ""}` });
      }
    }
    for (const item of student.schoolwork || []) {
      const date = new Date(item.date);
      if (date >= now && date < limit) rows.push({ date, kind: this._workKind(item.kind), title: item.title || this._workKind(item.kind), detail: item.subject || "" });
    }
    for (const item of student.meetings || []) {
      const date = new Date(item.start);
      if (date >= now && date < limit) rows.push({ date, kind: "Zebranie", title: item.title || "Zebranie", detail: item.location || "" });
    }
    return rows.sort((a, b) => a.date - b.date).slice(0, 12);
  };

  proto._renderDashboard = function (student) {
    this._mojvApplyDisplaySettings();
    const visible = this._mojvVisibleModules();
    const agenda = this._mojvAgendaRows(student);
    const grades = this._mojvGradeSummary(student);
    const dashboard = student.dashboard || {};
    const cards = [];
    if (visible.has("agenda")) cards.push(`<section class="card modular-card modular-agenda"><div class="section-head"><div><span class="kicker">Najbliższe 7 dni</span><h2>Agenda tygodnia</h2></div><span>${agenda.length}</span></div>${agenda.length ? `<div class="modular-list">${agenda.map((item) => `<article><time>${this._e(this._date(item.date, true))}<small>${this._time(item.date)}</small></time><div><small>${this._e(item.kind)}</small><strong>${this._e(item.title)}</strong>${item.detail ? `<span>${this._e(item.detail)}</span>` : ""}</div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak zajęć i terminów w najbliższych 7 dniach.</div>`}</section>`);
    if (visible.has("grades")) cards.push(`<section class="card modular-card"><div class="section-head"><div><span class="kicker">Oceny</span><h2>Średnie i trend</h2></div><span>${grades.length}</span></div>${grades.length ? `<div class="grade-trend-grid">${grades.map((item) => `<article class="${item.average < 3 ? "needs-attention" : ""}"><strong>${this._e(item.subject)}</strong><span>${item.average.toFixed(2)} <small title="Trend dwóch ostatnich ocen">${item.trend === "up" ? "↗" : item.trend === "down" ? "↘" : "→"}</small></span><small>średnia ważona</small></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak ocen liczbowych do wyliczenia średniej.</div>`}</section>`);
    if (visible.has("schoolwork")) {
      const upcoming = (student.schoolwork || []).filter((item) => new Date(item.date) >= this._dayStart(new Date())).sort((a, b) => new Date(a.date) - new Date(b.date)).slice(0, 4);
      cards.push(`<section class="card modular-card"><div class="section-head"><div><span class="kicker">Terminarz</span><h2>Najbliższe zadania</h2></div><span>${upcoming.length}</span></div>${upcoming.length ? `<div class="modular-list">${upcoming.map((item) => `<article><time>${this._e(this._date(item.date, true))}</time><div><small>${this._e(item.subject)}</small><strong>${this._e(item.title || this._workKind(item.kind))}</strong></div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak nadchodzących zadań.</div>`}</section>`);
    }
    if (visible.has("attendance")) cards.push(`<section class="card modular-card"><div class="section-head"><div><span class="kicker">Frekwencja</span><h2>Na dziś</h2></div></div><div class="modular-metrics"><div><small>Obecności</small><strong>${Number(student.attendance_summary?.present || 0)}</strong></div><div><small>Nieobecności</small><strong>${Number(student.attendance_summary?.absent || 0)}</strong></div><div><small>Spóźnienia</small><strong>${Number(student.attendance_summary?.late || 0)}</strong></div></div></section>`);
    const simpleCard = (key, kicker, title, rows, empty) => visible.has(key) ? `<section class="card modular-card"><div class="section-head"><div><span class="kicker">${kicker}</span><h2>${title}</h2></div><span>${rows.length}</span></div>${rows.length ? `<div class="modular-list">${rows.map((row) => `<article><div><strong>${this._e(row.title)}</strong>${row.detail ? `<span>${this._e(row.detail)}</span>` : ""}</div></article>`).join("")}</div>` : `<div class="mini-empty roomy">${empty}</div>`}</section>` : "";
    cards.push(simpleCard("messages", "Wiadomości", "Skrzynka", (student.messages || []).slice(0, 3).map((item) => ({ title: item.subject || "Bez tematu", detail: item.sender || "" })), "Brak wiadomości."));
    cards.push(simpleCard("notifications", "Powiadomienia", "Ostatnie", (student.notifications || []).slice(0, 3).map((item) => ({ title: item.title || "Powiadomienie", detail: item.message || item.kind || "" })), "Brak powiadomień."));
    cards.push(simpleCard("meetings", "Zebrania", "Najbliższe", (student.meetings || []).slice(0, 3).map((item) => ({ title: item.title || "Zebranie", detail: item.description || item.location || "" })), "Brak zebrań."));
    cards.push(simpleCard("praises", "Wychowanie", "Pochwały", (student.remarks || []).filter((item) => item.kind === "positive" || item.kind === "praise").slice(0, 3).map((item) => ({ title: item.category || "Pochwała", detail: item.text || "" })), "Brak pochwał."));
    cards.push(simpleCard("remarks", "Wychowanie", "Uwagi", (student.remarks || []).filter((item) => item.kind !== "positive" && item.kind !== "praise").slice(0, 3).map((item) => ({ title: item.category || "Uwaga", detail: item.text || "" })), "Brak uwag."));
    if (visible.has("important") && (dashboard.lucky_number || (dashboard.important_today || []).length || dashboard.next_free_day)) cards.push(`<section class="card modular-card"><div class="section-head"><div><span class="kicker">Informacje</span><h2>Ważne dzisiaj</h2></div></div><div class="modular-list">${dashboard.lucky_number ? `<article><time>★</time><div><small>Szczęśliwy numerek</small><strong>${this._e(dashboard.lucky_number.value)}</strong></div></article>` : ""}${(dashboard.important_today || []).map((item) => `<article><time>!</time><div><small>${this._e(item.subject || item.kind || "Informacja")}</small><strong>${this._e(item.title || "Ważne")}</strong></div></article>`).join("")}${dashboard.next_free_day ? `<article><time>◷</time><div><small>Dzień wolny</small><strong>${this._e(dashboard.next_free_day.name)}</strong></div></article>` : ""}</div></section>`);
    const optional = [["announcements", "Ogłoszenia", student.announcements], ["meal", "Jadłospis", student.meal], ["duties", "Dyżurni", student.duties]];
    for (const [key, label, data] of optional) if (visible.has(key) && ((Array.isArray(data) && data.length) || (data && !Array.isArray(data)))) cards.push(`<section class="card modular-card"><div class="section-head"><div><span class="kicker">Szkoła</span><h2>${label}</h2></div></div><div class="modular-list">${(Array.isArray(data) ? data : [data]).map((item) => `<article><div><strong>${this._e(typeof item === "string" ? item : item.title || item.name || "Wpis")}</strong>${typeof item === "object" && item.detail ? `<span>${this._e(item.detail)}</span>` : ""}</div></article>`).join("")}</div></section>`);
    const settings = this._mojvDisplaySettings();
    const color = settings.studentColors?.[student.id] || "#3f8cff";
    return `<div class="modular-dashboard" style="--mojv-student-color:${this._e(color)}"><div class="modular-toolbar"><div><span class="kicker"><span class="student-initial">${this._e((student.name || "?").trim().charAt(0))}</span> Twój układ</span><h2>${this._e(student.name || "Szkoła")}</h2></div><button type="button" class="mojv-print-button" data-mojv-customize-modules="true">Dostosuj karty</button></div><div class="modular-grid">${cards.length ? cards.join("") : `<div class="mini-empty roomy">Włącz przynajmniej jedną kartę w ustawieniach widoku.</div>`}</div></div>`;
  };

  proto._renderDashboard = function (student) {
    this._mojvApplyDisplaySettings();
    const settings = this._mojvDisplaySettings();
    const ids = Array.isArray(settings.dashboardStudents) ? settings.dashboardStudents : [];
    const students = (this._data?.students || []).filter((item) => ids.includes(item.id));
    if (!students.length) return this._renderDashboardForStudent(student);
    if (students.length === 1) return this._renderDashboardForStudent(students[0]);
    return `<div class="modular-dashboard-family">${students.map((item) => this._renderDashboardForStudent(item)).join("")}</div>`;
  };

  proto._mojvOpenModuleSettings = function () {
    this.shadowRoot.querySelector("[data-mojv-module-settings]")?.remove();
    const enabled = this._mojvVisibleModules();
    const labels = { agenda: "Agenda tygodnia", grades: "Średnie ocen", schoolwork: "Terminarz", attendance: "Frekwencja", important: "Ważne dzisiaj", messages: "Wiadomości", notifications: "Powiadomienia", meetings: "Zebrania", praises: "Pochwały", remarks: "Uwagi", announcements: "Ogłoszenia", meal: "Jadłospis", duties: "Dyżurni" };
    const settings = this._mojvDisplaySettings();
    const overlay = document.createElement("div");
    overlay.className = "mojv-module-overlay"; overlay.dataset.mojvModuleSettings = "true";
    const students = this._data?.students || [];
    const selectedIds = Array.isArray(settings.dashboardStudents) ? settings.dashboardStudents : [];
    const showAll = students.length > 1 && selectedIds.length === students.length && students.every((item) => selectedIds.includes(item.id));
    const showActive = !selectedIds.length;
    overlay.innerHTML = `<div class="mojv-custom-backdrop" data-mojv-close-modules="true"></div><section class="mojv-module-dialog" role="dialog" aria-modal="true"><div class="mojv-custom-head"><div><span class="kicker">Ustawienia pulpitu</span><h2>Układ, dzieci i wygląd</h2></div><button type="button" class="icon-button" data-mojv-close-modules="true" aria-label="Zamknij">×</button></div><form><div class="module-choice-list">${this._mojvModuleKeys().map((key) => `<label><input type="checkbox" value="${key}" ${enabled.has(key) ? "checked" : ""}>${labels[key]}</label>`).join("")}</div><fieldset class="student-choice-list"><legend>Pokaż na pulpicie</legend><label><input type="checkbox" name="dashboardActive" ${showActive ? "checked" : ""}> aktywne dziecko</label><label><input type="checkbox" name="dashboardAll" ${showAll ? "checked" : ""}> wszystkie dzieci</label>${students.map((item) => `<label><input type="checkbox" name="dashboardStudent" value="${this._e(item.id)}" ${selectedIds.includes(item.id) ? "checked" : ""}><span class="student-initial" style="--mojv-student-color:${this._e(settings.studentColors?.[item.id] || "#3f8cff")}">${this._e((item.name || "?").trim().charAt(0))}</span>${this._e(item.name)} <input type="color" name="studentColor" value="${this._e(settings.studentColors?.[item.id] || "#3f8cff")}" data-student-color="${this._e(item.id)}" aria-label="Kolor ${this._e(item.name)}"></label>`).join("")}</fieldset><div class="display-choice-list"><label>Wielkość tekstu <output data-mojv-font-output>${Math.round((Number(settings.fontScale) || 1.12) * 100)}%</output><input name="fontScale" type="range" min="0.9" max="1.45" step="0.05" value="${Number(settings.fontScale) || 1.12}"></label><label>Motyw dla ${this._e(this._activeStudent()?.name || "ucznia")}<select name="theme"><option value="system">systemowy</option><option value="blue">niebieski</option><option value="warm">ciepły</option><option value="dark">ciemny</option></select></label></div><div class="mojv-custom-actions"><button type="submit" class="mojv-custom-primary">Zapisz układ</button></div></form></section>`;
    overlay.querySelector("select[name=theme]").value = settings.themes?.[this._activeStudentId] || "system";
    overlay.addEventListener("click", (event) => { if (event.target.closest?.("[data-mojv-close-modules]")) overlay.remove(); });
    overlay.querySelector("input[name=fontScale]").addEventListener("input", (event) => { overlay.querySelector("[data-mojv-font-output]").textContent = `${Math.round(Number(event.target.value) * 100)}%`; });
    overlay.querySelector("form").addEventListener("submit", (event) => { event.preventDefault(); const next = new Set([...overlay.querySelectorAll(".module-choice-list input:checked")].map((input) => input.value)); const form = new FormData(event.currentTarget); const latest = this._mojvDisplaySettings(); latest.fontScale = Number(form.get("fontScale")) || 1.12; latest.themes = latest.themes || {}; latest.themes[this._activeStudentId] = String(form.get("theme") || "system"); latest.dashboardStudents = form.get("dashboardAll") ? students.map((item) => item.id) : form.get("dashboardActive") ? [] : [...overlay.querySelectorAll("input[name=dashboardStudent]:checked")].map((input) => input.value); latest.studentColors = latest.studentColors || {}; overlay.querySelectorAll("input[data-student-color]").forEach((input) => { latest.studentColors[input.dataset.studentColor] = input.value; }); localStorage.setItem("mojv.display_settings", JSON.stringify(latest)); this._mojvSaveVisibleModules(next); overlay.remove(); this._renderActiveView(); });
    this.shadowRoot.append(overlay);
  };

  proto._mojvDeleteCommunicationTemplate = async function (templateId) {
    if (!templateId || !window.confirm("Usunąć lokalny szablon?")) return;
    await this._hass.callWS({ type: "mojv/communication_templates", action: "remove", id: templateId });
    await this._refresh();
  };

  proto._renderPraises = function (student) {
    const rows = [...(student.remarks || [])].filter((item) => item.kind === "positive" || item.kind === "praise").sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card list-view-card praise-view"><div class="section-head"><div><span class="kicker">Wychowanie</span><h2>Pochwały</h2></div><span>${rows.length}</span></div>${rows.length ? `<div class="data-list">${rows.map((item) => `<article class="data-row"><div class="remark-badge praise-badge">★</div><div><strong>${this._e(item.category || "Pochwała")}</strong><span>${this._e(item.text || "")}</span><small>${this._e(item.author || "")}</small></div><time>${this._e(this._date(item.date, true))}</time></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak pochwał w pobranym zakresie.</div>`}</section>`;
  };

  proto._renderWorkspace = function () {
    const students = this._data?.students || [];
    const cards = students.map((student) => {
      const grade = this._mojvGradeSummary(student).at(-1);
      const next = this._nextLesson(student, new Date());
      const unread = (student.messages || []).filter((item) => item.unread).length;
      return `<section class="card workspace-student-card"><div class="section-head"><div><span class="kicker">${this._e(student.class || "Uczeń")}</span><h2>${this._e(student.name)}</h2></div></div><div class="workspace-grid"><article><small>Ostatnia średnia</small><strong>${grade ? `${this._e(grade.subject)} · ${grade.average.toFixed(2)}` : "Brak ocen"}</strong></article><article><small>Najbliższa lekcja</small><strong>${next ? `${this._e(next.subject)} · ${this._time(next.start)}` : "Brak"}</strong></article><article><small>Nieprzeczytane</small><strong>${unread}</strong></article><article><small>Najbliższe zebranie</small><strong>${student.meetings?.[0] ? this._e(student.meetings[0].title || "Zebranie") : "Brak"}</strong></article></div></section>`;
    }).join("");
    return `<div class="workspace-view"><div class="modular-toolbar"><div><span class="kicker">Konfiguracja widoku</span><h2>Porównanie dzieci</h2><p>Układ automatycznie dopasowuje się do szerokości panelu.</p></div><button type="button" class="mojv-print-button" data-mojv-customize-modules="true">Ustaw karty i tekst</button></div>${cards || `<div class="mini-empty roomy">Brak aktywnych profili uczniów.</div>`}</div>`;
  };

  proto._mojvOpenReplyDialog = function (messageId) {
    const student = this._activeStudent();
    const message = (student?.messages || []).find((item) => item.id === messageId);
    if (!message) return;
    this._closeMojvReplyDialog();
    const overlay = document.createElement("div");
    overlay.className = "mojv-custom-overlay";
    overlay.dataset.mojvReplyOverlay = "true";
    overlay.innerHTML = `<div class="mojv-custom-backdrop" data-mojv-close-reply="true"></div><section class="mojv-custom-dialog" role="dialog" aria-modal="true" aria-label="Odpowiedź na wiadomość"><form data-mojv-send-reply="true" data-mojv-message-id="${this._e(message.id)}"><div class="mojv-custom-head"><div><span class="kicker">Odpowiedź</span><h2>${this._e(message.subject || "Bez tematu")}</h2><p>${this._e(message.sender || "")}</p></div><button type="button" class="icon-button" data-mojv-close-reply="true" aria-label="Zamknij">×</button></div><div class="communication-template-form"><label class="communication-wide">Treść<textarea name="body" required maxlength="4000" placeholder="Wpisz odpowiedź..."></textarea></label><label class="communication-confirm"><input type="checkbox" name="confirmed"> Rozumiem, że wiadomość zostanie wysłana do szkoły.</label><p class="mojv-custom-error" data-mojv-send-error></p><div class="mojv-custom-actions"><button type="button" class="mojv-print-button" data-mojv-close-reply="true">Anuluj</button><button type="submit" class="mojv-custom-primary">Podgląd i wyślij</button></div></div></form></section>`;
    overlay.addEventListener("click", (event) => { if (event.target.closest?.("[data-mojv-close-reply]")) this._closeMojvReplyDialog(); });
    this.shadowRoot.append(overlay);
    overlay.querySelector("textarea")?.focus();
  };

  proto._closeMojvReplyDialog = function () {
    this.shadowRoot.querySelector("[data-mojv-reply-overlay]")?.remove();
  };

  proto._renderCommunication = function (student) {
    const templates = student.communication_templates || [];
    const excuses = templates.filter((item) => item.kind === "excuse");
    const replies = templates.filter((item) => item.kind === "reply");
    const templateRows = (rows, empty) => rows.length ? `<div class="communication-template-list">${rows.map((item) => `<article><div><strong>${this._e(item.name)}</strong><p>${this._e(item.body)}</p></div><button type="button" class="icon-button" data-mojv-delete-template="${this._e(item.id)}" aria-label="Usuń szablon ${this._e(item.name)}">×</button></article>`).join("")}</div>` : `<div class="mini-empty">${empty}</div>`;
    return `<div class="communication-layout" data-view="communication">
      <section class="card communication-card"><div class="section-head"><div><span class="kicker">Usprawiedliwienia</span><h2>Twoje szablony</h2></div><span>${excuses.length}</span></div>${templateRows(excuses, "Nie masz jeszcze szablonu usprawiedliwienia.")}</section>
      <section class="card communication-card"><div class="section-head"><div><span class="kicker">Wiadomości</span><h2>Szablony odpowiedzi</h2></div><span>${replies.length}</span></div>${templateRows(replies, "Nie masz jeszcze szablonu odpowiedzi.")}</section>
      <section class="card communication-card"><div class="section-head"><div><span class="kicker">Nowy schemat</span><h2>Zapisz tekst lokalnie</h2></div></div><form data-mojv-communication-template="true" class="communication-template-form"><label>Rodzaj<select name="kind"><option value="excuse">Usprawiedliwienie</option><option value="reply">Odpowiedź</option></select></label><label>Nazwa<input name="name" required maxlength="80" placeholder="np. Wizyta u lekarza"></label><label class="communication-wide">Treść<textarea name="body" required maxlength="2000" placeholder="Dzień dobry, proszę o usprawiedliwienie nieobecności..."></textarea></label><p class="mojv-custom-error" data-mojv-template-error></p><div class="mojv-custom-actions"><button type="submit" class="mojv-custom-primary">Zapisz szablon w Home Assistant</button></div></form></section>
      <section class="card communication-notice"><div class="section-head"><div><span class="kicker">Bezpieczne nadanie</span><h2>Wysyłka do dziennika</h2></div></div><p>Teksty są przechowywane lokalnie. Faktyczne wysłanie usprawiedliwienia lub odpowiedzi będzie wymagało osobnego podglądu i potwierdzenia, aby nic nie zostało wysłane przypadkiem.</p></section>
    </div>`;
  };

  proto._renderSchoolInfo = function (student) {
    const school = student.school_info;
    const homeroom = student.homeroom_teachers || [];
    const teachers = student.teachers || [];
    const freeDays = [...(student.free_days || [])].sort((a, b) => new Date(a.start) - new Date(b.start));
    const excuses = student.excuses || {};
    const excuseEntries = [...(excuses.entries || [])].sort((a, b) => new Date(b.date) - new Date(a.date));

    const schoolRows = school ? [
      ["Nazwa", school.name],
      ["Miasto", school.city],
      ["Adres", school.address],
      ["WWW", school.website],
      ["E-mail", school.email],
      ["Dyrekcja", (school.directors || []).join(", ")],
    ].filter(([, value]) => value) : [];

    return `<div class="expanded-info-view" data-view="info">
      <section class="card expanded-info-card">
        <div class="section-head"><div><span class="kicker">Informacje</span><h2>Szkoła</h2></div></div>
        ${schoolRows.length ? `<div class="expanded-kv">${schoolRows.map(([label, value]) => `<div><small>${this._e(label)}</small><strong>${this._e(value)}</strong></div>`).join("")}</div>` : `<div class="mini-empty roomy">Brak publicznych informacji o szkole.</div>`}
      </section>
      <section class="card expanded-info-card">
        <div class="section-head"><div><span class="kicker">Opieka</span><h2>Wychowawcy</h2></div><span>${homeroom.length}</span></div>
        ${homeroom.length ? `<div class="expanded-simple-list">${homeroom.map((item) => `<div><strong>${this._e(item.name)}</strong>${item.primary ? `<span>główny wychowawca</span>` : ""}</div>`).join("")}</div>` : `<div class="mini-empty roomy">Brak danych o wychowawcy.</div>`}
      </section>
      <section class="card expanded-info-card">
        <div class="section-head"><div><span class="kicker">Kadra</span><h2>Nauczyciele</h2></div><span>${teachers.length}</span></div>
        ${teachers.length ? `<div class="expanded-simple-list">${teachers.map((item) => `<div><strong>${this._e(item.name)}</strong><span>${this._e(item.subject || (item.homeroom ? "wychowawca" : ""))}</span></div>`).join("")}</div>` : `<div class="mini-empty roomy">Brak danych o nauczycielach.</div>`}
      </section>
      <section class="card expanded-info-card">
        <div class="section-head"><div><span class="kicker">Kalendarz</span><h2>Dni wolne</h2></div><span>${freeDays.length}</span></div>
        ${freeDays.length ? `<div class="expanded-simple-list">${freeDays.map((item) => `<div><strong>${this._e(item.name || "Dzień wolny")}</strong><span>${this._e(this._date(item.start, true))}${item.end && item.end !== item.start ? ` – ${this._e(this._date(item.end, true))}` : ""}</span></div>`).join("")}</div>` : `<div class="mini-empty roomy">Brak dni wolnych w pobranym zakresie.</div>`}
      </section>
      <section class="card expanded-info-card">
        <div class="section-head"><div><span class="kicker">Frekwencja</span><h2>Usprawiedliwienia</h2></div><span>${excuseEntries.length}</span></div>
        <div class="expanded-status-line"><span>${excuses.active ? "Usprawiedliwienia aktywne" : "Usprawiedliwienia nieaktywne"}</span>${excuses.blocked ? `<strong>zablokowane</strong>` : ""}</div>
        ${excuseEntries.length ? `<div class="expanded-simple-list">${excuseEntries.map((item) => `<div><strong>${this._e(this._date(item.date, true))}</strong><span>${item.lesson_number ? `lekcja ${this._e(item.lesson_number)} · ` : ""}status ${this._e(item.status)}</span></div>`).join("")}</div>` : `<div class="mini-empty roomy">Brak wpisów o usprawiedliwieniach.</div>`}
      </section>
    </div>`;
  };

  proto._renderCompletedTopics = function (student) {
    const direction = this._topicsSortDirection === "asc" ? "asc" : "desc";
    const rows = [...(student.completed_lessons || [])].sort((a, b) => {
      const delta = new Date(a.date) - new Date(b.date);
      return direction === "asc" ? delta : -delta;
    });
    const sortLabel = direction === "asc" ? "Najstarsze → najnowsze" : "Najnowsze → najstarsze";
    return `<section class="card expanded-topics-card" data-view="topics">
      <div class="section-head"><div><span class="kicker">Tematy</span><h2>Zrealizowane zajęcia</h2></div><div class="expanded-topic-actions"><span>${rows.length}</span><button type="button" class="topic-sort-button" data-topics-sort="true">${this._e(sortLabel)}</button></div></div>
      ${rows.length ? `<div class="expanded-topic-list">${rows.map((item) => `<article><time>${this._e(this._date(item.date, true))}</time><div><small>${item.lesson_number ? `Lekcja ${this._e(item.lesson_number)} · ` : ""}${this._e(item.subject || "Zajęcia")}</small><strong>${this._e(item.topic || "Brak tematu")}</strong>${item.teacher ? `<span>${this._e(item.teacher)}</span>` : ""}</div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak zrealizowanych tematów w pobranym zakresie.</div>`}
    </section>`;
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      :host{font-size:calc(16px * var(--mojv-font-scale,1.12))}:host([data-mojv-theme="blue"]){--mv-accent:#2f8cff}:host([data-mojv-theme="warm"]){--mv-accent:#d97706;--mv-soft:rgba(217,119,6,.10)}:host([data-mojv-theme="dark"]){--mv-card:#111827;--mv-soft:#1f2937;--mv-line:#3b4555}.app-shell{width:min(100%,1560px);max-width:none;padding-inline:clamp(12px,2vw,30px)}.topbar{flex-wrap:wrap;align-items:flex-start;min-height:0}.brand-copy p{max-width:48ch}.top-actions{margin-left:auto}.mojv-display-settings{display:inline-flex;align-items:center;justify-content:center;gap:1px;font-weight:850}.mojv-display-settings span{font-size:.72em;align-self:flex-end}.view-nav{width:100%;max-width:none;flex-wrap:wrap;overflow:visible}.view-tab{padding:0 10px;min-height:38px}.student-nav{width:auto;max-width:100%;flex-wrap:wrap;overflow:visible}.view-content{width:100%;min-width:0}.section-head h2,.data-row strong,.work-copy strong{font-size:calc(1em * var(--mojv-font-scale,1.12))}.data-row span,.data-row small,.work-copy>span,.work-copy p{font-size:calc(.84em * var(--mojv-font-scale,1.12));line-height:1.5}.list-view-card,.final-grades-card,.schoolwork-card{max-width:none}.praise-badge{color:var(--mv-good);background:color-mix(in srgb,var(--mv-good) 18%,transparent)}.student-initial{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--mojv-student-color,var(--mv-accent));color:#fff;font-size:11px;font-weight:900}.modular-dashboard-family{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:16px;align-items:start}.workspace-view{display:grid;gap:14px}.workspace-view p{margin:5px 0 0;color:var(--mv-muted)}.workspace-student-card{min-width:0}.workspace-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px;padding:16px}.workspace-grid article{display:grid;gap:5px;padding:13px;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft)}.workspace-grid small{color:var(--mv-muted);font-size:12px}.workspace-grid strong{font-size:16px;line-height:1.35}.today-layout{grid-template-columns:minmax(0,1.35fr) minmax(330px,.65fr);grid-template-areas:"hero day" "alerts alerts"}.alerts-card .alert-list{display:grid;grid-auto-flow:column;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-rows:repeat(3,minmax(64px,auto));overflow:visible;gap:0 14px}.alerts-card .alert-row{min-width:0}.alerts-card .mini-empty{width:100%}
      .expanded-today-card{display:grid;gap:14px;padding:18px}.expanded-today-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.expanded-today-grid>div,.expanded-important-row{display:grid;gap:3px;padding:12px;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft)}.expanded-important-row{width:100%;color:inherit;text-align:left;cursor:pointer}.expanded-important-row:hover,.expanded-important-row:focus-visible{border-color:var(--mv-accent);outline:none}.expanded-today-grid small,.expanded-today-grid span,.expanded-important-row span,.expanded-important-row small,.expanded-muted{color:var(--mv-muted)}.expanded-today-grid strong{font-size:20px}.expanded-important-list{display:grid;gap:8px}
      .expanded-info-view{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.expanded-info-card,.expanded-topics-card{padding:18px}.expanded-kv,.expanded-simple-list{display:grid;gap:8px}.expanded-kv>div,.expanded-simple-list>div{display:grid;gap:2px;padding:10px 0;border-bottom:1px solid var(--mv-line)}.expanded-kv>div:last-child,.expanded-simple-list>div:last-child{border-bottom:0}.expanded-kv small,.expanded-simple-list span{color:var(--mv-muted)}.expanded-status-line{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:10px 12px;border-radius:10px;background:var(--mv-soft);margin-bottom:8px}.expanded-status-line strong{color:var(--error-color,#db4437)}
      .expanded-topic-actions{display:flex;gap:8px;align-items:center}.expanded-topic-actions>span{color:var(--mv-muted);font-size:11px}.topic-sort-button,.mojv-print-button{min-height:36px;padding:0 10px;border:1px solid var(--mv-line);border-radius:10px;background:var(--mv-soft);cursor:pointer;font-size:10px;font-weight:700}.topic-sort-button:hover,.topic-sort-button:focus-visible,.mojv-print-button:hover,.mojv-print-button:focus-visible{border-color:var(--mv-accent);outline:none}.mojv-print-toolbar{display:flex;justify-content:flex-end;margin-bottom:10px}
      .expanded-topic-list{display:grid}.expanded-topic-list article{display:grid;grid-template-columns:110px minmax(0,1fr);gap:14px;padding:12px 0;border-bottom:1px solid var(--mv-line)}.expanded-topic-list article:last-child{border-bottom:0}.expanded-topic-list time,.expanded-topic-list small,.expanded-topic-list span{color:var(--mv-muted)}.expanded-topic-list article>div{display:grid;gap:3px}.attendance-legend{display:flex;align-items:center;flex-wrap:wrap;gap:7px;padding:12px 2px}.attendance-legend>span{margin-right:3px;color:var(--mv-muted);font-size:11px;font-weight:750}.attendance-legend-dot{width:30px;height:30px;border:0;border-radius:50%;cursor:help;font-size:9px;font-weight:900;line-height:1}.attendance-legend-dot.ok{color:var(--mv-good);background:color-mix(in srgb,var(--mv-good) 18%,transparent)}.attendance-legend-dot.bad{color:var(--mv-bad);background:color-mix(in srgb,var(--mv-bad) 18%,transparent)}.attendance-legend-dot.warn{color:var(--mv-warn);background:color-mix(in srgb,var(--mv-warn) 18%,transparent)}.attendance-legend-dot.muted{color:var(--mv-muted);background:var(--mv-soft)}.attendance-legend-dot:hover,.attendance-legend-dot:focus-visible{outline:2px solid var(--mv-accent);outline-offset:2px}
      .modular-dashboard{display:grid;gap:14px}.modular-toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px}.modular-toolbar h2{margin:4px 0 0;font-size:22px}.modular-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:14px;align-items:start}.modular-card{min-width:0}.modular-list{display:grid;padding:4px 18px 12px}.modular-list article{display:grid;grid-template-columns:76px minmax(0,1fr);gap:10px;padding:11px 0;border-bottom:1px solid var(--mv-line)}.modular-list article:last-child{border-bottom:0}.modular-list time{display:grid;align-content:start;gap:3px;color:var(--mv-muted);font-size:10px;font-weight:750}.modular-list time small,.modular-list span{color:var(--mv-muted);font-size:10px}.modular-list article>div{display:grid;gap:3px}.modular-list article small{color:var(--mv-muted);font-size:10px;text-transform:uppercase;letter-spacing:.05em}.grade-trend-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;padding:14px}.grade-trend-grid article{display:grid;gap:3px;padding:12px;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft)}.grade-trend-grid article.needs-attention{border-color:color-mix(in srgb,var(--mv-warn) 55%,var(--mv-line))}.grade-trend-grid article>span{font-size:25px;font-weight:850}.grade-trend-grid small{color:var(--mv-muted)}.modular-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:14px}.modular-metrics>div{display:grid;gap:4px;padding:12px;border-radius:12px;background:var(--mv-soft)}.modular-metrics small{color:var(--mv-muted);font-size:10px}.modular-metrics strong{font-size:24px}.mojv-module-overlay{position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:24px}.mojv-module-dialog{position:relative;z-index:1;width:min(460px,100%);background:var(--mv-card);border:1px solid var(--mv-line);border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.35);overflow:hidden}.module-choice-list{display:grid;gap:2px;padding:16px}.module-choice-list label{display:flex;align-items:center;gap:10px;min-height:42px;padding:0 8px;border-radius:9px;cursor:pointer}.module-choice-list label:hover{background:var(--mv-soft)}.module-choice-list input{width:17px;height:17px;accent-color:var(--mv-accent)}
      .message-actions{display:grid;justify-items:end;align-content:space-between;gap:8px}.message-actions time{color:var(--mv-muted);font-size:11px}.communication-layout{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.communication-card,.communication-notice{min-width:0}.communication-template-list{display:grid;padding:5px 18px 12px}.communication-template-list article{display:grid;grid-template-columns:minmax(0,1fr) 36px;gap:12px;padding:12px 0;border-bottom:1px solid var(--mv-line)}.communication-template-list article:last-child{border-bottom:0}.communication-template-list article>div{min-width:0}.communication-template-list strong{display:block}.communication-template-list p{margin:5px 0 0;color:var(--mv-muted);font-size:14px;line-height:1.55;white-space:pre-wrap}.communication-template-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:18px}.communication-template-form label{display:grid;gap:6px;color:var(--mv-muted);font-size:13px;font-weight:700}.communication-template-form input,.communication-template-form select,.communication-template-form textarea{width:100%;min-height:40px;padding:9px 10px;border:1px solid var(--mv-line);border-radius:10px;background:var(--mv-soft);color:var(--primary-text-color,#fff);font:inherit}.communication-template-form textarea{min-height:110px;resize:vertical}.communication-wide{grid-column:1/-1}.communication-confirm{grid-column:1/-1;display:flex!important;align-items:center;gap:8px}.communication-confirm input{width:18px;height:18px;min-height:18px!important;padding:0!important;accent-color:var(--mv-accent)}.communication-template-form .mojv-custom-actions{grid-column:1/-1;padding:0;border:0}.communication-notice{grid-column:1/-1;padding:0 18px 18px}.communication-notice p{margin:16px 0 0;color:var(--mv-muted);font-size:14px;line-height:1.55}.display-choice-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:0 16px 16px}.display-choice-list label{display:grid;gap:6px;color:var(--mv-muted);font-size:12px;font-weight:750}.display-choice-list select,.display-choice-list input[type=range]{width:100%;min-height:40px;border:1px solid var(--mv-line);border-radius:10px;background:var(--mv-soft);color:inherit;padding:0 8px}.student-choice-list{display:grid;gap:8px;margin:0 16px 16px;padding:12px;border:1px solid var(--mv-line);border-radius:12px}.student-choice-list legend{padding:0 5px;color:var(--mv-muted);font-size:12px;font-weight:800}.student-choice-list label{display:flex;align-items:center;gap:8px;min-height:30px}.student-choice-list input[type=color]{margin-left:auto;width:34px;height:26px;border:0;background:transparent}
      @media(max-width:760px){.expanded-info-view,.communication-layout,.display-choice-list{grid-template-columns:1fr}.expanded-today-grid{grid-template-columns:1fr}.expanded-topic-list article{grid-template-columns:1fr;gap:4px}.expanded-topic-actions{align-items:flex-end;flex-direction:column}.modular-toolbar{align-items:flex-start;flex-direction:column}.modular-toolbar button{width:100%}.modular-list article{grid-template-columns:82px minmax(0,1fr)}.modular-dashboard-family{grid-template-columns:1fr}.today-layout{grid-template-columns:1fr;grid-template-areas:"hero" "day" "alerts"}.alerts-card .alert-list{grid-auto-flow:row;grid-template-columns:1fr;grid-template-rows:none}.mojv-module-overlay{align-items:end;padding:0}.mojv-module-dialog{width:100%;border-radius:18px 18px 0 0}.communication-template-form{grid-template-columns:1fr}}
      .schedule-print-header{display:none}
      @media print{@page{size:A4 landscape;margin:10mm}:host{background:#fff!important;color:#000!important;print-color-adjust:exact;-webkit-print-color-adjust:exact}.topbar,.student-nav,.view-nav,.schedule-toolbar,.schedule-now-indicator,.mojv-print-toolbar,.mojv-print-button,.topic-sort-button{display:none!important}.app-shell{max-width:none!important;padding:0!important}.view-content{min-height:0}.schedule-print-header{display:block;margin:0 0 6mm;color:#000}.schedule-print-header h1{margin:0;font-size:18pt}.schedule-print-header p{margin:2mm 0 1mm;font-size:12pt;font-weight:700}.schedule-print-header small{font-size:10pt}.card{box-shadow:none!important;break-inside:avoid}.schedule-scroll{overflow:visible!important}.schedule-canvas{min-width:0!important}.schedule-table{font-size:9px}.schedule-now-indicator,.attendance-mini,.badge-row{display:none!important}}
    `;
  };
}
