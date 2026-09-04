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

  proto._mojvScheduleStatus = function (student, now = new Date()) {
    if (this._weekOffset !== 0) {
      return { state: "other-week", label: "Wybrany tydzień", detail: "Wróć do bieżącego tygodnia, aby zobaczyć stan na żywo." };
    }
    const lessons = this._todayLessons(student, now)
      .filter((lesson) => !lesson.cancelled)
      .sort((a, b) => new Date(a.start) - new Date(b.start));
    if (!lessons.length) {
      return { state: "empty", label: "Brak lekcji", detail: "Dzisiaj nie ma lekcji w pobranym planie." };
    }
    const current = lessons.find((lesson) => new Date(lesson.start) <= now && now < new Date(lesson.end));
    if (current) {
      return {
        state: "lesson",
        label: `Teraz · lekcja ${current.number || "—"}`,
        detail: `${current.subject || "Lekcja"} · ${this._time(current.start)}–${this._time(current.end)}`,
      };
    }
    const previous = [...lessons].reverse().find((lesson) => new Date(lesson.end) <= now);
    const next = lessons.find((lesson) => new Date(lesson.start) > now);
    if (previous && next) {
      return {
        state: "break",
        label: "Przerwa",
        detail: `Po lekcji ${previous.number || "—"} · następna: lekcja ${next.number || "—"} ${next.subject || ""} o ${this._time(next.start)}`,
      };
    }
    if (next) {
      return {
        state: "before",
        label: "Przed lekcjami",
        detail: `Pierwsza: lekcja ${next.number || "—"} ${next.subject || ""} o ${this._time(next.start)}`,
      };
    }
    return {
      state: "after",
      label: "Po lekcjach",
      detail: `Ostatnia lekcja zakończyła się o ${this._time(previous?.end)}`,
    };
  };

  proto._mojvScheduleStatusMarkup = function (status) {
    return `<section class="schedule-now-indicator schedule-state-${this._e(status.state)}" data-schedule-now-indicator="true"><span class="schedule-now-dot"></span><div><strong>${this._e(status.label)}</strong><small>${this._e(status.detail)}</small></div></section>`;
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
    let html = baseRenderSchedule.call(this, student);
    const nextDisabled = this._weekOffset >= 2 ? "disabled" : "";
    html = html.replace(
      /<button type="button" class="week-button" data-week="1"(?: disabled)?>›<\/button>/,
      `<button type="button" class="week-button" data-week="1" ${nextDisabled}>›</button>`,
    );
    html = html.replace(
      `›</button></div></div>`,
      `›</button><button type="button" class="mojv-print-button" data-mojv-print="schedule">Drukuj plan</button></div></div>`,
    );
    const status = this._mojvScheduleStatus(student, new Date());
    return html.replace(
      `<div class="schedule-scroll">`,
      `${this._mojvScheduleStatusMarkup(status)}<div class="schedule-scroll">`,
    );
  };

  proto._changeWeek = function (delta) {
    if (delta === 0) this._weekOffset = 0;
    else this._weekOffset = Math.max(-1, Math.min(2, this._weekOffset + delta));
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

    const indicator = this.shadowRoot.querySelector("[data-schedule-now-indicator]");
    const student = this._activeStudent();
    if (indicator && student) {
      const status = this._mojvScheduleStatus(student, now);
      indicator.className = `schedule-now-indicator schedule-state-${status.state}`;
      indicator.innerHTML = `<span class="schedule-now-dot"></span><div><strong>${this._e(status.label)}</strong><small>${this._e(status.detail)}</small></div>`;
    }
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .lesson-state-current{border-color:var(--mv-accent)!important;background:color-mix(in srgb,var(--mv-accent) 18%,var(--mv-soft))!important;box-shadow:inset 4px 0 0 var(--mv-accent)}
      .timeline-row.lesson-state-current{margin:0 -8px;padding:0 8px;border-radius:10px}.lesson-state-current .timeline-dot{background:var(--mv-accent)}
      .lesson-state-completed{background:color-mix(in srgb,var(--mv-muted) 20%,var(--mv-card))!important;border-color:color-mix(in srgb,var(--mv-muted) 35%,var(--mv-line))!important;color:color-mix(in srgb,var(--primary-text-color,#fff) 55%,var(--mv-muted));filter:saturate(.55)}.lesson-state-completed .schedule-lesson-meta,.lesson-state-completed .timeline-copy>span{color:var(--mv-muted)}
      .lesson-state-upcoming{background:var(--mv-soft)}
      .lesson-state-cancelled{opacity:1!important;border-color:color-mix(in srgb,var(--mv-bad) 55%,var(--mv-line))!important;background:color-mix(in srgb,var(--mv-bad) 10%,var(--mv-soft))!important;text-decoration-color:var(--mv-bad)}.lesson-state-cancelled .schedule-lesson-top strong,.lesson-state-cancelled .timeline-copy strong{text-decoration:line-through}
      .lesson-state-label.current-state{background:color-mix(in srgb,var(--mv-accent) 20%,transparent);color:var(--mv-accent)}.lesson-state-label.muted-state{background:var(--mv-soft);color:var(--mv-muted)}.lesson-state-badge-slot:empty{display:none}
      .schedule-now-indicator{display:grid;grid-template-columns:12px minmax(0,1fr);gap:10px;align-items:center;margin:12px 18px 0;padding:10px 13px;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft)}.schedule-now-indicator>div{display:grid;gap:2px}.schedule-now-indicator strong{font-size:12px}.schedule-now-indicator small{color:var(--mv-muted);font-size:10px}.schedule-now-dot{width:10px;height:10px;border-radius:50%;background:var(--mv-muted)}.schedule-state-lesson{border-color:color-mix(in srgb,var(--mv-accent) 50%,var(--mv-line));background:color-mix(in srgb,var(--mv-accent) 12%,var(--mv-card))}.schedule-state-lesson .schedule-now-dot{background:var(--mv-accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--mv-accent) 15%,transparent)}.schedule-state-break{border-color:color-mix(in srgb,var(--mv-warn) 60%,var(--mv-line));background:color-mix(in srgb,var(--mv-warn) 13%,var(--mv-card))}.schedule-state-break .schedule-now-dot{background:var(--mv-warn);box-shadow:0 0 0 4px color-mix(in srgb,var(--mv-warn) 15%,transparent)}.schedule-state-before .schedule-now-dot,.schedule-state-after .schedule-now-dot{background:var(--mv-good)}
      .mojv-print-button{min-height:44px;padding:0 12px;border:1px solid var(--mv-line);border-radius:13px;background:var(--mv-card);cursor:pointer;font-size:10px;font-weight:750;white-space:nowrap}.mojv-print-button:hover,.mojv-print-button:focus-visible{border-color:var(--mv-accent);outline:none}
      @media(max-width:760px){.schedule-now-indicator{margin:10px 12px 0}.mojv-print-button{min-height:40px}}
    `;
  };
}
