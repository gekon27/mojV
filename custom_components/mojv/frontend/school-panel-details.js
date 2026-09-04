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

  proto._openMojvDetail = function (detail) {
    this._closeMojvDetail(false);
    this.__mojvDetailReturnFocus = this.shadowRoot.activeElement;
    const overlay = document.createElement("div");
    overlay.className = "mojv-detail-overlay";
    overlay.dataset.mojvDetailOverlay = "true";
    const meta = [detail.kind, detail.subject, detail.date].filter(Boolean);
    overlay.innerHTML = `<div class="mojv-detail-backdrop" data-mojv-detail-close="true"></div>
      <section class="mojv-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="mojv-detail-title">
        <header class="mojv-detail-head">
          <div>${meta.length ? `<small>${meta.map((item) => this._e(item)).join(" · ")}</small>` : ""}<h2 id="mojv-detail-title">${this._e(detail.title || "Szczegóły")}</h2></div>
          <button type="button" class="mojv-detail-close" data-mojv-detail-close="true" aria-label="Zamknij szczegóły">×</button>
        </header>
        <div class="mojv-detail-body">${this._detailBodyMarkup(detail.body)}</div>
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
      return {
        title: item.title || this._workKind(item.kind),
        kind: this._workKind(item.kind),
        subject: item.subject || "Bez przedmiotu",
        date: this._date(item.date, true),
        body: item.description,
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
    const items = [...(student.schoolwork || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
    const upcoming = items.filter((item) => new Date(item.date) >= now);
    const past = items.filter((item) => new Date(item.date) < now).reverse().slice(0, 12);
    const renderRows = (rows) => rows.map((item) => {
      const date = new Date(item.date);
      const days = Math.ceil((this._dayStart(date) - now) / 86400000);
      const due = days === 0 ? "Dzisiaj" : days === 1 ? "Jutro" : days > 1 ? `Za ${days} dni` : "Minęło";
      const preview = this._detailPreview(item.description, 120);
      return `<button type="button" class="work-row mojv-detail-trigger" data-mojv-detail-kind="schoolwork" data-mojv-detail-id="${this._e(item.id)}" aria-label="Pokaż szczegóły: ${this._e(item.title || this._workKind(item.kind))}"><span class="work-date"><strong>${date.toLocaleDateString("pl-PL", { day: "2-digit" })}</strong><span>${date.toLocaleDateString("pl-PL", { month: "short" })}</span></span><span class="work-copy"><span><span class="work-kind">${this._e(this._workKind(item.kind))}</span><strong>${this._e(item.title || this._workKind(item.kind))}</strong></span><span>${this._e(item.subject || "Bez przedmiotu")}</span>${preview ? `<p>${this._e(preview)}</p>` : `<p class="mojv-preview-empty">Brak dodatkowej treści</p>`}</span><span class="due-pill ${days <= 1 && days >= 0 ? "soon" : days < 0 ? "past" : ""}">${this._e(due)}</span></button>`;
    }).join("");
    return `<div class="schoolwork-layout" data-view="schoolwork">
      <section class="card schoolwork-card"><div class="section-head"><div><span class="kicker">Terminarz</span><h2>Nadchodzące</h2></div><span>${upcoming.length}</span></div>${upcoming.length ? `<div class="work-list">${renderRows(upcoming)}</div>` : `<div class="mini-empty roomy">Brak nadchodzących sprawdzianów i zadań.</div>`}</section>
      ${past.length ? `<section class="card schoolwork-card muted-card"><div class="section-head"><div><span class="kicker">Historia</span><h2>Ostatnie terminy</h2></div></div><div class="work-list">${renderRows(past)}</div></section>` : ""}
    </div>`;
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .work-row.mojv-detail-trigger{width:100%;border:0;border-bottom:1px solid var(--mv-line);border-radius:0;background:transparent;color:inherit;text-align:left;cursor:pointer;padding:0}.work-row.mojv-detail-trigger:last-child{border-bottom:0}.work-row.mojv-detail-trigger:hover,.work-row.mojv-detail-trigger:focus-visible{background:color-mix(in srgb,var(--mv-accent) 7%,transparent);outline:none}.work-row.mojv-detail-trigger .work-date,.work-row.mojv-detail-trigger .work-copy,.work-row.mojv-detail-trigger .due-pill{display:block}.work-row.mojv-detail-trigger .work-copy>span:first-child{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.mojv-preview-empty{font-style:italic}
      .mojv-detail-overlay{position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:24px}.mojv-detail-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.58);backdrop-filter:blur(3px)}.mojv-detail-dialog{position:relative;z-index:1;width:min(720px,100%);max-height:min(82vh,820px);display:flex;flex-direction:column;background:var(--mv-card);border:1px solid var(--mv-line);border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.35);overflow:hidden}.mojv-detail-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:18px 20px;border-bottom:1px solid var(--mv-line)}.mojv-detail-head small{display:block;color:var(--mv-muted);font-size:10px;margin-bottom:5px}.mojv-detail-head h2{margin:0;font-size:20px}.mojv-detail-close{width:40px;height:40px;flex:0 0 auto;border:1px solid var(--mv-line);border-radius:12px;background:var(--mv-soft);font-size:24px;line-height:1;cursor:pointer}.mojv-detail-close:focus-visible{outline:2px solid var(--mv-accent);outline-offset:2px}.mojv-detail-body{overflow:auto;padding:18px 20px;white-space:normal}.mojv-detail-body p{margin:0 0 12px;line-height:1.6;white-space:pre-wrap}.mojv-detail-body p:last-child{margin-bottom:0}.mojv-detail-empty{color:var(--mv-muted);font-style:italic}
      @media(max-width:760px){.mojv-detail-overlay{align-items:end;padding:0}.mojv-detail-dialog{width:100%;max-height:88vh;border-radius:18px 18px 0 0;border-bottom:0}.mojv-detail-head,.mojv-detail-body{padding-left:16px;padding-right:16px}}
    `;
  };
}
