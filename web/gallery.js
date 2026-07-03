/* slidekit layout gallery — ALL layouts as thumbnails with click-to-zoom.
 *
 * Reference view: shows every layout regardless of review status (the main page hides
 * approved ones). Each tile carries a status chip (✓ approved / ⚑ flagged / – pending)
 * from web/data/state.json. Tapping a tile opens a lightbox with the preview scaled to
 * the viewport.
 */
(function () {
  "use strict";

  var grid = document.getElementById("tgrid");
  var lb = document.getElementById("lightbox");
  var lbTitle = document.getElementById("lb-title");
  var lbChip = document.getElementById("lb-chip");
  var lbPurpose = document.getElementById("lb-purpose");
  var lbWrap = document.getElementById("lb-stagewrap");

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

  function stageEl(c) {
    var stage = document.createElement("div");
    stage.className = "stage";
    stage.style.width = c.width_px + "px";
    stage.style.height = c.height_px + "px";
    stage.style.background = c.background;
    stage.innerHTML = c.nodes_html;
    return stage;
  }

  function fitStage(stage, host, w, h, maxH) {
    if (!host.clientWidth) return; // detached (collapsed variant) — rescaled on reveal
    var scale = host.clientWidth / w;
    if (maxH) scale = Math.min(scale, maxH / h);
    stage.style.transform = "scale(" + scale + ")";
    host.style.height = (h * scale) + "px";
  }

  function chipFor(st) {
    if (!st) return { cls: "c-pending", text: "pending" };
    if (st.status === "approved") return { cls: "c-ok", text: "✓ approved" };
    return { cls: "c-flag", text: "⚑ flagged" };
  }

  function openLightbox(c, st) {
    lbTitle.textContent = c.component;
    var chip = chipFor(st);
    lbChip.className = "chip " + chip.cls;
    lbChip.textContent = chip.text;
    lbPurpose.textContent = c.purpose + (st && st.comment ? " — 👎 " + st.comment : "");
    lbWrap.innerHTML = "";
    var stage = stageEl(c);
    lbWrap.appendChild(stage);
    lb.hidden = false;
    document.body.style.overflow = "hidden";
    requestAnimationFrame(function () {
      fitStage(stage, lbWrap, c.width_px, c.height_px, window.innerHeight * 0.7);
    });
  }

  function closeLightbox() {
    lb.hidden = true;
    lbWrap.innerHTML = "";
    document.body.style.overflow = "";
  }

  lb.querySelector(".lb-backdrop").addEventListener("click", closeLightbox);
  lb.querySelector(".lb-close").addEventListener("click", closeLightbox);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !lb.hidden) closeLightbox();
  });

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
    grid.innerHTML = "";
    grid.setAttribute("aria-busy", "false");

    function makeTile(c, extraCls) {
      var st = review[c.component];
      var chip = chipFor(st);
      var tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile" + (extraCls ? " " + extraCls : "");
      tile.innerHTML =
        '<div class="tile-preview"></div>' +
        '<div class="tile-meta"><span class="tile-name">' + esc(c.component) + '</span>' +
        '<span class="tile-chips"><span class="chip ' + chip.cls + '">' + esc(chip.text) +
        '</span></span></div>';
      var host = tile.querySelector(".tile-preview");
      var stage = stageEl(c);
      host.appendChild(stage);
      var rescale = function () { fitStage(stage, host, c.width_px, c.height_px); };
      requestAnimationFrame(rescale);
      window.addEventListener("resize", rescale);
      tile.addEventListener("click", function () { openLightbox(c, st); });
      return tile;
    }

    // Anchor-first: the grid holds one tile per FAMILY (its anchor); variants fan
    // out inline behind a "+N" chip on the anchor tile. 24 distinct layouts at a
    // glance, all 36 components two taps away.
    var byFamily = {}, famOrder = [];
    comps.forEach(function (c) {
      if (!byFamily[c.family]) { byFamily[c.family] = []; famOrder.push(c.family); }
      byFamily[c.family].push(c);
    });

    var expanders = [];
    famOrder.forEach(function (fam) {
      var members = byFamily[fam].slice().sort(function (a, b) {
        return (a.role === "anchor" ? 0 : 1) - (b.role === "anchor" ? 0 : 1);
      });
      var anchor = members[0], variants = members.slice(1);
      var tile = makeTile(anchor, null);
      grid.appendChild(tile);
      if (!variants.length) return;

      var anyFlag = variants.some(function (v) {
        var st = review[v.component];
        return st && st.status === "flagged";
      });
      var plus = document.createElement("span");
      plus.className = "chip c-plus" + (anyFlag ? " c-plus-flag" : "");
      plus.textContent = "+" + variants.length;
      plus.title = variants.length + " variant(s) — tap to expand";
      tile.querySelector(".tile-chips").appendChild(plus);

      var vtiles = variants.map(function (v) { return makeTile(v, "tile-variant"); });
      var open = false;
      function setOpen(o) {
        open = o;
        plus.classList.toggle("c-plus-open", open);
        if (open) {
          var after = tile;
          vtiles.forEach(function (vt) { after.insertAdjacentElement("afterend", vt); after = vt; });
          window.dispatchEvent(new Event("resize")); // stages were unsized while detached
        } else {
          vtiles.forEach(function (vt) { vt.remove(); });
        }
      }
      plus.addEventListener("click", function (e) {
        e.stopPropagation(); // don't open the anchor's lightbox
        setOpen(!open);
      });
      expanders.push(setOpen);
    });

    var expandAll = document.getElementById("expandall");
    if (expandAll && expanders.length) {
      var allOpen = false;
      expandAll.hidden = false;
      expandAll.addEventListener("click", function () {
        allOpen = !allOpen;
        expanders.forEach(function (fn) { fn(allOpen); });
        expandAll.textContent = allOpen ? "Collapse variants" : "Expand all variants";
      });
    }
  }).catch(function (err) {
    grid.innerHTML = '<p class="loading">Could not load layouts: ' + esc(err.message) + '</p>';
  });
})();
