/* Minimal stand-in for the Claude Data `dash` API, so templates/sverige_index.html runs as a plain static page
 * (GitHub Pages). Implements only what that page uses:
 *   dash.data(id)        -> {status: "loading" | "ok" | "error", data: rows}; reads data/<id>.json ({rows, meta})
 *   dash.calc(id, spec)  -> derived dataset: spec.fn(...rows of spec.inputs), read with dash.data(id)
 *   dash.draw(name, fn)  -> registers fn(el) for every [data-draw=name]; dash.draw(name) redraws it now
 *   dash.colors          -> categorical palette as CSS variables (theme follows light/dark automatically)
 * Every draw is rerun when a dataset arrives and when the window width changes.
 */
(function () {
  "use strict";
  const DATA_DIR = "data/";
  const files = new Map(); // id -> {status, data}
  const calcs = new Map(); // id -> {inputs, fn, key, value}
  const draws = new Map(); // name -> fn
  const LOADING = Object.freeze({ status: "loading", data: null });

  function load(id) {
    const entry = { status: "loading", data: null };
    files.set(id, entry);
    fetch(DATA_DIR + encodeURIComponent(id) + ".json", { cache: "no-cache" })
      .then((r) => { if (!r.ok) throw new Error(id + ": HTTP " + r.status); return r.json(); })
      .then((j) => {
        if (!Array.isArray(j.rows)) throw new Error(id + ": no rows");
        entry.status = "ok"; entry.data = j.rows;
      })
      .catch((e) => { console.error("dash-shim:", e); entry.status = "error"; entry.data = null; })
      .then(scheduleAll);
    return entry;
  }

  function data(id) {
    const c = calcs.get(id);
    if (!c) return files.get(id) || load(id);
    const ins = c.inputs.map(data);
    if (ins.some((d) => d.status === "error")) return { status: "error", data: null };
    if (ins.some((d) => d.status !== "ok")) return LOADING;
    const key = ins.map((d) => d.data);
    if (!c.key || c.key.some((k, i) => k !== key[i])) {
      c.key = key;
      try { c.value = { status: "ok", data: c.fn(...key) }; }
      catch (e) { console.error("dash-shim: calc " + id, e); c.value = { status: "error", data: null }; }
    }
    return c.value;
  }

  function calc(id, spec) {
    calcs.set(id, { inputs: spec.inputs || [], fn: spec.fn, key: null, value: null });
    scheduleAll();
  }

  function run(name) {
    const fn = draws.get(name);
    if (!fn) return;
    document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => {
      try { fn(el); } catch (e) { console.error("dash-shim: draw " + name, e); }
    });
  }

  function draw(name, fn) {
    if (typeof fn === "function") { draws.set(name, fn); scheduleAll(); return; }
    run(name);
  }

  let pending = false;
  function scheduleAll() {
    if (pending) return;
    pending = true;
    const go = () => { pending = false; for (const name of draws.keys()) run(name); };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go, { once: true });
    else setTimeout(go, 0); // not requestAnimationFrame: it never fires in a background tab
  }

  let lastW = window.innerWidth, timer = null;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastW) return; // ignore height-only changes (mobile toolbars)
    lastW = window.innerWidth;
    clearTimeout(timer);
    timer = setTimeout(scheduleAll, 150);
  });

  const colors = ["--sv-c1", "--sv-c2", "--sv-c3", "--sv-c4", "--sv-c5", "--sv-c6"].map((v) => "var(" + v + ")");
  window.dash = { data, calc, draw, colors };
})();
