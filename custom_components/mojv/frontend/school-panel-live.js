import "./school-panel.js";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvLiveModulesPatched) {
  proto.__mojvLiveModulesPatched = true;

  const baseAvailableViews = proto._availableViews;
  const baseRenderActiveView = proto._renderActiveView;
  const baseStyles = proto._styles;

  proto._availableViews = function (student) {
    const views = baseAvailableViews.call(this, student);
    if ((student?.messages || []).length) views.push(["messages", "Wiadomości", "✉"]);
    if ((student?.attendance_stats || []).length) views.push(["attendance_stats", "Statystyki", "%"]);
    if ((student?.achievements || []).length) views.push(["achievements", "Osiągnięcia", "★"]);
    if ((student?.meetings || []).length) views.push(["meetings", "Zebrania", "◷"]);
    return views;
  };

  proto._renderActiveView = function () {
    const content = this.shadowRoot.querySelector("#view-content");
    const student = this._activeStudent();
    if (!content || !student || this._error) return baseRenderActiveView.call(this);

    switch (this._activeView) {
      case "messages":
        content.innerHTML = this._renderMessages(student);
        return;
      case "attendance_stats":
        content.innerHTML = this._renderAttendanceStats(student);
        return;
      case "achievements":
        content.innerHTML = this._renderAchievements(student);
        return;
      case "meetings":
        content.innerHTML = this._renderMeetings(student);
        return;
      default:
        return baseRenderActiveView.call(this);
    }
  };

  proto._renderMessages = function (student) {
    const rows = [...(student.messages || [])].sort((a, b) => new Date(b.date) - new Date(a.date));
    return `<section class="card list-view-card live-module-card" data-view="messages">
      <div class="section-head"><div><span class="kicker">Wiadomości</span><h2>Odebrane</h2></div><span>${rows.length}</span></div>
      <div class="data-list">${rows.map((message) => `<article class="data-row message-row ${message.unread ? "unread" : ""}">
        <div class="live-icon">${message.unread ? "●" : "✉"}</div>
        <div><strong>${this._e(message.subject || "Bez tematu")}</strong><span>${this._e(message.sender || "Nadawca nieznany")}</span>${message.body ? `<p>${this._e(message.body)}</p>` : ""}</div>
        <time>${this._e(this._date(message.date, true))}</time>
      </article>`).join("")}</div>
    </section>`;
  };

  proto._renderAttendanceStats = function (student) {
    const stats = [...(student.attendance_stats || [])];
    const cards = stats.map((stat) => {
      const label = stat.subject || "Wszystkie przedmioty";
      const percentage = stat.percentage == null ? "—" : `${Number(stat.percentage).toFixed(1).replace(".0", "")}%`;
      return `<article class="stat-card">
        <div class="stat-head"><div><span class="kicker">${this._e(label)}</span><strong>${this._e(percentage)}</strong></div><span>${this._e(stat.total ?? 0)} lekcji</span></div>
        <div class="stat-grid">
          <span><small>Obecności</small><strong>${this._e(stat.present ?? 0)}</strong></span>
          <span><small>Nieobecności</small><strong>${this._e(stat.absent ?? 0)}</strong></span>
          <span><small>Usprawiedl.</small><strong>${this._e(stat.excused ?? 0)}</strong></span>
          <span><small>Spóźnienia</small><strong>${this._e((stat.late ?? 0) + (stat.excused_late ?? 0))}</strong></span>
        </div>
      </article>`;
    }).join("");
    return `<section class="card list-view-card live-module-card" data-view="attendance_stats">
      <div class="section-head"><div><span class="kicker">Frekwencja</span><h2>Statystyki</h2></div><span>${stats.length}</span></div>
      <div class="stat-cards">${cards}</div>
    </section>`;
  };

  proto._renderAchievements = function (student) {
    const rows = [...(student.achievements || [])].sort((a, b) => {
      if (!a.date) return 1;
      if (!b.date) return -1;
      return new Date(b.date) - new Date(a.date);
    });
    return `<section class="card list-view-card live-module-card" data-view="achievements">
      <div class="section-head"><div><span class="kicker">Osiągnięcia</span><h2>Wyróżnienia i wyniki</h2></div><span>${rows.length}</span></div>
      <div class="data-list">${rows.map((item) => `<article class="data-row"><div class="live-icon achievement">★</div><div><strong>${this._e(item.title || "Osiągnięcie")}</strong>${item.description ? `<span>${this._e(item.description)}</span>` : ""}</div><time>${item.date ? this._e(this._date(item.date, true)) : ""}</time></article>`).join("")}</div>
    </section>`;
  };

  proto._safeUrl = function (value) {
    if (!value) return "";
    try {
      const url = new URL(String(value));
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch (_error) {
      return "";
    }
  };

  proto._renderMeetings = function (student) {
    const rows = [...(student.meetings || [])].sort((a, b) => new Date(a.start) - new Date(b.start));
    return `<section class="card list-view-card live-module-card" data-view="meetings">
      <div class="section-head"><div><span class="kicker">Zebrania</span><h2>Spotkania z rodzicami</h2></div><span>${rows.length}</span></div>
      <div class="data-list">${rows.map((item) => {
        const online = this._safeUrl(item.online_url);
        return `<article class="data-row meeting-row"><div class="live-icon">◷</div><div><strong>${this._e(item.title || "Zebranie")}</strong><span>${this._e(item.location || "")}</span>${item.description ? `<p>${this._e(item.description)}</p>` : ""}${online ? `<a class="meeting-link" href="${this._e(online)}" target="_blank" rel="noopener noreferrer">Otwórz spotkanie online</a>` : ""}</div><time>${this._e(this._date(item.start, true))}<small>${this._e(this._time(item.start))}</small></time></article>`;
      }).join("")}</div>
    </section>`;
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .live-module-card .data-row{align-items:flex-start}
      .live-module-card .data-row p{margin:7px 0 0;color:var(--primary-text-color);line-height:1.45;white-space:pre-wrap}
      .live-icon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:color-mix(in srgb,var(--mv-accent) 14%,transparent);color:var(--mv-accent);font-weight:800}
      .live-icon.achievement{color:var(--mv-warn);background:color-mix(in srgb,var(--mv-warn) 15%,transparent)}
      .message-row.unread strong{color:var(--mv-accent)}
      .stat-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
      .stat-card{padding:16px;border:1px solid var(--mv-line);background:var(--mv-soft);border-radius:14px}
      .stat-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.stat-head>div{display:grid;gap:5px}.stat-head strong{font-size:24px}.stat-head>span{font-size:11px;color:var(--mv-muted)}
      .stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:14px}.stat-grid span{display:grid;padding:8px;border-radius:10px;background:var(--mv-card)}.stat-grid small{color:var(--mv-muted);font-size:10px}.stat-grid strong{margin-top:2px}
      .meeting-row time{display:grid;gap:3px;text-align:right}.meeting-row time small{color:var(--mv-muted)}
      .meeting-link{display:inline-block;margin-top:8px;color:var(--mv-accent);font-weight:700;text-decoration:none}.meeting-link:hover{text-decoration:underline}
    `;
  };
}
