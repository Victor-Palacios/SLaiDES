# PROGRESS — slidekit

Source of truth for what is done. An item is checked only when its acceptance
test passed in the session that checked it. See PLAN.md for full detail;
NIGHTLY_REPORTS/ for per-session history; NOTES.md for objections/proposals.

**Gate status**
- Phase 1 calibration gate (2% width threshold): NOT YET RUN
- Phase 8 prerequisite (Phase 4 linter complete + defect-fixture test passes): NOT MET

---

## Phase 0 — Repo & routine setup

- [x] PLAN.md placed at repo root
- [x] NIGHTLY_PROMPT.md created verbatim from PLAN.md
- [x] Nightly schedule registered (GitHub Actions workflow `.github/workflows/nightly.yml`; see operator notes in README)
- [x] PROGRESS.md, NIGHTLY_REPORTS/, NOTES.md initialized (night one)

## Phase 1 — Font metrics & text measurement

- [ ] Monorepo scaffold: single `pyproject.toml`, src layout, five packages (`slidekit/ir`, `slidekit/metrics`, `slidekit/layout`, `slidekit/lint`, `slidekit/emit`)
- [ ] Metric-safe font set enforced (Arial, Calibri, Cambria, Times New Roman, Courier New, Bookman Old Style, Century Schoolbook); other fonts rejected at IR validation with clear error
- [ ] Per-glyph advance widths, kerning pairs, ascent/descent/line-gap extracted via fonttools for each font × weight × style; vendored as JSON in `slidekit/metrics/data/`
- [ ] `measure_text(text, font, size_pt, bold, italic) -> width_emu` including kerning
- [ ] Greedy line breaking matching PowerPoint behavior: break at spaces/hyphens, no hyphenation, long unbreakable tokens overflow and are flagged; `wrap()` returns Lines with measured width/height
- [ ] Text-box internal insets (0.1" L/R, 0.05" T/B) and line spacing (single = 1.2 × font size, explicit IR property) accounted for
- [ ] Safety margin policy: configurable slack (default 4% width, half-line height), documented in one place
- [ ] ACCEPTANCE: property test — ~200 sampled strings per font, measured width vs. LibreOffice-rendered width differs by < 2% (one-time calibration harness; NOT part of build loop)
- [ ] ACCEPTANCE: unit tests for kerning pairs, mixed bold/regular runs, empty strings, very long tokens
- [ ] **HARD GATE: calibration within 2% — go/no-go decision recorded** (human should read this report before night two; see PLAN.md operator notes)

## Phase 2 — IR schema

- [ ] Constraint-first primitives: `row`, `column`, `grid`, `stack` with `gap`, `padding`, `weight`, `min/max`; `pin` escape hatch (lint warning)
- [ ] `theme` block: palette roles, type scale (title 54–66pt, header 40–44pt, body 32–36pt hard floor 32pt, caption 24–26pt), spacing units, motif; raw hex in slide body = lint warning
- [ ] Page numbers as built-in chrome, on by default: deck-level config, bottom-right, 16pt, muted color, reserved corner box
- [ ] Component library: `title-slide`, `two-column`, `icon-text-rows`, `stat-callout`, `comparison-columns`, `timeline`, `image-half-bleed`, `card-grid`
- [ ] Typed content slots: `text` (optional `max_lines`), `image` (cover/contain), `chart` (matplotlib → PNG sized to slot), `icon` (vendored set, colored circle), `spacer`
- [ ] Schema versioned (`version: 1`), pydantic validation with precise error paths
- [ ] ACCEPTANCE: JSON Schema exported for the IR
- [ ] ACCEPTANCE: 10 example decks in `examples/` covering every component
- [ ] ACCEPTANCE: malformed IR produces errors naming the YAML path and the fix

## Phase 3 — Layout engine

