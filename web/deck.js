/* slidekit feedback site — the DECK REVIEW page.
 *
 * Data: web/data/decks.json — every showcase deck rendered slide-by-slide from the SAME
 * geometry-driven HTML the layout gallery uses (scripts/build_web_decks.py; no screenshots).
 *
 * You pick a deck, scroll its slides, and comment on any of them. Each comment is SCOPED:
 *   - "slide"  → fix THIS slide of THIS deck (a deck-specific change).
 *   - "layout" → fix the reusable component + theme so EVERY future deck benefits.
 * Submitting POSTs to the same Netlify function as the layout queue; the CI fold records
 * each mark in ops/FEEDBACK.yaml (slide-scoped marks tagged with the deck + slide index),
 * while layout-scoped marks also drive the layout review queue exactly as before.
 */
(function () {
  "use strict";

  var decksById = {};      // stem -> deck object
  var current = null;      // current deck object
  var state = {};          // "stem::index" -> { verdict, comment, severity, scope }

  var deckEl = document.getElementById("deck");
  var pickEl = document.getElementById("deckpick");
  var submitBtn = document.getElementById("submit");
  var pendingEl = document.getElementById("pending");
  var countsEl = document.getElementById("counts");

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  function key(stem, idx) { return stem + "::" + idx; }

  function isMarked(s) { return s.verdict || (s.comment && s.comment.trim()); }

  function markedCount() {
    return Object.keys(state).filter(function (k) { return isMarked(state[k]); }).length;
  }

  function refreshFooter() {
    var n = markedCount();
    submitBtn.disabled = n === 0;
    pendingEl.textContent = n === 0 ? "No marks yet." : n + " slide" + (n === 1 ? "" : "s") + " marked.";
  }

  function scaleStage(stage, preview, w, h) {
    var avail = preview.clientWidth;
    if (!avail) return;
    var scale = avail / w;
    stage.style.transform = "scale(" + scale + ")";
    preview.style.height = (h * scale) + "px";
  }

  function previewBlock(frag) {
    var preview = document.createElement("div");
    preview.className = "preview";
    var stage = document.createElement("div");
    stage.className = "stage";
    stage.style.width = frag.width_px + "px";
    stage.style.height = frag.height_px + "px";
    stage.style.background = frag.background;
    stage.innerHTML = frag.nodes_html;
    preview.appendChild(stage);
    var rescale = function () { scaleStage(stage, preview, frag.width_px, frag.height_px); };
    requestAnimationFrame(rescale);
    window.addEventListener("resize", rescale);
    return preview;
  }

  function makeSlideCard(deck, slide) {
    var k = key(deck.stem, slide.index);
    state[k] = { verdict: null, comment: "", severity: "med", scope: "slide" };

    var card = document.createElement("section");
    card.className = "card";
    card.dataset.key = k;

    var head = document.createElement("div");
    head.className = "card-head";
    head.innerHTML =
      '<div class="card-title"><h2>Slide ' + slide.index + '</h2>' +
      '<span class="tag">' + esc(slide.component) + '</span></div>' +
      (slide.caption ? '<p class="card-purpose">' + esc(slide.caption) + '</p>' : '');
    card.appendChild(head);

    card.appendChild(previewBlock(slide));

    var controls = document.createElement("div");
    controls.className = "controls";
    controls.innerHTML =
      '<div class="verdict">' +
        '<button type="button" class="vbtn good" data-v="good">👍 Good</button>' +
        '<button type="button" class="vbtn bad" data-v="bad">👎 Needs work</button>' +
        '<button type="button" class="vbtn add" data-v="add-before">➕ Add slide before ↑</button>' +
        '<button type="button" class="vbtn add" data-v="add-after">➕ Add slide after ↓</button>' +
      '</div>' +
      '<textarea class="comment" placeholder="What to change on this slide…"></textarea>' +
      '<fieldset class="scope">' +
        '<legend>This note changes</legend>' +
        '<label><input type="radio" name="scope-' + esc(k) + '" value="slide" checked> ' +
          'This slide <span class="scope-hint">(this deck only)</span></label>' +
        '<label><input type="radio" name="scope-' + esc(k) + '" value="layout"> ' +
          'Layout &amp; theme <span class="scope-hint">(all future decks)</span></label>' +
      '</fieldset>' +
      '<label class="sev">Severity ' +
        '<select><option value="low">low</option><option value="med" selected>med</option>' +
        '<option value="high">high</option></select></label>';
    card.appendChild(controls);

    var commentEl = controls.querySelector(".comment");
    var scopeInputs = controls.querySelectorAll('input[type="radio"]');

    function isAddVerdict(v) { return v === "add-before" || v === "add-after"; }

    var vbtns = controls.querySelectorAll(".vbtn");
    vbtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var v = btn.dataset.v;
        var st = state[k];
        st.verdict = st.verdict === v ? null : v;
        var adding = isAddVerdict(st.verdict);
        // Adding a slide is inherently deck-specific — force slide scope and lock the
        // scope selector so an "add slide" request can never be filed as layout feedback.
        if (adding) {
          st.scope = "slide";
          scopeInputs.forEach(function (r) { r.checked = r.value === "slide"; });
        }
        scopeInputs.forEach(function (r) { r.disabled = adding; });
        commentEl.placeholder = adding
          ? "Describe the new slide you want here…"
          : "What to change on this slide…";
        vbtns.forEach(function (b) { b.classList.toggle("on", b.dataset.v === st.verdict); });
        card.classList.toggle("marked-good", st.verdict === "good");
        card.classList.toggle("marked-bad", st.verdict === "bad");
        card.classList.toggle("marked-add", adding);
        refreshFooter();
      });
    });
    controls.querySelector(".comment").addEventListener("input", function (e) {
      state[k].comment = e.target.value;
      refreshFooter();
    });
    controls.querySelectorAll('input[type="radio"]').forEach(function (r) {
      r.addEventListener("change", function (e) { state[k].scope = e.target.value; });
    });
    controls.querySelector(".sev select").addEventListener("change", function (e) {
      state[k].severity = e.target.value;
    });

    return card;
  }

  function renderDeck(deck) {
    current = deck;
    state = {};
    deckEl.innerHTML = "";
    var h = document.createElement("h3");
    h.className = "section-h";
    h.textContent = deck.title + " — " + deck.slide_count + " slides";
    deckEl.appendChild(h);
    deck.slides.forEach(function (s) { deckEl.appendChild(makeSlideCard(deck, s)); });
    countsEl.innerHTML = "<b>" + deck.slide_count + "</b> slides · " +
      Object.keys(decksById).length + " decks";
    refreshFooter();
    try { window.localStorage.setItem("sk_deck", deck.stem); } catch (e) {}
    window.dispatchEvent(new Event("resize"));
  }

  function toast(msg, isErr) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.className = "toast show" + (isErr ? " err" : "");
    setTimeout(function () { t.className = "toast" + (isErr ? " err" : ""); }, 4200);
  }

  function collect() {
    return Object.keys(state).map(function (k) {
      var s = state[k];
      var comment = (s.comment || "").trim();
      if (!s.verdict && !comment) return null;
      var parts = k.split("::");
      var stem = parts[0], idx = parseInt(parts[1], 10);
      var slide = current.slides[idx - 1];
      // "Add slide before/after" is always deck-specific, regardless of the scope radio.
      var adding = s.verdict === "add-before" || s.verdict === "add-after";
      var scope = adding ? "slide" : s.scope;
      var item = {
        component: slide.component,
        verdict: s.verdict || "note",
        comment: comment,
        severity: s.severity,
        scope: scope
      };
      // Only slide-scoped marks carry the deck coordinates; layout marks stay clean.
      if (scope === "slide") { item.deck = stem; item.slide = idx; }
      return item;
    }).filter(Boolean);
  }

  function submit() {
    var items = collect();
    if (!items.length) return;
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting…";
    fetch("/.netlify/functions/submit-feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ items: items })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) {
        if (!r.ok) throw new Error(body.error || ("HTTP " + r.status));
        return body;
      });
    }).then(function () {
      // Optimistic reset: marks are captured server-side; clear the form.
      deckEl.querySelectorAll(".card").forEach(function (card) {
        var k = card.dataset.key;
        state[k] = { verdict: null, comment: "", severity: "med", scope: "slide" };
        card.classList.remove("marked-good", "marked-bad", "marked-add");
        card.querySelectorAll(".vbtn").forEach(function (b) { b.classList.remove("on"); });
        var cm = card.querySelector(".comment");
        if (cm) { cm.value = ""; cm.placeholder = "What to change on this slide…"; }
        card.querySelectorAll('input[type="radio"]').forEach(function (r) {
          r.disabled = false;
          if (r.value === "slide") r.checked = true;
        });
      });
      toast("Saved " + items.length + " mark" + (items.length === 1 ? "" : "s") + ".");
      refreshFooter();
    }).catch(function (err) {
      toast("Submit failed: " + err.message, true);
    }).finally(function () {
      submitBtn.textContent = "Submit feedback";
      refreshFooter();
    });
  }

  submitBtn.addEventListener("click", submit);
  pickEl.addEventListener("change", function () {
    var d = decksById[pickEl.value];
    if (d) renderDeck(d);
  });

  fetch("/data/decks.json", { credentials: "same-origin" }).then(function (r) {
    if (!r.ok) throw new Error("decks HTTP " + r.status);
    return r.json();
  }).then(function (data) {
    deckEl.setAttribute("aria-busy", "false");
    var decks = data.decks || [];
    if (!decks.length) { deckEl.innerHTML = '<p class="loading">No decks to review.</p>'; return; }
    pickEl.innerHTML = "";
    decks.forEach(function (d) {
      decksById[d.stem] = d;
      var opt = document.createElement("option");
      opt.value = d.stem;
      opt.textContent = d.title + " (" + d.slide_count + ")";
      pickEl.appendChild(opt);
    });
    var want = null;
    try { want = window.localStorage.getItem("sk_deck"); } catch (e) {}
    var start = (want && decksById[want]) ? want : decks[0].stem;
    pickEl.value = start;
    renderDeck(decksById[start]);
  }).catch(function (err) {
    deckEl.innerHTML = '<p class="loading">Could not load decks: ' + esc(err.message) + '</p>';
  });
})();
