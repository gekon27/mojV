import "./school-panel-hub-base.js";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvDetailUxPatched) {
  proto.__mojvDetailUxPatched = true;

  const baseConnectedCallback = proto.connectedCallback;
  const baseStyles = proto._styles;

  proto._detailPreview = function (value, limit = 120) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length <= limit ? text : `${text.slice(0, limit - 1).trimEnd()}…`;
  };

  proto._detailBodyMarkup = function (value) {
    const text = String(value || "").replace(/\r\n?/g, "\n").trim();
    if (!text) return `<p class="mojv-detail-empty">Brak dodatkowej treści.</p>`;
    return text
      .split(/\n{2,}/)
      .map((paragraph) => `<p>${this._e(paragraph.replace(/\n/g, " "))}</p>`)
      .join("");
  };

  proto._mojvDateTime = function (value) {
    if (!value) return "Brak danych z portalu";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "Brak danych z portalu";
    return `${this._date(value, true)} · ${this._time(value)}`;
  };

  proto._openMojvDetail = function (detail) {
    this._closeMojvDetail(false);
    this.__mojvDetailReturnFocus = this.shadowRoot.activeElement;
    const overlay = document.createElement("div");
    overlay.className = "mojv-detail-overlay";
    overlay.dataset.mojvDetailOverlay = "true";
    const meta = [detail.kind, detail.subject, detail.date].filter(Boolean);
    const fields = Array.isArray(detail.fields) ? detail.fields : [];
    const fieldsMarkup = fields.length
      ? `<dl class="mojv-detail-fields">${fields.map(([label, value]) => `<div><dt>${this._e(label)}</dt><dd>${this._e(value || "Brak danych z portalu")}</dd></div>`).join("")}</dl>`
      : "";
    overlay.innerHTML = `<div class="mojv-detail-backdrop" data-mojv-detail-close="true"></div>
      <section class="mojv-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="mojv-detail-title">
        <header class="mojv-detail-head">
          <div>${meta.length ? `<small>${meta.map((item) => this._e(item)).join(" · ")}</small>` : ""}<h2 id="mojv-detail-title">${this._e(detail.title || "Szczegóły")}</h2></div>
          <button type="button" class="mojv-detail-close" data-mojv-detail-close="true" aria-label="Zamknij szczegóły">×</button>
        </header>
        <div class="mojv-detail-body">${fieldsMarkup}<section class="mojv-detail-description"><small>Opis</small>${this._detailBodyMarkup(detail.body)}</section></div>
      </section>`;
    this.shadowRoot.appendChild(overlay);
    window.requestAnimationFrame(() => overlay.querySelector(".mojv-detail-close")?.focus());
  };

  proto._closeMojvDetail = function (restoreFocus = true) {
    const overlay = this.shadowRoot.querySelector("[data-mojv-detail-overlay]");
    if (overlay) overlay.remove();
    if (restoreFocus && this.__mojvDetailReturnFocus?.focus) {
      this.__mojvDetailReturnFocus.focus();
    }
    this.__mojvDetailReturnFocus = null;
  };

  proto._resolveMojvDetail = function (trigger) {
    const student = this._activeStudent();
    if (!student) return null;
    if (trigger.dataset.mojvDetailKind === "schoolwork") {
      const item = (student.schoolwork || []).find((row) => String(row.id) === trigger.dataset.mojvDetailId);
      if (!item) return null;
      const kind = this._workKind(item.kind);
      const dueAt = item.due_at || item.date;
      return {
        title: item.title || kind,
        kind,
        subject: item.subject || "Bez przedmiotu",
        date: dueAt ? this._date(dueAt, true) : "",
        body: item.description,
        fields: [
          ["Typ", kind],
          ["Przedmiot", item.subject || "Brak danych z portalu"],
          ["Nauczyciel", item.teacher || "Brak danych z portalu"],
          ["Utworzone", this._mojvDateTime(item.created_at)],
          ["Termin", this._mojvDateTime(dueAt)],
        ],
      };
    }
    if (trigger.dataset.mojvDetailKind === "important") {
      const index = Number(trigger.dataset.mojvDetailIndex);
      const item = (student.important_today || [])[index];
      if (!item) return null;
      return {
        title: item.title || item.kind || "Ważne",
        kind: item.kind || "Informacja",
        subject: item.subject || "",
        date: "",
        body: item.description,
      };
    }
    return null;
  };

  proto.connectedCallback = function () {
    const result = baseConnectedCallback.call(this);
    if (!this.__mojvDetailEventsBound) {
      this.__mojvDetailEventsBound = true;
      this.shadowRoot.addEventListener("click", (event) => {
        const close = event.target.closest?.("[data-mojv-detail-close]");
        if (close) {
          event.preventDefault();
          this._closeMojvDetail();
          return;
        }
        const trigger = event.target.closest?.(".mojv-detail-trigger");
        if (!trigger) return;
        const detail = this._resolveMojvDetail(trigger);
        if (detail) {
          event.preventDefault();
          this._openMojvDetail(detail);
        }
      });
      this.shadowRoot.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && this.shadowRoot.querySelector("[data-mojv-detail-overlay]")) {
          event.preventDefault();
          this._closeMojvDetail();
        }
      });
    }
    return result;
  };

  proto._renderSchoolwork = function (student) {
    const now = this._dayStart(new Date());
    const itemDate = (item) => new Date(item.due_at || item.date);
    const items = [...(student.schoolwork || [])].sort((a, b) => itemDate(a) - itemDate(b));
    const upcoming = items.filter((item) => itemDate(item) >= now);
    const past = items.filter((item) => itemDate(item) < now).reverse().slice(0, 12);
    const renderRows = (rows) => rows.map((item) => {
      const dueAt = item.due_at || item.date;
      const date = new Date(dueAt);
      const days = Math.ceil((this._dayStart(date) - now) / 86400000);
      const due = days === 0 ? "Dzisiaj" : days === 1 ? "Jutro" : days > 1 ? `Za ${days} dni` : "Minęło";
      const preview = this._detailPreview(item.description, 160);
      const teacher = item.teacher || "Brak danych z portalu";
      const created = this._mojvDateTime(item.created_at);
      const deadline = this._mojvDateTime(dueAt);
      return `<button type="button" class="work-row mojv-detail-trigger" data-mojv-detail-kind="schoolwork" data-mojv-detail-id="${this._e(item.id)}" aria-label="Pokaż szczegóły: ${this._e(item.title || this._workKind(item.kind))}">
        <span class="work-date"><strong>${date.toLocaleDateString("pl-PL", { day: "2-digit" })}</strong><span>${date.toLocaleDateString("pl-PL", { month: "short" })}</span></span>
        <span class="work-copy">
          <span><span class="work-kind">${this._e(this._workKind(item.kind))}</span><strong>${this._e(item.title || this._workKind(item.kind))}</strong></span>
          <span class="work-meta-line"><b>Przedmiot:</b> ${this._e(item.subject || "Brak danych z portalu")} · <b>Nauczyciel:</b> ${this._e(teacher)}</span>
          <span class="work-meta-line"><b>Utworzone:</b> ${this._e(created)} · <b>Termin:</b> ${this._e(deadline)}</span>
          ${preview ? `<p><b>Opis:</b> ${this._e(preview)}</p>` : `<p class="mojv-preview-empty"><b>Opis:</b> Brak dodatkowej treści</p>`}
        </span>
        <span class="due-pill ${days <= 1 && days >= 0 ? "soon" : days < 0 ? "past" : ""}">${this._e(due)}</span>
      </button>`;
    }).join("");
    return `<div class="schoolwork-layout" data-view="schoolwork">
      <section class="card schoolwork-card"><div class="section-head"><div><span class="kicker">Terminarz</span><h2>Sprawdziany i zadania domowe</h2></div><span>${upcoming.length}</span></div>${upcoming.length ? `<div class="work-list">${renderRows(upcoming)}</div>` : `<div class="mini-empty roomy">Brak nadchodzących sprawdzianów i zadań.</div>`}</section>
      ${past.length ? `<section class="card schoolwork-card muted-card"><div class="section-head"><div><span class="kicker">Historia</span><h2>Ostatnie terminy</h2></div></div><div class="work-list">${renderRows(past)}</div></section>` : ""}
    </div>`;
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .work-row.mojv-detail-trigger{width:100%;min-height:112px;border:0;border-bottom:1px solid var(--mv-line);border-radius:0;background:transparent;color:inherit;text-align:left;cursor:pointer;padding:8px 0}.work-row.mojv-detail-trigger:last-child{border-bottom:0}.work-row.mojv-detail-trigger:hover,.work-row.mojv-detail-trigger:focus-visible{background:color-mix(in srgb,var(--mv-accent) 7%,transparent);outline:none}.work-row.mojv-detail-trigger .work-date,.work-row.mojv-detail-trigger .work-copy,.work-row.mojv-detail-trigger .due-pill{display:block}.work-row.mojv-detail-trigger .work-copy>span:first-child{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.work-meta-line{margin-top:5px!important;white-space:normal!important;line-height:1.45}.work-meta-line b,.work-copy p b{color:var(--primary-text-color,#fff);font-weight:700}.mojv-preview-empty{font-style:italic}
      .mojv-detail-overlay{position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:24px}.mojv-detail-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.58);backdrop-filter:blur(3px)}.mojv-detail-dialog{position:relative;z-index:1;width:min(760px,100%);max-height:min(84vh,860px);display:flex;flex-direction:column;background:var(--mv-card);border:1px solid var(--mv-line);border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.35);overflow:hidden}.mojv-detail-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:18px 20px;border-bottom:1px solid var(--mv-line)}.mojv-detail-head small{display:block;color:var(--mv-muted);font-size:10px;margin-bottom:5px}.mojv-detail-head h2{margin:0;font-size:20px}.mojv-detail-close{width:40px;height:40px;flex:0 0 auto;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft);font-size:24px;line-height:1;cursor:pointer}.mojv-detail-close:focus-visible{outline:2px solid var(--mv-accent);outline-offset:2px}.mojv-detail-body{overflow:auto;padding:18px 20px;white-space:normal}.mojv-detail-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:0 0 18px}.mojv-detail-fields>div{display:grid;gap:3px;padding:10px 12px;border:1px solid var(--mv-line);border-radius:11px;background:var(--mv-soft)}.mojv-detail-fields dt{color:var(--mv-muted);font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}.mojv-detail-fields dd{margin:0;font-size:12px;font-weight:700}.mojv-detail-description>small{display:block;margin-bottom:7px;color:var(--mv-muted);font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.05em}.mojv-detail-body p{margin:0 0 12px;line-height:1.6;white-space:pre-wrap}.mojv-detail-body p:last-child{margin-bottom:0}.mojv-detail-empty{color:var(--mv-muted);font-style:italic}
      @media(max-width:760px){.mojv-detail-overlay{align-items:end;padding:0}.mojv-detail-dialog{width:100%;max-height:88vh;border-radius:18px 18px 0 0;border-bottom:0}.mojv-detail-head,.mojv-detail-body{padding-left:16px;padding-right:16px}.mojv-detail-fields{grid-template-columns:1fr}.work-row.mojv-detail-trigger{grid-template-columns:44px 1fr}.work-row.mojv-detail-trigger .due-pill{grid-column:2;justify-self:start;margin-top:4px}}
    `;
  };
}
