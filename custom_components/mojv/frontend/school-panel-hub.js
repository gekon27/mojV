import "./school-panel-hub-base.js";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvExpandedSchoolHubPatched) {
  proto.__mojvExpandedSchoolHubPatched = true;

  const baseAvailableViews = proto._availableViews;
  const baseRenderActiveView = proto._renderActiveView;
  const baseRenderDashboard = proto._renderDashboard;
  const baseStyles = proto._styles;

  proto._availableViews = function (student) {
    const views = baseAvailableViews.call(this, student);
    const hasInfo = Boolean(
      student?.school_info ||
      (student?.teachers || []).length ||
      (student?.homeroom_teachers || []).length ||
      (student?.free_days || []).length ||
      student?.excuses?.active ||
      student?.excuses?.blocked ||
      (student?.excuses?.entries || []).length
    );
    if (hasInfo && !views.some(([id]) => id === "info")) {
      views.push(["info", "Informacje", "ⓘ"]);
    }
    if ((student?.completed_lessons || []).length && !views.some(([id]) => id === "topics")) {
      views.push(["topics", "Tematy", "≡"]);
    }
    return views;
  };

  proto._renderActiveView = function () {
    const content = this.shadowRoot.querySelector("#view-content");
    const student = this._activeStudent();
    if (!content || !student || this._error) return baseRenderActiveView.call(this);

    switch (this._activeView) {
      case "info":
        content.innerHTML = this._renderSchoolInfo(student);
        return;
      case "topics":
        content.innerHTML = this._renderCompletedTopics(student);
        return;
      default:
        return baseRenderActiveView.call(this);
    }
  };

  proto._renderDashboard = function (student) {
    const base = baseRenderDashboard.call(this, student);
    const dashboard = student?.dashboard || {};
    const lucky_number = dashboard.lucky_number;
    const important_today = dashboard.important_today || [];
    const next_free_day = dashboard.next_free_day;
    if (!lucky_number && !important_today.length && !next_free_day) return base;

    const important = important_today.length
      ? `<div class="expanded-important-list">${important_today.map((item) => `<div class="expanded-important-row"><strong>${this._e(item.title || item.kind || "Ważne")}</strong>${item.subject ? `<span>${this._e(item.subject)}</span>` : ""}</div>`).join("")}</div>`
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
    const rows = [...(student.completed_lessons || [])].sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card expanded-topics-card" data-view="topics">
      <div class="section-head"><div><span class="kicker">Tematy</span><h2>Zrealizowane zajęcia</h2></div><span>${rows.length}</span></div>
      ${rows.length ? `<div class="expanded-topic-list">${rows.map((item) => `<article><time>${this._e(this._date(item.date, true))}</time><div><small>${item.lesson_number ? `Lekcja ${this._e(item.lesson_number)} · ` : ""}${this._e(item.subject || "Zajęcia")}</small><strong>${this._e(item.topic || "Brak tematu")}</strong>${item.teacher ? `<span>${this._e(item.teacher)}</span>` : ""}</div></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak zrealizowanych tematów w pobranym zakresie.</div>`}
    </section>`;
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .expanded-today-card{display:grid;gap:14px;padding:18px}.expanded-today-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.expanded-today-grid>div,.expanded-important-row{display:grid;gap:3px;padding:12px;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft)}.expanded-today-grid small,.expanded-today-grid span,.expanded-important-row span,.expanded-muted{color:var(--mv-muted)}.expanded-today-grid strong{font-size:20px}.expanded-important-list{display:grid;gap:8px}
      .expanded-info-view{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.expanded-info-card,.expanded-topics-card{padding:18px}.expanded-kv,.expanded-simple-list{display:grid;gap:8px}.expanded-kv>div,.expanded-simple-list>div{display:grid;gap:2px;padding:10px 0;border-bottom:1px solid var(--mv-line)}.expanded-kv>div:last-child,.expanded-simple-list>div:last-child{border-bottom:0}.expanded-kv small,.expanded-simple-list span{color:var(--mv-muted)}.expanded-status-line{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:10px 12px;border-radius:10px;background:var(--mv-soft);margin-bottom:8px}.expanded-status-line strong{color:var(--error-color,#db4437)}
      .expanded-topic-list{display:grid}.expanded-topic-list article{display:grid;grid-template-columns:110px minmax(0,1fr);gap:14px;padding:12px 0;border-bottom:1px solid var(--mv-line)}.expanded-topic-list article:last-child{border-bottom:0}.expanded-topic-list time,.expanded-topic-list small,.expanded-topic-list span{color:var(--mv-muted)}.expanded-topic-list article>div{display:grid;gap:3px}
      @media(max-width:760px){.expanded-info-view{grid-template-columns:1fr}.expanded-today-grid{grid-template-columns:1fr}.expanded-topic-list article{grid-template-columns:1fr;gap:4px}}
    `;
  };
}
