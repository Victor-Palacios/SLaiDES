/* slidekit layout-feedback site — the REVIEW QUEUE (main page).
 *
 * Data: web/data/previews.json (current geometry-driven preview per layout, regenerated
 * whenever layouts change) + web/data/state.json (operator review state, maintained by
 * scripts/feedback_intake_web.py from submitted verdicts).
 *
 * The main page shows only layouts that still need the operator's attention:
 *   - flagged  (👎 earlier): shown FIRST, as a before/after comparison once a fix has
 *     landed (previews.json changed vs the snapshot taken at flag time) — approve with
 *     👍 to clear it, or 👎 to re-flag with a fresh note.
 *   - pending  (never reviewed): the normal single-preview card with 👍/👎 + comment.
 *   - approved (👍 earlier): not shown here at all — see gallery.html for everything.
 *
 * Submitting POSTs to the Netlify function; CI folds the marks into ops/FEEDBACK.yaml
 * and state.json, and the site redeploys (~1–2 min). The page updates optimistically in
 * the meantime. Auth is a signed cookie set at the edge; nothing token-ish lives here.
 */
(function () {
  "use strict";

  var state = {}; // component -> { verdict, comment, severity }

  var gallery = document.getElementById("gallery");
  var submitBtn = document.getElementById("submit");
  var pendingEl = document.getElementById("pending");
  var countsEl = document.getElementById("counts");

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

  function markedCount() {
    return Object.keys(state).filter(function (k) {
      var s = state[k];
      return s.verdict || (s.comment && s.comment.trim());
    }).length;
  }

  function refreshFooter() {
    var n = markedCount();
    submitBtn.disabled = n === 0;
    pendingEl.textContent = n === 0 ? "No marks yet." : n + " layout" + (n === 1 ? "" : "s") + " marked.";
  }

  function scaleStage(stage, preview, w, h) {
    var avail = preview.clientWidth;
    if (!avail) return;
    var scale = avail / w;
    stage.style.transform = "scale(" + scale + ")";
    preview.style.height = (h * scale) + "px";
  }

  function previewBlock(frag, label) {
    var wrap = document.createElement("div");
    if (label) {
      var l = document.createElement("div");
      l.className = "cmp-label" + (label.indexOf("Before") === 0 ? " cmp-before" : " cmp-after");
      l.textContent = label;
      wrap.appendChild(l);
    }
    var preview = document.createElement("div");
    preview.className = "preview";
    var stage = document.createElement("div");
    stage.className = "stage";
    stage.style.width = frag.width_px + "px";
    stage.style.height = frag.height_px + "px";
    stage.style.background = frag.background;
    stage.innerHTML = frag.nodes_html;
    preview.appendChild(stage);
    wrap.appendChild(preview);
    var rescale = function () { scaleStage(stage, preview, frag.width_px, frag.height_px); };
    requestAnimationFrame(rescale);
    window.addEventListener("resize", rescale);
    return wrap;
  }

  function fragChanged(before, current) {
    return before.nodes_html !== current.nodes_html ||
           before.background !== current.background ||
           before.width_px !== current.width_px ||
           before.height_px !== current.height_px;
  }

  function makeCard(c, review) {
    state[c.component] = { verdict: null, comment: "", severity: "med" };

    var card = document.createElement("section");
    card.className = "card";
    card.dataset.component = c.component;

    var role = c.role === "variant" ? ("variant of " + c.variant_of) : c.family;
    var head = document.createElement("div");
    head.className = "card-head";
    head.innerHTML =
      '<div class="card-title"><h2>' + esc(c.component) + '</h2>' +
      '<span class="tag">' + esc(role) + '</span>' +
      (c.role === "variant" && c.differs_by
        ? '<span class="tag tag-diff">differs by: ' + esc(c.differs_by) + '</span>' : '') +
      (review ? '<span class="badge b-flag">flagged</span>' : '') +
      '</div>' +
      '<p class="card-purpose">' + esc(c.purpose) + '</p>' +
      (review
        ? '<p class="flaginfo">👎 ' + esc(review.comment) + ' <span class="flagdate">(' + esc(review.date) + ')</span></p>'
        : '<p class="card-when">Use when: ' + esc(c.use_when) + '</p>');
    card.appendChild(head);

    // Preview area: comparison for flagged-with-changes, single otherwise.
    var current = { width_px: c.width_px, height_px: c.height_px, background: c.background, nodes_html: c.nodes_html };
    if (review && review.before && fragChanged(review.before, current)) {
      card.appendChild(previewBlock(review.before, "Before — what you flagged"));
      card.appendChild(previewBlock(current, "Current — after the fix"));
    } else {
      if (review) {
        var wait = document.createElement("p");
        wait.className = "flagwait";
        wait.textContent = "⏳ No change has landed yet — this is still the version you flagged.";
        card.appendChild(wait);
      }
      card.appendChild(previewBlock(current, null));
    }

    var controls = document.createElement("div");
    controls.className = "controls";
    controls.innerHTML =
      '<div class="verdict">' +
        '<button type="button" class="vbtn good" data-v="good">👍 ' + (review ? "Approve" : "Good") + '</button>' +
        '<button type="button" class="vbtn bad" data-v="bad">👎 ' + (review ? "Still needs work" : "Needs work") + '</button>' +
      '</div>' +
      '<textarea class="comment" placeholder="Optional note — what to change…"></textarea>' +
      '<label class="sev">Severity ' +
        '<select><option value="low">low</option><option value="med" selected>med</option>' +
        '<option value="high">high</option></select></label>';
    card.appendChild(controls);

    var vbtns = controls.querySelectorAll(".vbtn");
    vbtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var v = btn.dataset.v;
        var st = state[c.component];
        st.verdict = st.verdict === v ? null : v;
        vbtns.forEach(function (b) { b.classList.toggle("on", b.dataset.v === st.verdict); });
        card.classList.toggle("marked-good", st.verdict === "good");
        card.classList.toggle("marked-bad", st.verdict === "bad");
        refreshFooter();
      });
    });
    controls.querySelector(".comment").addEventListener("input", function (e) {
      state[c.component].comment = e.target.value;
      refreshFooter();
    });
    controls.querySelector(".sev select").addEventListener("change", function (e) {
      state[c.component].severity = e.target.value;
    });

    return card;
  }

  function sectionHeading(text) {
    var h = document.createElement("h3");
    h.className = "section-h";
    h.textContent = text;
    return h;
  }

  function toast(msg, isErr) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.className = "toast show" + (isErr ? " err" : "");
    setTimeout(function () { t.className = "toast" + (isErr ? " err" : ""); }, 4200);
  }

  function collect() {
    return Object.keys(state).map(function (comp) {
      var s = state[comp];
      var comment = (s.comment || "").trim();
      if (!s.verdict && !comment) return null;
      return { component: comp, verdict: s.verdict || "note", comment: comment, severity: s.severity };
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
      // Optimistic update: approved cards leave the queue now; the committed
      // state.json catches up on the next deploy (~1–2 min).
      var approved = 0;
      items.forEach(function (it) {
        if (it.verdict !== "good") return;
        var card = gallery.querySelector('[data-component="' + it.component + '"]');
        if (card) { card.remove(); approved++; }
        delete state[it.component];
      });
      items.forEach(function (it) {
        if (it.verdict !== "good" && state[it.component]) {
          state[it.component] = { verdict: null, comment: "", severity: "med" };
        }
      });
      gallery.querySelectorAll(".card").forEach(function (card) {
        card.classList.remove("marked-good", "marked-bad");
        card.querySelectorAll(".vbtn").forEach(function (b) { b.classList.remove("on"); });
        var cm = card.querySelector(".comment"); if (cm) cm.value = "";
      });
      toast("Saved " + items.length + " mark" + (items.length === 1 ? "" : "s") +
            (approved ? " · " + approved + " approved (moved to All layouts)" : "") + ".");
      refreshFooter();
    }).catch(function (err) {
      toast("Submit failed: " + err.message, true);
    }).finally(function () {
      submitBtn.textContent = "Submit feedback";
      refreshFooter();
    });
  }

  submitBtn.addEventListener("click", submit);

  Promise.all([
    fetch("/data/previews.json", { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error("previews HTTP " + r.status); return r.json();
    }),
    fetch("/data/state.json", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : { components: {} }; })
      .catch(function () { return { components: {} }; })
  ]).then(function (res) {
    var comps = res[0].components;
    var review = (res[1] && res[1].components) || {};
    gallery.innerHTML = "";
    gallery.setAttribute("aria-busy", "false");

    var flagged = comps.filter(function (c) {
      return review[c.component] && review[c.component].status === "flagged";
    });
    var pending = comps.filter(function (c) { return !review[c.component]; });
    var approvedCount = comps.length - flagged.length - pending.length;

    if (flagged.length) {
      gallery.appendChild(sectionHeading("Flagged — confirm the fix (" + flagged.length + ")"));
      flagged.forEach(function (c) { gallery.appendChild(makeCard(c, review[c.component])); });
    }
    if (pending.length) {
      // Anchor-first family stacks: each family shows ONE card (its anchor when
      // pending, else its first pending variant); remaining pending variants sit
      // behind a "+N variants" expander so the queue length ≈ distinct layouts.
      var famOrder = [], famMap = {};
      pending.forEach(function (c) {
        if (!famMap[c.family]) { famMap[c.family] = []; famOrder.push(c.family); }
        famMap[c.family].push(c);
      });
      gallery.appendChild(sectionHeading(
        "Not yet reviewed (" + pending.length + " across " + famOrder.length + " layout famil" +
        (famOrder.length === 1 ? "y" : "ies") + ")"));
      famOrder.forEach(function (fam) {
        var members = famMap[fam].slice().sort(function (a, b) {
          return (a.role === "anchor" ? 0 : 1) - (b.role === "anchor" ? 0 : 1);
        });
        gallery.appendChild(makeCard(members[0], null));
        var rest = members.slice(1);
        if (!rest.length) return;
        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "vtoggle";
        var showLabel = "▸ " + rest.length + " variant" + (rest.length === 1 ? "" : "s") +
                        " of " + members[0].component;
        toggle.textContent = showLabel;
        var group = document.createElement("div");
        group.className = "variants";
        group.hidden = true;
        rest.forEach(function (c) { group.appendChild(makeCard(c, null)); });
        toggle.addEventListener("click", function () {
          group.hidden = !group.hidden;
          toggle.textContent = group.hidden ? showLabel : "▾ hide variants";
          if (!group.hidden) {
            // Stages were laid out while hidden (zero width) — rescale now.
            window.dispatchEvent(new Event("resize"));
          }
        });
        gallery.appendChild(toggle);
        gallery.appendChild(group);
      });
    }
    if (!flagged.length && !pending.length) {
      gallery.innerHTML = '<p class="loading">🎉 Everything is reviewed and approved. ' +
        'See <a href="/gallery.html">All layouts</a>.</p>';
    }
    countsEl.innerHTML = "<b>" + approvedCount + "</b> approved · " +
      "<span class='b-bad'>" + flagged.length + "</span> flagged · " +
      pending.length + " pending";
    refreshFooter();
  }).catch(function (err) {
    gallery.innerHTML = '<p class="loading">Could not load layouts: ' + esc(err.message) + '</p>';
  });
})();
