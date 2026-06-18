# PROGRESS — slidekit

Source of truth for what is done. An item is checked only when its acceptance
test passed in the session that checked it. See PLAN.md for full detail;
NIGHTLY_REPORTS/ for per-session history; NOTES.md for objections/proposals.

**Gate status**
- Phase 1 calibration gate (2% width threshold): **PASS** (max error 0.076%, commit 23f2b3c)
- Phase 8 prerequisite (Phase 4 linter complete + defect-fixture test passes): **MET** (commit 954fb32)

---

## Phase 0 — Repo & routine setup

- [x] PLAN.md placed at repo root
- [x] NIGHTLY_PROMPT.md created verbatim from PLAN.md
- [x] Nightly schedule registered (GitHub Actions workflow `.github/workflows/nightly.yml`; see operator notes in README)
- [x] PROGRESS.md, NIGHTLY_REPORTS/, NOTES.md initialized (night one)

## Phase 1 — Font metrics & text measurement

- [x] Monorepo scaffold: single `pyproject.toml`, src layout, five packages (`slidekit/ir`, `slidekit/metrics`, `slidekit/layout`, `slidekit/lint`, `slidekit/emit`)
- [x] Metric-safe font set enforced (Arial, Calibri, Cambria, Times New Roman, Courier New, Bookman Old Style, Century Schoolbook); other fonts rejected at IR validation with clear error
- [x] Per-glyph advance widths, kerning pairs, ascent/descent/line-gap extracted via fonttools for each font × weight × style; vendored as JSON in `slidekit/metrics/data/`
- [x] `measure_text(text, font, size_pt, bold, italic) -> width_emu` including kerning
- [x] Greedy line breaking matching PowerPoint behavior: break at spaces/hyphens, no hyphenation, long unbreakable tokens overflow and are flagged; `wrap()` returns Lines with measured width/height
- [x] Text-box internal insets (0.1" L/R, 0.05" T/B) and line spacing (single = 1.2 × font size, explicit IR property) accounted for
- [x] Safety margin policy: configurable slack (default 4% width, half-line height), documented in one place
- [x] ACCEPTANCE: property test — ~200 sampled strings per font, measured width vs. LibreOffice-rendered width differs by < 2% (calibration harness PASS; max error 0.076%; commit 23f2b3c)
- [x] ACCEPTANCE: unit tests for kerning pairs, mixed bold/regular runs, empty strings, very long tokens (28 tests pass)
- [x] **HARD GATE: calibration within 2% — PASS** (max error 0.076%; full report in calibration_report.json)

## Phase 2 — IR schema

- [x] Constraint-first primitives: component-based layout (row/column/grid via two-column, stat-callout, card-grid etc.); `pin` escape hatch reserved for v1.1
- [x] `theme` block: palette roles, type scale (title 54–66pt, header 40–44pt, body 32–36pt hard floor 32pt, caption 24–26pt), spacing units, motif; font validated against safe set
- [x] Page numbers as built-in chrome, on by default: deck-level config, bottom-right, 16pt, muted color, reserved corner box
- [x] Component library: `title-slide`, `two-column`, `icon-text-rows`, `stat-callout`, `comparison-columns`, `timeline`, `image-half-bleed`, `card-grid`
- [x] Typed content slots: `text` (optional `max_lines`), `image` (cover/contain), `chart` (stub), `icon` (name), `spacer`
- [x] Schema versioned (`version: 1`), pydantic validation with precise error paths
- [x] ACCEPTANCE: JSON Schema exported for the IR (`slidekit schema`)
- [x] ACCEPTANCE: 10 example decks in `examples/` covering every component
- [x] ACCEPTANCE: malformed IR produces errors naming the YAML path and the fix

## Phase 3 — Layout engine

