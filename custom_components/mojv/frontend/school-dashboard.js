import "./school-panel-hub.js";

class MojVSchoolDashboard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._panel = null;
    this._narrow = false;
    this._inner = null;
  }

  set hass(value) {
    this._hass = value;
    this._sync();
  }

  set narrow(value) {
    this._narrow = Boolean(value);
    this._sync();
  }

  set panel(value) {
    this._panel = value;
    this._sync();
  }

  connectedCallback() {
    if (!this._inner) {
      this.shadowRoot.innerHTML = `<style>:host{display:block;min-height:100vh;background:var(--primary-background-color,#0b1118)}.dashboard-shell{min-height:100vh;width:100%}</style><div class="dashboard-shell"></div>`;
      this._inner = document.createElement("mojv-school-panel");
      this._inner.style.display = "block";
      this._inner.style.width = "100%";
      this._inner.style.minHeight = "100vh";
      this.shadowRoot.querySelector(".dashboard-shell").appendChild(this._inner);
    }
    this._sync();
  }

  _sync() {
    if (!this._inner) return;
    if (this._hass) this._inner.hass = this._hass;
    this._inner.narrow = false;
    if (this._panel) this._inner.panel = this._panel;
  }
}

if (!customElements.get("mojv-school-dashboard")) customElements.define("mojv-school-dashboard", MojVSchoolDashboard);
