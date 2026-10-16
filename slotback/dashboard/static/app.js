// Slotback dashboard: replay, tamper, verify upload, ROI model, kill switch, widget session.
// Vanilla JS, no build step. Respects prefers-reduced-motion.
(() => {
  const $ = (s) => document.querySelector(s);
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const STATIC = document.documentElement.dataset.static === "1";

  // ── Impact replay: end state first (design 3A), press to replay ──
  const data = $("#replay-data");
  const btn = $("#replay-btn");
  if (data && btn) {
    const events = JSON.parse(data.textContent);
    const counter = $("#recovered");
    const list = $("#ledger-list");
    const marks = [...document.querySelectorAll(".tl .mk")];
    let timer = null, i = 0, filled = 0, lastAnnounce = 0;
    const label = (e) => `${e.care ? "◆ " : ""}${e.type}${e.rank ? " · r" + e.rank : ""}` +
      `${e.outcome ? " · " + e.outcome.replace("_", " ") : ""}`;
    const reset = () => {
      i = 0; filled = 0; counter.textContent = "0"; list.innerHTML = "";
      marks.forEach((m) => { m.dataset.final = m.dataset.final || m.className + "|" + m.textContent;
        m.style.visibility = "hidden"; });
    };
    const step = () => {
      if (i >= events.length) { stop(true); return; }
      const e = events[i++];
      const li = document.createElement("li");
      li.className = (e.care ? "care-ev" : "") + (e.type === "slot_filled" ? " fill" : "");
      li.innerHTML = `<span class="n">#${e.seq}</span><span class="t">${e.ts} · ${label(e)}</span>`;
      list.prepend(li);
      while (list.children.length > 14) list.lastChild.remove();
      const mk = marks.find((m) => m.dataset.slot === e.slot);
      if (mk && e.type === "slot_freed") { mk.style.visibility = "visible"; mk.className = "mk freed"; mk.textContent = "⟳"; }
      if (mk && e.type === "slot_filled") { const [c, t] = mk.dataset.final.split("|"); mk.className = c; mk.textContent = t; }
      if (mk && e.type === "slot_unfilled") { mk.className = "mk un"; mk.textContent = "✕"; }
      if (e.type === "slot_filled") {
        filled++;
        const now = Date.now();
        if (now - lastAnnounce > 5000 || i === events.length) { counter.textContent = filled; lastAnnounce = now; }
        else counter.textContent = filled;
      }
    };
    const stop = (done) => {
      clearInterval(timer); timer = null;
      btn.textContent = btn.dataset.labelPlay;
      if (done) { counter.textContent = counter.dataset.final; marks.forEach((m) => (m.style.visibility = "visible")); }
    };
    btn.addEventListener("click", () => {
      if (timer) { stop(false); return; }
      if (i === 0 || i >= events.length) reset();
      btn.textContent = btn.dataset.labelPause;
      if (reduced) { while (i < events.length) step(); stop(true); return; }
      timer = setInterval(step, Math.max(20, 60000 / events.length));
    });
  }

  // ── Tamper with one event (in-memory copy on the server) ──
  const tamper = $("#tamper-btn"), restore = $("#restore-btn"), out = $("#tamper-result"), chain = $("#chain-status");
  if (tamper) {
    const original = chain.textContent, originalClass = chain.className;
    tamper.addEventListener("click", async () => {
      tamper.disabled = true;
      const seq = Number(tamper.dataset.seq);
      const r = STATIC ? await fetch("tamper.json") : await fetch("/api/demo/tamper", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ seq }) });
      const rep = await r.json();
      const c = rep.checks.chain;
      chain.textContent = "✕ Chain broken"; chain.className = "chain-bad";
      out.hidden = false; out.className = "alert err";
      out.innerHTML = `<b>Chain broken at #${c.seq}.</b> ${c.detail}. Only an in-memory copy was changed; the stored ledger is intact.`;
      document.querySelectorAll(`#ledger-list li[data-seq="${c.seq}"]`).forEach((li) => li.classList.add("bad"));
      restore.hidden = false; restore.focus();
    });
    restore.addEventListener("click", () => {
      chain.textContent = original; chain.className = originalClass;
      out.hidden = true; restore.hidden = true; tamper.disabled = false; tamper.focus();
      document.querySelectorAll("#ledger-list li.bad").forEach((li) => li.classList.remove("bad"));
    });
  }

  // ── Verify upload ──
  const vf = $("#verify-form");
  if (vf) {
    const outList = $("#verify-out"), prog = $("#verify-progress");
    ["dragover", "dragleave", "drop"].forEach((ev) => vf.addEventListener(ev, (e) => {
      e.preventDefault(); vf.classList.toggle("over", ev === "dragover");
      if (ev === "drop" && e.dataTransfer.files[0]) { $("#bundle").files = e.dataTransfer.files; vf.requestSubmit(); }
    }));
    vf.addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = $("#bundle").files[0];
      if (!f) return;
      const fd = new FormData(); fd.append("file", f);
      const key = $("#trusted").value.trim();
      prog.hidden = false; prog.textContent = `Checking ${f.name}…`; outList.innerHTML = "";
      const r = await fetch("/api/verify" + (key ? "?trusted_key=" + encodeURIComponent(key) : ""), { method: "POST", body: fd });
      const rep = await r.json();
      prog.hidden = true;
      if (!r.ok) { outList.innerHTML = `<li><span class="st un">✕ ${rep.error || "Upload failed"}</span></li>`; return; }
      outList.innerHTML = `<li><b class="${rep.ok ? "chain-ok" : "chain-bad"}">${rep.ok ? "✓ Passed" : "✕ Failed"}</b> · ${rep.events} events</li>` +
        Object.entries(rep.checks).map(([k, c]) => {
          const cls = c.status === "pass" ? "st ok" : c.status === "fail" ? "st un" : "st neutral";
          const icon = c.status === "pass" ? "✓" : c.status === "fail" ? "✕" : "–";
          return `<li><span class="${cls}">${icon} ${k}</span> ${c.seq ? "at #" + c.seq + " · " : ""}<span class="muted">${c.detail}</span></li>`;
        }).join("");
    });
  }

  // ── Static snapshot: precomputed verifier report for the sample bundle ──
  const sr = $("#static-report");
  if (sr) fetch(sr.dataset.src).then((r) => r.json()).then((rep) => {
    sr.innerHTML = `<li><b class="${rep.ok ? "chain-ok" : "chain-bad"}">${rep.ok ? "✓ Passed" : "✕ Failed"}</b> · ${rep.events} events</li>` +
      Object.entries(rep.checks).map(([k, c]) => `<li><span class="${c.status === "pass" ? "st ok" : "st un"}">${c.status === "pass" ? "✓" : "✕"} ${k}</span> <span class="muted">${c.detail}</span></li>`).join("");
  });

  // ── ROI model (formulas mirror docs/04_business_case.md) ──
  const roi = $("#roi-inputs");
  if (roi) {
    const v = (id) => Number($("#in-" + id).value);
    const eur = (x) => "€" + Math.round(x).toLocaleString("en-GB");
    const n = (x) => Math.round(x).toLocaleString("en-GB");
    const calc = () => {
      roi.querySelectorAll("input[type=range]").forEach((el) => {
        $("#out-" + el.id.slice(3)).textContent = Number(el.value).toLocaleString("en-GB") + (el.dataset.unit || "");
      });
      const missed = v("appointments") * v("noshow") / 100;
      const freed = missed * v("contact") / 100 * v("cancel") / 100;
      const filled = freed * v("fill") / 100;
      const billable = Math.max(0, filled - freed * v("baseline") / 100);
      const value = billable * v("cost");
      const pay = billable * v("price") + v("platform");
      $("#r-missed").textContent = n(missed); $("#r-freed").textContent = n(freed);
      $("#r-filled").textContent = n(filled); $("#r-slots").textContent = n(billable);
      $("#r-value").textContent = eur(value); $("#r-pay").textContent = eur(pay);
      $("#r-net").textContent = eur(value - pay);
      $("#r-breakeven").textContent = billable > 0 ? eur((value - v("platform")) / billable) : "—";
    };
    roi.addEventListener("input", calc); calc();
  }

  // ── Kill switch ──
  const kf = $("#kill-form");
  if (kf) kf.addEventListener("submit", async (e) => {
    e.preventDefault();
    const paused = kf.dataset.paused !== "true";
    const r = await fetch(`/api/kill-switch?access_code=${encodeURIComponent($("#kill-code").value)}&paused=${paused}`, { method: "POST" });
    $("#kill-msg").textContent = r.ok ? (paused ? "Calling paused." : "Calling resumed.") : "Wrong access code.";
    if (r.ok) setTimeout(() => location.reload(), 600);
  });

  // ── Try: start a widget session ──
  const sf = $("#session-form");
  if (sf) sf.addEventListener("submit", async (e) => {
    e.preventDefault();
    const r = await fetch("/api/sessions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: $("#code").value }) });
    const msg = $("#session-msg");
    if (!r.ok) { msg.textContent = r.status === 429 ? "Too many sessions, try again in a minute." : "Wrong access code."; return; }
    const s = await r.json();
    const slot = $("#widget-slot");
    const w = document.createElement("elevenlabs-convai");
    w.setAttribute("agent-id", slot.dataset.agentId);
    w.setAttribute("dynamic-variables", JSON.stringify({ secret__call_token: s.call_token, call_id: s.call_id }));
    slot.replaceChildren(w);
    if (!document.querySelector("script[data-convai]")) {
      const sc = document.createElement("script");
      sc.src = "https://unpkg.com/@elevenlabs/convai-widget-embed"; sc.async = true; sc.dataset.convai = "1";
      document.body.appendChild(sc);
    }
    msg.textContent = "Session ready. Press the call button.";
  });
})();