- [x] Slide canvas 16:9 default (12192000 × 6858000 EMU), 4:3 optional; all math in EMU
- [x] Two-pass flex solver (measure, then assign); intrinsic text sizes from Phase 1 wrapping
- [x] Text auto-fit policy: wrap → `E_OVERFLOW`; never truncate, never shrink past 32pt floor; recorded in layout report
- [x] Chrome layer: page-number box laid out last, recorded in `ResolvedDeck` like any node
- [x] `ResolvedDeck` output: every node has absolute rect, text nodes have line boxes; `slidekit layout deck.yaml --json`
- [x] ACCEPTANCE: golden-file tests — each example deck's resolved JSON committed (10 golden files)
- [x] ACCEPTANCE: determinism test — two runs byte-identical
- [x] ACCEPTANCE: fuzz test — random valid IR never produces NaN/negative sizes/crashes (Hypothesis)

## Phase 4 — Linter

- [x] Errors: `E_OVERFLOW`, `E_OVERLAP`, `E_MARGIN` (0.5"), `E_GAP` (0.3"), `E_MIN_BODY_SIZE` (32pt hard, chrome + caption-tier exempt), `E_PAGE_NUMBER`, `E_FONT`; E_CONTRAST stub (full WCAG deferred to v1.1)
- [x] Warnings: repeated component >2 consecutive slides; text-only slide; weak title hierarchy (<1.4× body); >6 bullets; W_TEXT_ONLY
- [x] Output: JSON list `{code, slide, node_path, message, suggested_fix}`
- [x] ACCEPTANCE: fixture deck with one instance of every defect — linter catches all (19 tests pass)
- [x] ACCEPTANCE: clean deck produces zero errors (all 10 example decks pass)

## Phase 5 — Emitters

- [x] pptx emitter: python-pptx, resolved EMU rects, auto-fit OFF, word-wrap ON, explicit font runs, literal RGB, text box insets matching constants.py
- [x] ACCEPTANCE: round-trip test — emit → reopen → positions/sizes match resolved geometry exactly (7 tests pass)
- [x] HTML debug preview (absolute-positioned divs at 96 DPI; human spot-check only)
- [x] **FIRST-LIGHT DEMO: `examples/demo-5.yaml` → `demo-5.pptx`** — 5 slides (title, two-column, stat callout, icon-text rows, comparison), lint-clean, page numbers, zero screenshot calls (commit 9db4235)

## Phase 6 — Verification harness (CI only)

- [x] Smoke test: build all example decks → `soffice --headless --convert-to pdf` → `pdftoppm` → pixel heuristics (ink within margins, no text pixels outside computed rects ± slack) — `slidekit/verify`, 15 tests incl. sensitivity check; all 11 decks pass (max stray 0.41% vs 1% threshold). Surfaced + fixed a real icon-overflow drift in the emitter (commit 7632299)
- [x] Wired into CI on layout/metrics changes; explicitly NOT part of deck generation — workflow installed at `.github/workflows/verify.yml` (from `ci/verify.yml`) by an operator-scoped session; triggers on layout/metrics/emit/verify/examples paths. See NOTES.md (commit 518f8d0; installed in follow-up)

## Phase 7 — Agent interface

- [x] SKILL.md: when to use, IR cheatsheet, component gallery, build/fix loop (no image rendering) — `SKILL.md` (commit 1fc3b9f)
- [x] `slidekit new --template <component-mix>` scaffolds themed starter deck — `slidekit/scaffold.py`, templates title-slide/standard/comparison/pitch + `--list`; all build lint-clean (commit 1fc3b9f)
- [x] ACCEPTANCE: lint errors name IR path + concrete fix; fresh-agent fix-on-first-try rate measured — tests in `tests/test_cli/test_scaffold.py` assert non-empty node_path + concrete suggested_fix; live measurement (2026-06-13 session 2): 3 fresh agents given only SKILL.md + a broken deck each, **fix-on-first-try 2/3, eventual lint-clean 3/3, zero rendering** (see NIGHTLY_REPORTS/2026-06-13-session2.md)

## Phase 8 — agency-agents integration

**Done on branch `agency-agents-integration`.** agency-agents is vendored at
`integrations/agency-agents/` (MIT, snapshot — see `integrations/README.md`).
All agent edits go inside that tree and are validated with
`integrations/agency-agents/scripts/lint-agents.sh`.

