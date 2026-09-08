import "./school-panel-lesson-states.js?v=0.15.11";

const PanelClass = customElements.get("mojv-school-panel");
const proto = PanelClass?.prototype;

if (proto && !proto.__mojvCustomSchedulePatched) {
  proto.__mojvCustomSchedulePatched = true;
  const baseConnectedCallback = proto.connectedCallback;
  const baseStyles = proto._styles;

  proto.connectedCallback = function () {
    const result = baseConnectedCallback.call(this);
    if (!this.__mojvCustomScheduleBound) {
      this.__mojvCustomScheduleBound = true;
      this.shadowRoot.addEventListener("click", async (event) => {
        const add = event.target.closest?.("[data-mojv-add-custom]");
        if (add) {
          event.preventDefault();
          this._openCustomScheduleDialog();
          return;
        }
        const remove = event.target.closest?.("[data-mojv-remove-custom]");
        if (remove) {
          event.preventDefault();
          await this._removeCustomSchedule(remove.dataset.mojvRemoveCustom);
        }
      });
      this.shadowRoot.addEventListener("submit", async (event) => {
        if (!(event.target instanceof HTMLFormElement) || event.target.dataset.mojvCustomSchedule !== "true") return;
        event.preventDefault();
        const submit = event.target.querySelector("button[type=submit]");
        if (submit) submit.disabled = true;
        try {
          const values = new FormData(event.target);
          await this._hass.callWS({
            type: "mojv/custom_schedule",
            action: "add",
            event: {
              student_id: this._activeStudentId || "",
              subject: String(values.get("subject") || ""),
              weekday: Number(values.get("weekday")),
              start: String(values.get("start") || ""),
              end: String(values.get("end") || ""),
              room: String(values.get("room") || ""),
              note: String(values.get("note") || ""),
            },
          });
          this._closeCustomScheduleDialog();
          await this._refresh();
        } catch (error) {
          const message = event.target.querySelector("[data-mojv-custom-error]");
          if (message) message.textContent = `Nie zapisano: ${String(error)}`;
          if (submit) submit.disabled = false;
        }
      });
    }
    return result;
  };

  proto._openCustomScheduleDialog = function () {
    const student = this._activeStudent();
    if (!student) return;
    this._closeCustomScheduleDialog();
    const options = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"];
    const dialog = document.createElement("div");
    dialog.className = "mojv-custom-overlay";
    dialog.dataset.mojvCustomOverlay = "true";
    dialog.innerHTML = `<div class="mojv-custom-backdrop" data-mojv-close-custom="true"></div><section class="mojv-custom-dialog" role="dialog" aria-modal="true" aria-label="Dodaj zajęcia dodatkowe"><form data-mojv-custom-schedule="true"><div class="mojv-custom-head"><div><span class="kicker">Własny plan</span><h2>Dodaj zajęcia</h2><p>${this._e(student.name)}</p></div><button type="button" class="icon-button" data-mojv-close-custom="true" aria-label="Zamknij">×</button></div><div class="mojv-custom-fields"><label>Nazwa zajęć<input name="subject" required maxlength="160" placeholder="np. Szachy"></label><label>Dzień<select name="weekday">${options.map((label, index) => `<option value="${index}">${label}</option>`).join("")}</select></label><label>Od<input name="start" type="time" required value="15:00"></label><label>Do<input name="end" type="time" required value="16:00"></label><label>Sala / miejsce<input name="room" maxlength="160" placeholder="np. sala 12"></label><label>Notatka<input name="note" maxlength="160" placeholder="opcjonalnie"></label></div><p class="mojv-custom-error" data-mojv-custom-error></p><div class="mojv-custom-actions"><button type="button" class="mojv-print-button" data-mojv-close-custom="true">Anuluj</button><button type="submit" class="mojv-custom-primary">Zapisz lokalnie w Home Assistant</button></div></form></section>`;
    dialog.addEventListener("click", (event) => {
      if (event.target.closest?.("[data-mojv-close-custom]")) this._closeCustomScheduleDialog();
    });
    this.shadowRoot.append(dialog);
    dialog.querySelector("input[name=subject]")?.focus();
  };

  proto._closeCustomScheduleDialog = function () {
    this.shadowRoot.querySelector("[data-mojv-custom-overlay]")?.remove();
  };

  proto._removeCustomSchedule = async function (eventId) {
    if (!eventId || !window.confirm("Usunąć te własne zajęcia z planu?")) return;
    await this._hass.callWS({ type: "mojv/custom_schedule", action: "remove", id: eventId });
    await this._refresh();
  };

  proto._styles = function () {
    return `${baseStyles.call(this)}
      .mojv-custom-overlay{position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:24px}.mojv-custom-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.58);backdrop-filter:blur(3px)}.mojv-custom-dialog{position:relative;z-index:1;width:min(620px,100%);background:var(--mv-card);border:1px solid var(--mv-line);border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.35);overflow:hidden}.mojv-custom-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:18px 20px;border-bottom:1px solid var(--mv-line)}.mojv-custom-head h2{margin:4px 0 0;font-size:20px}.mojv-custom-head p{margin:5px 0 0;color:var(--mv-muted);font-size:12px}.mojv-custom-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:20px}.mojv-custom-fields label{display:grid;gap:6px;color:var(--mv-muted);font-size:11px;font-weight:700}.mojv-custom-fields input,.mojv-custom-fields select{min-height:40px;padding:0 10px;border:1px solid var(--mv-line);border-radius:10px;background:var(--mv-soft);color:var(--primary-text-color,#fff);font:inherit}.mojv-custom-error{min-height:18px;margin:0 20px;color:var(--mv-bad);font-size:11px}.mojv-custom-actions{display:flex;justify-content:flex-end;gap:8px;padding:16px 20px;border-top:1px solid var(--mv-line)}.mojv-custom-primary{min-height:36px;padding:0 12px;border:0;border-radius:10px;background:var(--mv-accent);color:#fff;cursor:pointer;font-weight:750}.mojv-custom-primary:disabled{opacity:.5}@media(max-width:620px){.mojv-custom-overlay{align-items:end;padding:0}.mojv-custom-dialog{width:100%;border-radius:18px 18px 0 0}.mojv-custom-fields{grid-template-columns:1fr}.mojv-custom-actions{flex-direction:column-reverse}.mojv-custom-actions button{width:100%}}
    `;
  };
}