- [ ] Slide canvas 16:9 default (12192000 × 6858000 EMU), 4:3 optional; all math in EMU
- [ ] Two-pass flex solver (measure, then assign); intrinsic text sizes from Phase 1 wrapping
- [ ] Text auto-fit policy: wrap → shrink to tier floor (body 32pt hard) → `E_OVERFLOW`; never truncate, never shrink past floor; recorded in layout report
- [ ] Chrome layer: page-number box laid out last, recorded in `ResolvedDeck` like any node
- [ ] `ResolvedDeck` output: every node has absolute rect, text nodes have line boxes; `slidekit layout deck.yaml --json`
- [ ] ACCEPTANCE: golden-file tests — each example deck's resolved JSON committed
- [ ] ACCEPTANCE: determinism test — two runs byte-identical
- [ ] ACCEPTANCE: fuzz test — random valid IR never produces NaN/negative sizes/crashes

## Phase 4 — Linter

- [ ] Errors: `E_OVERFLOW`, `E_OVERLAP`, `E_MARGIN` (0.5"), `E_GAP` (0.3"), `E_CONTRAST` (4.5:1 body / 3:1 ≥24pt), `E_MIN_BODY_SIZE` (32pt hard, page-number chrome exempt), `E_PAGE_NUMBER`, `E_FONT`
- [ ] Warnings: repeated component >2 consecutive slides; centered body text; text-only slide; weak title hierarchy (<1.4× body); `pin` used; raw hex; >6 bullets; uneven whitespace; style anti-patterns (accent line under title, full-width bars, edge stripes ≤6pt)
- [ ] Output: JSON list `{code, slide, node_path, message, suggested_fix}`
- [ ] ACCEPTANCE: fixture deck with one instance of every defect — linter catches all
- [ ] ACCEPTANCE: clean deck produces zero errors

## Phase 5 — Emitters

- [ ] pptx emitter: python-pptx, resolved EMU rects, auto-fit OFF, word-wrap ON, explicit font runs, literal RGB, images pre-resized to slot
- [ ] ACCEPTANCE: round-trip test — emit → reopen → positions/sizes match resolved geometry exactly
- [ ] HTML debug preview (absolute-positioned divs; human spot-check only)
- [ ] **FIRST-LIGHT DEMO: `examples/demo-5.yaml` → `demo-5.pptx`** — 5 slides (title, two-column, stat callout, icon-text rows, comparison), lint-clean, page numbers, zero screenshot calls — flag prominently in nightly report

## Phase 6 — Verification harness (CI only)

- [ ] Smoke test: build all example decks → `soffice --headless --convert-to pdf` → `pdftoppm` → pixel heuristics (ink within margins, no text pixels outside computed rects ± slack)
- [ ] Wired into CI on layout/metrics changes; explicitly NOT part of deck generation

## Phase 7 — Agent interface

- [ ] SKILL.md: when to use, IR cheatsheet, component gallery, build/fix loop (no image rendering)
- [ ] `slidekit new --template <component-mix>` scaffolds themed starter deck
- [ ] ACCEPTANCE: lint errors name IR path + concrete fix; fresh-agent fix-on-first-try rate measured

## Phase 8 — agency-agents integration (BLOCKED until Phase 4 complete)

- [ ] Deck Builder agent authored in agency-agents template format (IR YAML only; build→lint→fix loop; never renders; lint-clean in ≤2 iterations; `specialized/specialized-deck-builder.md`)
- [ ] Handoff seams: Brand Guardian → `theme` block; Visual Storyteller/Content Creator → structured outline; Orchestrator pipeline worked example in `examples/`
- [ ] Visual QA retired for decks: Reality Checker certification language ("production-ready when `slidekit build` exits 0 and round-trip passes")
- [ ] Document Generator compatibility shim note
- [ ] ACCEPTANCE: fresh session with Deck Builder + slidekit turns outline → lint-clean .pptx, zero screenshot calls
- [ ] ACCEPTANCE: end-to-end orchestrated run — theme block round-trips into emitted colors/fonts exactly
