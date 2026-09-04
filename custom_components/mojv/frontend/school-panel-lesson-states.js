import "./school-panel-hub-base.js";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvLessonStatesPatched) {
  proto.__mojvLessonStatesPatched = true;

  const baseStyles = proto._styles;
  const baseRenderSchedule = proto._renderSchedule;

  proto._mojvLessonState = function (lesson, now = new Date()) {
    if (lesson?.cancelled) return "cancelled";
    const start = new Date(lesson?.start);
    const end = new Date(lesson?.end);
    if (start <= now && now < end) return "current";
    if (end <= now) return "completed";
    return "upcoming";
  };

  proto._mojvLessonStateLabel = function (state) {
    return ({
      cancelled: "Odwołana",
      current: "Teraz",
      completed: "Odbyta",
      upcoming: "",
    })[state] || "";
  };

  proto._mojvLessonStateBadge = function (state) {
    const label = this._mojvLessonStateLabel(state);
    if (!label) return "";
    const cls = state === "cancelled" ? "bad" : state === "current" ? "current-state" : "muted-state";
    return `<span class="badge lesson-state-label ${cls}" data-lesson-state-label="true">${this._e(label)}</span>`;
  };

  proto._todayLessonRow = function (lesson) {
    const [text, cls, mark] = this._attendance(lesson.attendance);
    const state = this._mojvLessonState(lesson, new Date());
    return `<article class="timeline-row lesson-state-${state}" data-lesson-state="${state}"><div class="timeline-time">${this._time(lesson.start)}<small>${this._time(lesson.end)}</small></div><div class="timeline-dot"></div><div class="timeline-copy"><div><strong>${this._e(lesson.subject)}</strong>${this._mojvLessonStateBadge(state)}${lesson.replacement ? `<span class="badge warn">Zastępstwo</span>` : ""}</div><span>Lekcja ${this._e(lesson.number)} · ${this._e(lesson.room || "bez sali")}${lesson.teacher ? ` · ${this._e(lesson.teacher)}` : ""}</span></div><div class="attendance-dot ${cls}" title="${this._e(text)}">${this._e(mark)}</div></article>`;
  };

  proto._scheduleLesson = function (lesson) {
    const [text, cls, mark] = this._attendance(lesson.attendance);
    const state = this._mojvLessonState(lesson, new Date());
    return `<div class="schedule-lesson lesson-state-${state}" data-lesson-state="${state}" data-cancelled="${lesson.cancelled ? "true" : "false"}" data-start="${this._e(lesson.start)}" data-end="${this._e(lesson.end)}"><div class="schedule-lesson-top"><span class="lesson-number">${this._e(lesson.number)}</span><strong>${this._e(lesson.subject)}</strong><span class="attendance-mini ${cls}" title="${this._e(text)}">${this._e(mark)}</span></div><div class="schedule-lesson-meta">${this._e(lesson.room || "bez sali")}${lesson.teacher ? ` · ${this._e(lesson.teacher)}` : ""}</div><div class="badge-row"><span class="lesson-state-badge-slot">${this._mojvLessonStateBadge(state)}</span>${lesson.replacement ? `<span class="badge warn">Zastępstwo</span>` : ""}</div></div>`;
  };

  proto._renderSchedule = function (student) {
    const html = baseRenderSchedule.call(this, student);
    const nextDisabled = this._weekOffset >= 4 ? "disabled" : "";
    return html.replace(
      /<button type="button" class="week-button" data-week="1"(?: disabled)?>›<\/button>/,
      `<button type="button" class="week-button" data-week="1" ${nextDisabled}>›</button>`,
    );
  };

  proto._changeWeek = function (delta) {
    if (delta === 0) this._weekOffset = 0;
    else this._weekOffset = Math.max(-1, Math.min(4, this._weekOffset + delta));
    if (this._activeView === "schedule") this._renderActiveView();
  };

  proto._updateScheduleCurrentClasses = function () {
    const now = new Date();
    this.shadowRoot.querySelectorAll(".schedule-lesson").forEach((element) => {
      const state = this._mojvLessonState({
        start: element.dataset.start,
        end: element.dataset.end,
        cancelled: element.dataset.cancelled === "true",
      }, now);
      for (const name of ["cancelled", "current", "completed", "upcoming"]) {
        element.classList.toggle(`lesson-state-${name}`, state === name);
      }
      element.dataset.lessonState = state;
      const slot = element.querySelector(".lesson-state-badge-slot");
      if (slot) slot.innerHTML = this._mojvLessonStateBadge(state);
    });
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .lesson-state-current{border-color:var(--mv-accent)!important;background:color-mix(in srgb,var(--mv-accent) 16%,var(--mv-soft))!important;box-shadow:inset 3px 0 0 var(--mv-accent)}
      .timeline-row.lesson-state-current{margin:0 -8px;padding:0 8px;border-radius:10px}.lesson-state-current .timeline-dot{background:var(--mv-accent)}
      .lesson-state-completed{background:color-mix(in srgb,var(--mv-muted) 8%,transparent)!important;color:color-mix(in srgb,var(--primary-text-color,#fff) 62%,var(--mv-muted))}.lesson-state-completed .schedule-lesson-meta,.lesson-state-completed .timeline-copy>span{color:var(--mv-muted)}
      .lesson-state-upcoming{background:var(--mv-soft)}
      .lesson-state-cancelled{opacity:1!important;border-color:color-mix(in srgb,var(--mv-bad) 55%,var(--mv-line))!important;background:color-mix(in srgb,var(--mv-bad) 10%,var(--mv-soft))!important;text-decoration-color:var(--mv-bad)}.lesson-state-cancelled .schedule-lesson-top strong,.lesson-state-cancelled .timeline-copy strong{text-decoration:line-through}
      .lesson-state-label.current-state{background:color-mix(in srgb,var(--mv-accent) 20%,transparent);color:var(--mv-accent)}.lesson-state-label.muted-state{background:var(--mv-soft);color:var(--mv-muted)}.lesson-state-badge-slot:empty{display:none}
    `;
  };
}
