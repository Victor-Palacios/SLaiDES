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

## Phase 8 — agency-agents integration (BLOCKED until Phase 4 complete)

- [ ] Deck Builder agent authored in agency-agents template format (IR YAML only; build→lint→fix loop; never renders; lint-clean in ≤2 iterations; `specialized/specialized-deck-builder.md`)
- [ ] Handoff seams: Brand Guardian → `theme` block; Visual Storyteller/Content Creator → structured outline; Orchestrator pipeline worked example in `examples/`
- [ ] Visual QA retired for decks: Reality Checker certification language ("production-ready when `slidekit build` exits 0 and round-trip passes")
- [ ] Document Generator compatibility shim note
- [ ] ACCEPTANCE: fresh session with Deck Builder + slidekit turns outline → lint-clean .pptx, zero screenshot calls
- [ ] ACCEPTANCE: end-to-end orchestrated run — theme block round-trips into emitted colors/fonts exactly