- [x] Deck Builder agent authored in agency-agents template format (IR YAML only; build→lint→fix loop; never renders; lint-clean in ≤2 iterations) — `integrations/agency-agents/specialized/specialized-deck-builder.md`; passes upstream `lint-agents.sh` (0 err/warn) and `check-agent-originality.sh` (0.0%)
- [x] Handoff seams — Brand Guardian → `theme` block and Visual Storyteller/Content Creator → structured outline shapes documented in the Deck Builder agent file; **worked example** added at `examples/agency-pipeline-demo/` (Brand Guardian `brand-guardian-theme.md` + Storyteller `storyteller-outline.md` fixtures in the seam shapes → `deck.yaml` → `deck.pptx`, built lint-clean; commit 2749067)
- [x] Visual QA retired for decks — deck-scoped certification language applied into `integrations/agency-agents/testing/testing-reality-checker.md` (READY on `slidekit build` exit 0 + empty lint errors + round-trip pass, no screenshot sign-off); Evidence Collector / Playwright screenshot QA for UI work left untouched; `lint-agents.sh` + `check-agent-originality.sh` PASS (commit 8822aa0)
- [x] Document Generator compatibility shim note — delegation note added to `integrations/agency-agents/specialized/specialized-document-generator.md` PPTX section (PDF/DOCX/XLSX paths untouched)
- [x] ACCEPTANCE: outline → lint-clean .pptx, zero screenshot calls — `tests/test_integration/test_agency_pipeline.py::TestOutlineBuildsCleanWithoutRendering`: `slidekit build` exits 0, empty lint-error list, build path shells out to no render tool (subprocess guarded), and deck components match the outline fixture (4 tests; commit 2749067)
- [x] ACCEPTANCE: end-to-end orchestrated run — theme block round-trips into emitted colors/fonts exactly — `TestThemeRoundTrip`: reopened `.pptx` surface/font/text/muted equal the theme block parsed from `deck.yaml` exactly (3 tests; commit 2749067)

## Phase 9 — 40-design library (operator-directed scope expansion, 2026-06-14)

Goal: grow the component library from 8 to **40 core slide designs**. Full
blueprint and per-design integration points in `docs/SLIDE_DESIGNS.md`. Build the
32 new designs in catalog order; each ships model + layout handler + dispatch
branch + golden test + example deck + SKILL gallery row, lint-clean, before the
next. (Research reconciliation pending — chatgpt.com/grok.com blocked by egress.)

- [x] B/C openers+emphasis: section-divider, agenda, quote-opener, big-number, pull-quote, statement, definition, question (8 designs; models + `_layout_*` handlers + dispatch + goldens 11–18 + examples + SKILL rows; all lint-clean, golden tests pass; commit c60079b, 2026-06-14)
- [x] C lists: bullet-list, feature-list, checklist, numbered-steps (4 designs; models + handlers + dispatch + goldens 19–22 + examples + SKILL rows; all lint-clean, suite green; commit f54b7f8, 2026-06-14)

_Phase 9 running tally: **40 of 40** designs shipped (8 v1 + 12 on 2026-06-14 + 3 on 2026-06-15 + 5 on 2026-06-16 + 6 on 2026-06-17 + 6 on 2026-06-18). Component library complete._
- [x] D comparison: before-after, pros-cons, this-vs-that (3 designs; models + `_layout_*` handlers + dispatch + goldens 23–25 + examples + SKILL rows; all lint-clean, suite green, schema validates; 2026-06-15)
- [x] E data: kpi-grid, chart-slide, chart-with-insight, table-slide, metric-comparison (5 designs; models + `_layout_*` handlers + dispatch + goldens 26–30 + examples + SKILL rows; charts render as measured bar rectangles + labels, tables as a cell grid with an accent header rule, deltas as accent chips — all deterministic, no freehand marks; all 5 build lint-clean, suite green at 189 passed / 35 skipped, schema validates; 2026-06-16)
- [x] F process/shape: process-steps, roadmap, funnel, pyramid, matrix-2x2, swot (6 designs; models + `_layout_*` handlers + dispatch + goldens 31–36 + examples + PDFs + SKILL rows; funnels/pyramids are measured centered narrowing/widening colored bars, matrix-2x2 is a grouped accent cross + 4 quadrant cells + axis captions, swot is a 2×2 of titled accent/muted bulleted panels — all deterministic, no freehand connectors; all 6 build lint-clean, suite green at 195 passed / 41 skipped, schema validates; 2026-06-17)
- [x] G/H structure+visual: comparison-matrix, team-grid, image-full-bleed, image-grid, logo-wall, testimonial (6 designs; models + `_layout_*` handlers + dispatch + goldens 37–42 + examples + SKILL rows; all build lint-clean; 2026-06-18)
- [x] ACCEPTANCE: each new design has a golden-file layout test + a lint-clean example deck
- [x] ACCEPTANCE: SKILL.md component gallery lists all 40; `slidekit schema` validates every new component
- [x] ACCEPTANCE: full test suite green; verify harness passes on all new example decks (suite 217 passed / 47 skipped; verify-render CI rendered every example deck through LibreOffice+poppler and passed the pixel harness — run 27781859805 on commit 27817bb, 2026-06-18)

