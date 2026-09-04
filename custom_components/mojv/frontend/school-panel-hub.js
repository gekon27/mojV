import "./school-panel-live.js";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvSchoolHubPatched) {
  proto.__mojvSchoolHubPatched = true;

  const baseConnectedCallback = proto.connectedCallback;
  const baseAvailableViews = proto._availableViews;
  const baseRenderActiveView = proto._renderActiveView;
  const baseRenderNavigation = proto._renderNavigation;
  const baseStyles = proto._styles;
  const baseTickClock = proto._tickClock;

  proto.connectedCallback = function () {
    if (!this.__mojvHubDefaultApplied) {
      this.__mojvHubDefaultApplied = true;
      this._activeView = "dashboard";
    }
    return baseConnectedCallback.call(this);
  };

  proto._availableViews = function (student) {
    const views = baseAvailableViews.call(this, student).filter(([id]) => !["dashboard", "activity", "notifications"].includes(id));
    const result = [["dashboard", "Pulpit", "⌂"], ...views];
    if ((student?.activity || []).length) result.push(["activity", "Aktywność", "≡"]);
    result.push(["notifications", "Powiadomienia", "◉"]);
    return result;
  };

  proto._renderNavigation = function () {
    baseRenderNavigation.call(this);
    const student = this._activeStudent();
    const dashboard = student?.dashboard || {};
    const counts = {
      messages: Number(dashboard.unread_messages || 0),
      schoolwork: Number(dashboard.upcoming_schoolwork || 0),
      meetings: Number(dashboard.upcoming_meetings || 0),
      notifications: (student?.notifications || []).length,
    };
    const nav = this.shadowRoot.querySelector("#view-nav");
    if (!nav) return;
    nav.querySelectorAll("button[data-view]").forEach((button) => {
      button.querySelectorAll(".view-badge").forEach((node) => node.remove());
      const count = counts[button.dataset.view] || 0;
      if (!count) return;
      const badge = document.createElement("span");
      badge.className = "view-badge";
      badge.textContent = count > 99 ? "99+" : String(count);
      button.appendChild(badge);
    });
  };

  proto._renderActiveView = function () {
    const content = this.shadowRoot.querySelector("#view-content");
    const student = this._activeStudent();
    if (!content || !student || this._error) return baseRenderActiveView.call(this);

    switch (this._activeView) {
      case "dashboard":
        content.innerHTML = this._renderDashboard(student);
        this._lastCurrentKey = this._lessonKey(this._currentLesson(student));
        this._updateDashboardLive();
        return;
      case "activity":
        content.innerHTML = this._renderActivity(student);
        return;
      case "notifications":
        content.innerHTML = this._renderNotifications(student);
        return;
      default:
        return baseRenderActiveView.call(this);
    }
  };

  proto._renderDashboard = function (student) {
    const summary = student.dashboard || {};
    const current = this._currentLesson(student, new Date());
    const next = this._nextLesson(student, new Date());
    const latestGrade = summary.latest_grade;
    const work = summary.next_schoolwork;
    const meeting = summary.next_meeting;
    const remark = summary.latest_remark;
    const achievement = summary.latest_achievement;
    const latestMessage = summary.latest_message;
    const attendance = summary.attendance_percentage == null ? "—" : `${Number(summary.attendance_percentage).toFixed(1).replace(".0", "")}%`;
    const [attendanceText, attendanceClass, attendanceMark] = this._attendance(current?.attendance);

    const summaryCard = (icon, label, value, meta = "", extraClass = "") => `<article class="hub-summary-card ${extraClass}">
      <span class="hub-summary-icon">${this._e(icon)}</span>
      <div><small>${this._e(label)}</small><strong>${this._e(value || "—")}</strong>${meta ? `<span>${this._e(meta)}</span>` : ""}</div>
    </article>`;

    return `<div class="hub-dashboard" data-view="dashboard">
      <section class="card hub-lesson-card">
        <div class="section-head"><div><span class="kicker">Pulpit</span><h2>${this._e(student.name)}</h2></div><span class="class-pill">${this._e(student.class || "Uczeń")}</span></div>
        <div class="hub-current-grid">
          <div class="hub-current-copy"><span class="kicker">Teraz</span><h3>${this._e(current?.subject || "Przerwa / brak lekcji")}</h3>${current ? `<p>Lekcja ${this._e(current.number)} · ${this._e(current.room || "bez sali")}${current.teacher ? ` · ${this._e(current.teacher)}` : ""}</p>` : `<p>Brak trwającej lekcji.</p>`}<div class="hub-attendance ${attendanceClass}">${this._e(attendanceMark)} ${this._e(current ? attendanceText : "Poza lekcją")}</div></div>
          <div class="hub-countdown"><strong id="hub-live-minutes">${current ? this._minutesToEnd(current, new Date()) : "—"}</strong><span>${current ? "min do końca" : ""}</span></div>
        </div>
        <div class="hub-next"><span>Następna</span><strong>${this._e(next?.subject || "Brak kolejnej lekcji")}</strong><small>${next ? `${this._time(next.start)}–${this._time(next.end)} · ${this._e(next.room || "bez sali")}` : ""}</small></div>
      </section>

      <section class="hub-summary-grid">
        ${summaryCard("✉", "Nieprzeczytane", String(summary.unread_messages || 0), "wiadomości")}
        ${summaryCard("5", "Ostatnia ocena", latestGrade?.value || "—", latestGrade ? `${latestGrade.subject}${latestGrade.weight ? ` · waga ${latestGrade.weight}` : ""}` : "")}
        ${summaryCard("%", "Frekwencja", attendance, "ogółem")}
        ${summaryCard("◆", "Najbliższy termin", work?.title || "Brak", work ? `${work.subject} · ${this._date(work.date, true)}` : "")}
        ${summaryCard("◷", "Najbliższe zebranie", meeting?.title || "Brak", meeting ? `${this._date(meeting.start, true)} · ${this._time(meeting.start)}` : "")}
        ${summaryCard(remark?.kind === "positive" ? "★" : "!", remark?.kind === "positive" ? "Ostatnia pochwała" : "Ostatnia uwaga", remark?.category || (remark ? "Wpis" : "Brak"), remark?.text || "")}
        ${summaryCard("★", "Osiągnięcie", achievement?.title || "Brak", achievement?.description || "")}
        ${summaryCard("●", "Aktywne powiadomienia", String((student.notifications || []).length), "historia mojV")}
      </section>

      <section class="hub-detail-grid">
        <article class="card hub-detail-card"><div class="section-head"><div><span class="kicker">Wiadomości</span><h2>Ostatnia</h2></div></div>${latestMessage ? `<strong>${this._e(latestMessage.subject || "Bez tematu")}</strong><span>${this._e(latestMessage.sender || "")}</span><small>${this._date(latestMessage.date, true)}</small>` : `<div class="mini-empty">Brak wiadomości.</div>`}</article>
        <article class="card hub-detail-card"><div class="section-head"><div><span class="kicker">Synchronizacja</span><h2>Status</h2></div></div><strong>${this._data?.updated_at ? this._e(this._date(this._data.updated_at, true)) : "Brak danych"}</strong><span>${this._data?.updated_at ? this._e(this._time(this._data.updated_at)) : ""}</span><small>HTTP first · automatyczny fallback</small></article>
      </section>
    </div>`;
  };

  proto._activityIcon = function (kind) {
    return ({ grade: "5", final_grade: "✓", remark: "!", praise: "★", message: "✉", schoolwork: "◆", meeting: "◷", achievement: "★", attendance: "✓" })[kind] || "•";
  };

  proto._activityLabel = function (kind) {
    return ({ grade: "Ocena", final_grade: "Klasyfikacja", remark: "Uwaga", praise: "Pochwała", message: "Wiadomość", schoolwork: "Terminarz", meeting: "Zebranie", achievement: "Osiągnięcie", attendance: "Frekwencja" })[kind] || "Aktywność";
  };

  proto._renderActivity = function (student) {
    const rows = [...(student.activity || [])];
    return `<section class="card hub-list-card" data-view="activity">
      <div class="section-head"><div><span class="kicker">Aktywność</span><h2>Wszystko w jednym miejscu</h2></div><span>${rows.length}</span></div>
      ${rows.length ? `<div class="hub-timeline">${rows.map((item) => `<article class="hub-timeline-row ${this._e(item.kind || "")}"><div class="hub-timeline-icon">${this._e(this._activityIcon(item.kind))}</div><div class="hub-timeline-copy"><small>${this._e(this._activityLabel(item.kind))}</small><strong>${this._e(item.title || "Wpis")}</strong>${item.subtitle ? `<span>${this._e(item.subtitle)}</span>` : ""}${item.detail ? `<p>${this._e(item.detail)}</p>` : ""}</div><time>${item.date ? this._e(this._date(item.date, true)) : ""}${item.date ? `<small>${this._e(this._time(item.date))}</small>` : ""}</time></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak aktywności w pobranym zakresie.</div>`}
    </section>`;
  };

  proto._notificationIcon = function (kind) {
    return ({ grade: "5", final_grade: "✓", remark: "!", praise: "★", message: "✉", absence: "×", late: "!", lesson_cancelled: "×", lesson_replacement: "↔", lesson_changed: "↻", lesson_ending: "⌛", schoolwork_new: "◆", schoolwork_due: "◆", meeting_new: "◷", meeting_due: "◷", achievement: "★" })[kind] || "●";
  };

  proto._renderNotifications = function (student) {
    const rows = [...(student.notifications || [])];
    return `<section class="card hub-list-card" data-view="notifications">
      <div class="section-head"><div><span class="kicker">Powiadomienia</span><h2>Historia mojV</h2></div><span>${rows.length}</span></div>
      ${rows.length ? `<div class="hub-notification-list">${rows.map((item) => `<article class="hub-notification-row priority-${this._e(item.priority || "normal")}"><div class="hub-notification-icon">${this._e(this._notificationIcon(item.kind))}</div><div><small>${this._e(item.kind || "powiadomienie")}</small><strong>${this._e(item.title || "Powiadomienie")}</strong><p>${this._e(item.message || "")}</p></div><time>${item.created_at ? this._e(this._date(item.created_at, true)) : ""}${item.created_at ? `<small>${this._e(this._time(item.created_at))}</small>` : ""}</time></article>`).join("")}</div>` : `<div class="mini-empty roomy">Brak zapisanych powiadomień. Pierwsza synchronizacja LIVE tworzy baseline bez lawiny starych alertów.</div>`}
    </section>`;
  };

  proto._tickClock = function () {
    baseTickClock.call(this);
    if (this._activeView === "dashboard") this._updateDashboardLive();
  };

  proto._updateDashboardLive = function () {
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
    const minutes = this.shadowRoot.querySelector("#hub-live-minutes");
    if (minutes) minutes.textContent = current ? String(this._minutesToEnd(current, now)) : "—";
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .view-tab{position:relative}.view-badge{min-width:17px;height:17px;padding:0 5px;border-radius:999px;display:inline-grid;place-items:center;background:var(--error-color,#db4437);color:#fff;font-size:9px;font-weight:800;line-height:1;margin-left:2px}
      .hub-dashboard{display:grid;gap:14px}.hub-lesson-card{padding:20px}.hub-current-grid{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;padding:18px 0}.hub-current-copy h3{font-size:clamp(25px,4vw,38px);margin:4px 0}.hub-current-copy p{margin:0;color:var(--mv-muted)}.hub-attendance{display:inline-flex;gap:6px;align-items:center;margin-top:12px;padding:6px 10px;border-radius:999px;background:var(--mv-soft);font-weight:700}.hub-countdown{width:112px;height:112px;border-radius:50%;display:grid;place-items:center;align-content:center;background:color-mix(in srgb,var(--mv-accent) 13%,var(--mv-card));border:1px solid color-mix(in srgb,var(--mv-accent) 28%,var(--mv-line));text-align:center}.hub-countdown strong{font-size:34px}.hub-countdown span{font-size:10px;color:var(--mv-muted)}.hub-next{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;padding:12px 14px;border-radius:12px;background:var(--mv-soft)}.hub-next>span,.hub-next small{color:var(--mv-muted)}
      .hub-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.hub-summary-card{min-height:92px;display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:center;padding:14px;border:1px solid var(--mv-line);border-radius:14px;background:var(--mv-card);box-shadow:var(--ha-card-box-shadow,none)}.hub-summary-icon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:color-mix(in srgb,var(--mv-accent) 13%,transparent);color:var(--mv-accent);font-weight:900}.hub-summary-card>div{min-width:0;display:grid;gap:2px}.hub-summary-card small,.hub-summary-card span{color:var(--mv-muted);overflow:hidden;text-overflow:ellipsis}.hub-summary-card strong{font-size:18px;overflow:hidden;text-overflow:ellipsis}
      .hub-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.hub-detail-card{display:grid;gap:6px}.hub-detail-card>span,.hub-detail-card>small{color:var(--mv-muted)}
      .hub-list-card{padding:18px}.hub-timeline,.hub-notification-list{display:grid}.hub-timeline-row,.hub-notification-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;padding:13px 4px;border-top:1px solid var(--mv-line);align-items:flex-start}.hub-timeline-row:first-child,.hub-notification-row:first-child{border-top:0}.hub-timeline-icon,.hub-notification-icon{width:36px;height:36px;border-radius:10px;display:grid;place-items:center;background:var(--mv-soft);color:var(--mv-accent);font-weight:900}.hub-timeline-copy,.hub-notification-row>div:nth-child(2){display:grid;gap:3px;min-width:0}.hub-timeline-copy small,.hub-notification-row small{color:var(--mv-muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em}.hub-timeline-copy span{color:var(--mv-muted)}.hub-timeline-copy p,.hub-notification-row p{margin:3px 0 0;line-height:1.4;white-space:pre-wrap}.hub-timeline-row time,.hub-notification-row time{display:grid;gap:2px;text-align:right;color:var(--mv-muted);font-size:11px}.hub-notification-row.priority-high{border-left:3px solid var(--error-color,#db4437);padding-left:10px}.hub-notification-row.priority-low{opacity:.86}
      @media (max-width:1000px){.hub-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
      @media (max-width:680px){.hub-current-grid{grid-template-columns:1fr}.hub-countdown{width:88px;height:88px}.hub-next{grid-template-columns:1fr}.hub-summary-grid,.hub-detail-grid{grid-template-columns:1fr}.hub-timeline-row,.hub-notification-row{grid-template-columns:auto minmax(0,1fr)}.hub-timeline-row time,.hub-notification-row time{grid-column:2;text-align:left}}
    `;
  };
}