## Phase 10 — computational aesthetics (operator-directed, 2026-06-14)

Add a deterministic **aesthetic scoring** layer over the ResolvedDeck — balance,
alignment, whitespace, non-overlap, contrast, color harmony, info density, visual
hierarchy, cross-slide consistency — turning "no defects" into a graded 0–100 score,
still computed from source geometry (no rendering, no vision). Full spec + metric
definitions + research lineage in `docs/AESTHETICS.md`. Advisory only (warnings +
score); the linter remains the gate.

- [ ] `slidekit/aesthetics/` module: per-metric functions over ResolvedDeck (balance, alignment, whitespace, non-overlap, contrast, color-harmony, density, hierarchy)
- [ ] Deck-level cross-slide consistency metric
- [ ] Composite `AestheticScore` (configurable weights) + `slidekit score deck.yaml --json` CLI
- [ ] Advisory `W_AESTH_*` warnings below thresholds (never block the build)
- [ ] ACCEPTANCE: deterministic (two runs identical) + unit tests per metric on hand-checked fixtures
- [ ] ACCEPTANCE: every Phase 9 example deck clears a documented baseline score
- [ ] DEFERRED (data-dependent): weight calibration against a human-labeled slide-pair set; do NOT claim human correlation until then

## Phase 10 — first cut shipped (2026-06-14, interactive)
- [x] `slidekit/aesthetics/` + `slidekit score deck.yaml [--json]` — deterministic 0–100 score over
  ResolvedDeck: balance, whitespace, alignment, non-overlap, hierarchy, contrast. Advisory; 4 tests; 168 green.
- [x] FLAW FIXED (2026-06-15, commit 7045e5c): added `richness` (visual-engagement) sub-score + WCAG
  large-text 3:1 for big text so accent emphasis isn't penalised. Validated: designed `big-number` deck
  out-scores plain `agents-in-ai`/`all_components` (regression test). 7 new unit tests.
- [x] Added `color_harmony` (theme hue relationship) + `cross_slide_consistency` (deck-level margin
  variance, bounded [0.9,1.0]) metrics (docs/AESTHETICS.md; commit 7045e5c).
- [x] Visual-polish pass on the 8 v1 component handlers (PRIORITY OVERRIDE #2, 2026-06-15): headings in
  brand primary, hero data (stat values, timeline dates) in accent, icon fills recorded; all decks stay
  lint-clean; every example deck score rose (e.g. all-components 75.4→84.8); PDFs rebuilt; goldens regen.
- [x] `W_AESTH_*` advisory warnings + optional `--min-score` gate (2026-06-18): 9 advisory
  `W_AESTH_*` codes (one per sub-metric; theme-level metrics warn once at deck level) with
  documented `ADVISORY_THRESHOLDS` tuned from the 40-deck distribution; warnings included in
  the `slidekit score --json` report; opt-in `--min-score N` CI floor (exits 1 below the bar,
  exit 0 by default — the linter stays the gate). 9 tests; suite 214 passed / 47 skipped.
  (info-density metric still TODO; weight calibration DEFERRED.)
- [ ] DEFERRED: weight calibration vs a human-labelled slide-pair set.
