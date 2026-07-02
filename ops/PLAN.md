# Agent-First Slide Builder — Implementation Plan

## Objective

Build a slide-generation system where layout correctness is **provable from source** rather than verified by rendering screenshots. The agent authors a declarative slide IR; a deterministic layout engine computes geometry using real font metrics; a linter catches every class of defect that visual QA currently catches; a compiler emits .pptx. Image inspection is demoted from inner-loop workflow to optional CI smoke test.

**Success metric:** a deck that passes the linter renders in PowerPoint/Google Slides with zero user-visible layout defects (overflow, overlap, margin violations, contrast failures), with no screenshot round-trips during generation.

**Ecosystem context:** slidekit is also the deck-production backbone for the [agency-agents](https://github.com/msitarzewski/agency-agents) multi-agent roster. That repo decomposes *judgment* (content, brand, narrative, sign-off) across persona subagents; slidekit decomposes *correctness* (fit, overlap, contrast) into deterministic checks. Phase 8 wires the two together. Build slidekit as a standalone repo regardless — the integration is a thin layer on top, not a dependency.

## Why this architecture

.pptx files store absolute positions but not rendered truth — text overflow depends on font metrics and the renderer's line-breaking. Visual QA exists to recover that truth after the fact. This system recovers it **before** the fact by (a) restricting the design space to fonts with known, shippable metrics, and (b) implementing the line-breaking/box-layout math ourselves. Geometry is then computed, not guessed, so checking it is arithmetic, not vision.

## Non-goals (v1)

- Editing arbitrary inbound .pptx files (foreign templates still need the inspect-render loop)
- Animations, transitions, embedded video/audio
- Fonts outside the metric-safe set (see Phase 1)
- WYSIWYG editor / GUI
- Pixel-perfect parity with a specific renderer; the target is "no user-visible defects," enforced via conservative slack margins

## Architecture

```
deck.yaml (IR) ──► layout engine ──► resolved geometry (EMU) ──► lint ──► compile
                   (font metrics,        (every box has              │        │
                    box model,            x,y,w,h + per-line         │        ├─► .pptx (python-pptx or raw OOXML)
                    line breaking)        text extents)              │        └─► .html (debug preview, optional)
                                                              fail = exit 1,
                                                              machine-readable errors
```

Five packages in a monorepo (Python; single `pyproject.toml`, src layout):

| Package | Responsibility |
|---|---|
| `slidekit/ir` | IR schema (pydantic), parsing, validation of structure |
| `slidekit/metrics` | Font metric tables (extracted via fonttools, vendored as JSON), text measurement, line breaking |
| `slidekit/layout` | Box model solver: nested flex rows/columns/grids → absolute EMU rects |
| `slidekit/lint` | Post-layout checks: overflow, overlap, margins, contrast, style rules |
| `slidekit/emit` | Compile resolved geometry → .pptx; optional HTML debug renderer |

CLI: `slidekit build deck.yaml -o deck.pptx` (runs layout + lint + emit; lint failure aborts with JSON error list the agent can act on).

---

## Phase 1 — Font metrics & text measurement (the keystone)

Everything depends on trustworthy text measurement. Do this first and test it hardest.

**Tasks**

1. Restrict v1 to the metric-safe font set: **Arial, Calibri, Cambria, Times New Roman, Courier New, Bookman Old Style, Century Schoolbook** (these ship with Office and render true-to-width). Reject other fonts at IR validation with a clear error.
2. Use `fonttools` to extract per-glyph advance widths, kerning pairs, ascent/descent/line-gap for each font × weight × style. Vendor the extracted tables as JSON inside `slidekit/metrics/data/` so the build never depends on system fonts at runtime.
3. Implement `measure_text(text, font, size_pt, bold, italic) -> width_emu` including kerning.
4. Implement greedy line breaking matching PowerPoint behavior: break at spaces/hyphens, no hyphenation, long unbreakable tokens overflow (and must be flagged). `wrap(text, font_spec, box_width_emu) -> list[Line]` where each Line carries its measured width and height.
5. Account for text-box internal insets (PowerPoint defaults: 0.1" L/R, 0.05" T/B) and line spacing rules (single = 1.2 × font size as a baseline approximation; expose as explicit IR property).
6. **Safety margin policy:** all fit checks apply a configurable slack (default 4% width, one half-line height) to absorb renderer variance. Document this constant in one place.

**Acceptance**

- Property test: for ~200 sampled strings per font, our measured width vs. LibreOffice-rendered width (one-time calibration harness using `soffice` → pdf → text extraction or PIL with the actual TTFs) differs by < 2%.
- Unit tests for kerning pairs, mixed bold/regular runs, empty strings, very long tokens.
- This calibration harness is throwaway tooling for validating metrics — it is NOT part of the build loop.

## Phase 2 — IR schema

Declarative YAML/JSON. The agent writes intent; numbers are mostly derived.

**Design rules**

- **Constraint-first, coordinates-last.** Primary layout primitives are `row`, `column`, `grid`, `stack` (z-layering) with `gap`, `padding`, `weight` (flex-grow), `min/max` size. Absolute positioning exists (`pin: {x,y,w,h}`) but is an escape hatch the linter reports as a warning.
- **Design tokens, not inline styles.** A `theme` block defines palette roles (`primary`, `surface`, `accent`, `text`, `muted`), the type scale (title 54–66pt, header 40–44pt, body 32–36pt, caption 24–26pt), spacing units, and one motif. **Body text has a hard floor of 32pt — never below, anywhere in the system.** Title size is flexible as long as it stays clearly above the header tier. Components reference tokens; raw hex in a slide body is a lint warning.
- **Page numbers are built-in chrome, on by default.** Every slide gets its number rendered bottom-right at 16pt in the theme's `muted` color. This is deck-level config (`page_numbers: {enabled: true, start_at: 1, skip_title_slide: false}`), not authored per slide. As UI chrome rather than content, it is the one sanctioned exception to the 32pt body floor and may sit inside the 0.5" margin zone; the layout engine reserves its corner box so slide content can never collide with it (a collision is a normal `E_OVERLAP`).
- **Component library** as IR-level building blocks (each compiles to a row/column tree): `title-slide`, `two-column`, `icon-text-rows`, `stat-callout`, `comparison-columns`, `timeline`, `image-half-bleed`, `card-grid`. This bakes good layout variety into the cheap path.
- **Content slots are typed**: `text` (with `max_lines` optional), `image` (path + fit mode: cover/contain), `chart` (delegate to a chart spec → rendered to PNG via matplotlib at build time, sized exactly to its slot), `icon` (name from a vendored icon set, rendered into a colored circle), `spacer`.
- Schema versioned (`version: 1`), validated by pydantic with precise error paths so the agent can self-correct from error messages alone.

**Acceptance**

- JSON Schema exported for the IR (agents and editors can validate without running the tool).
- 10 example decks in `examples/` covering every component.
- Malformed IR produces errors that name the YAML path and the fix.

## Phase 3 — Layout engine

**Tasks**

1. Slide canvas: 16:9 default (12192000 × 6858000 EMU), 4:3 optional. All internal math in EMU.
2. Flex solver: two-pass (measure, then assign). Intrinsic sizes for text come from Phase 1 wrapping; images/charts from declared aspect ratio; rows/columns aggregate children + gaps + padding.
3. Text auto-fit policy, in priority order and recorded in the layout report: (1) wrap within box; (2) if `shrink: true`, step font down to the tier's floor — **body floor is 32pt, hard**; (3) otherwise emit lint error `E_OVERFLOW` — never silently truncate, never shrink past the floor. With a 32pt minimum, the honest fix for too much text is less text or another slide, and the error message should say so.
4. **Chrome layer:** the page-number box is laid out last on every slide — a fixed-size 16pt text box anchored to the bottom-right corner — and recorded in `ResolvedDeck` like any other node so the linter and emitter treat it uniformly.
5. Output: `ResolvedDeck` — every node annotated with absolute rect, every text node with its line boxes. Serializable to JSON (`slidekit layout deck.yaml --json`) so the agent or tests can inspect geometry without rendering anything.

**Acceptance**

- Golden-file tests: each example deck's resolved JSON is committed; layout changes show up as reviewable diffs.
- Determinism test: two runs produce byte-identical resolved JSON.
- Fuzz test: random valid IR trees never produce NaN/negative sizes or crashes.

## Phase 4 — Linter (the replacement for visual QA)

Every check the image-inspection prompt performs, implemented as geometry/style assertions over `ResolvedDeck`. Errors block the build; warnings are reported.

**Errors (block)**

- `E_OVERFLOW` — text lines exceed box (after slack), or content exceeds slide bounds
- `E_OVERLAP` — intersecting rects not in an intentional `stack`
- `E_MARGIN` — content closer than 0.5" to slide edge
- `E_GAP` — sibling blocks closer than 0.3"
- `E_CONTRAST` — text/icon vs. effective background below WCAG-ish ratio (4.5:1 body, 3:1 for ≥24pt)
- `E_MIN_BODY_SIZE` — any body text below 32pt (hard rule; this is an error, not a warning). Page-number chrome (16pt, bottom-right) is the only exemption.
- `E_PAGE_NUMBER` — page numbering enabled but a slide's number is missing, mispositioned (not bottom-right), or overlapped by content
- `E_FONT` — font outside the safe set

**Warnings**

- Same layout component used on >2 consecutive slides; centered body text; text-only slide (no image/chart/icon/shape); title smaller than 1.4× body size (weak hierarchy); absolute `pin` used; raw hex color in slide body; >6 bullets in one list; uneven whitespace distribution (largest empty region > 3× median)
- Style-rule warnings encoding known anti-patterns: accent line directly under a title; full-width header/footer bars; edge stripes on cards (detect thin rects ≤6pt thick flush to a parent edge)

**Output:** JSON list `{code, slide, node_path, message, suggested_fix}` — designed so an agent can fix-and-rebuild without seeing a single pixel.

**Acceptance:** a fixture deck containing one instance of every defect; the linter must catch all of them. A clean deck produces zero errors.

## Phase 5 — Emitters

**pptx (primary):** python-pptx, placing every shape at its resolved EMU rect with auto-fit OFF and word-wrap ON (our layout already did the fitting — disable PowerPoint's). Explicit font runs, theme colors written as literal RGB (no reliance on the file's theme part), images pre-resized/cropped at build time to their slot. Round-trip test: emit → reopen with python-pptx → assert positions/sizes match resolved geometry exactly.

**HTML debug preview (secondary, ~1 day):** absolute-positioned divs from the same resolved geometry. Purely for a human spot-check; never used by the agent loop.

**Google Slides:** v1 ships .pptx (imports cleanly into Slides). A native Slides-API emitter is a later phase — same resolved geometry, different backend — only if pptx-import fidelity proves insufficient.

## Phase 6 — Verification harness (CI only, not inner loop)

One scripted smoke test: build all example decks → `soffice --headless --convert-to pdf` → `pdftoppm` → run cheap pixel heuristics (no LLM): ink within margins, no text pixels outside computed text rects (±slack). Runs in CI on layout/metrics changes to catch drift between our math and a real renderer. **Explicitly not part of deck generation.** If this harness disagrees with the linter, the fix goes into metrics/layout/slack — never into a per-deck visual loop.

## Phase 7 — Agent interface

- `SKILL.md` for the tool: when to use, IR cheatsheet, component gallery with thumbnails, the build/fix loop ("run `slidekit build`; if lint errors, edit IR per `suggested_fix`; rebuild — do not render images").
- `slidekit new --template <component-mix>` scaffolds a themed starter deck so the agent edits rather than authors from blank.
- Error-message quality is a feature: every lint error names the IR path and a concrete fix. Test this by feeding errors to a fresh agent session and measuring fix-on-first-try rate.

## Phase 8 — agency-agents integration

Integrate with [github.com/msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) so its persona subagents produce decks through slidekit instead of ad-hoc pptx code + screenshot QA. **Hard prerequisite: Phase 4 linter is real and trusted.** An agent persona pointing at a tool that can't prove correctness is just that repo's Document Generator with extra steps.

**Tasks**

1. **Author a `Deck Builder` agent** in the agency-agents template format (frontmatter with name/description/color; Identity & Memory; Core Mission; Critical Rules; Technical Deliverables; Workflow Process; Success Metrics). Its contract:
   - Deliverable is **slidekit IR YAML only** — never raw python-pptx/pptxgenjs code, never direct .pptx manipulation.
   - Workflow is `slidekit build deck.yaml` → read JSON lint errors → edit IR per `suggested_fix` → rebuild. **Never renders or inspects screenshots.**
   - Critical Rules embed the Phase 7 IR cheatsheet and component gallery so the agent file is self-sufficient when installed standalone.
   - Success metric: lint-clean on ≤2 build iterations.
   - Install target: `~/.claude/agents/` via the repo's `install.sh` conventions (file named `specialized/specialized-deck-builder.md` if upstreaming via PR).
2. **Define handoff seams** matching the IR's structure, so upstream personas slot in without knowing slidekit internals:
   - **Brand Guardian** → emits the IR `theme` block (palette roles, type scale, motif). Document the expected YAML shape in the agent file.
   - **Visual Storyteller / Content Creator** → emit a structured slide outline (per-slide: intent, component suggestion, copy, asset refs) as markdown the Deck Builder transcribes into IR.
   - **Agents Orchestrator** → pipeline definition: Brand Guardian → Storyteller → Deck Builder → `slidekit build`. Add this as a worked example in `examples/` (mirroring the repo's Nexus discovery exercise format).
3. **Retire visual QA for decks in the agency workflow.** Update the Deck Builder's rules and provide suggested language for Reality Checker certification: "deck is production-ready when `slidekit build` exits 0 (lint clean) and the round-trip test passes." Evidence Collector (screenshot QA) remains for UI work but is explicitly out of the deck path.
4. **Compatibility shim for the repo's Document Generator agent:** a short note in its style recommending delegation to Deck Builder + slidekit for .pptx outputs, keeping its other formats (PDF/DOCX/XLSX) untouched.

**Acceptance**

- Fresh Claude Code session with only the Deck Builder agent + slidekit installed turns a content outline into a lint-clean .pptx with zero screenshot tool calls.
- End-to-end orchestrated run (theme from Brand Guardian fixture, outline from Storyteller fixture) produces a deck where the theme block round-trips into emitted colors/fonts exactly.

---

## Build order

Phases 1 → 8, strictly in order — every later phase consumes the prior phase's outputs. Two hard gates and one demo checkpoint:

- **After Phase 1:** if calibration can't get measured text widths within 2% of a real renderer, stop and reassess slack constants before writing the layout engine. This is the cheap kill-switch for the whole bet.
- **First-light demo (end of Phase 5):** the first openable output. Deliverable: `examples/demo-5.yaml` → `demo-5.pptx`, a 5-slide deck exercising one title slide, one two-column, one stat callout, one icon-text rows, one comparison — built lint-clean, with page numbers, with zero screenshot calls. This is the acceptance demo for the core thesis; treat it as a named milestone, not a side effect. (Earlier partial visibility: Phase 3's `--json` resolved geometry, and the optional HTML debug preview can be pulled forward a few hours after Phase 3 if a visual sanity check is wanted before the pptx emitter exists.)
- **Before Phase 8:** do not start the agency-agents integration until the Phase 4 linter ships; the Deck Builder agent's entire value proposition is "trust the lint output."

## Risks & mitigations

- **Line-break divergence from PowerPoint** (justification edge cases, East-Asian text): v1 supports left-aligned Latin text only; the slack margin absorbs small divergence; CI harness catches systematic drift.
- **LibreOffice (calibration) vs PowerPoint (target) differences:** calibrate only on the safe font set, where both render metric-identically.
- **Chart sizing:** charts are rasterized to exact slot dimensions at build time, so they can't overflow by construction.
- **Scope creep into foreign-deck editing:** out of scope; keep the existing inspect-render workflow for that and say so in SKILL.md.
- **Persona drift back to screenshot QA:** agency-agents' Evidence Collector culture defaults to visual proof. Mitigate by making the Deck Builder's rules prohibit rendering, and by making lint errors actionable enough (path + suggested_fix) that screenshots are never the easier route.

---

## Overnight routine (unattended nightly builds)

This project is built by a scheduled, unattended Claude Code session running nightly at midnight. Each session is stateless, so continuity lives in files: `PROGRESS.md` (phase/criterion checklist), `NIGHTLY_REPORTS/` (one report per session), and `NOTES.md` (objections and out-of-scope proposals). This plan file is saved as `PLAN.md` in the repo root and is the source of truth every session re-reads.

### Setup task (run once, by Claude Code, when handed this plan)

1. Initialize the repo if needed; place this file at `./PLAN.md`.
2. Create `./NIGHTLY_PROMPT.md` containing exactly the prompt in the next section (verbatim, no edits).
3. Create the schedule. Preferred: Claude Code's built-in scheduled tasks (`/schedule` — marketed as "Routines"), set to run `NIGHTLY_PROMPT.md` daily at 00:00 local time in this repo. Fallback if scheduled tasks are unavailable in this environment: a cron entry —
   `0 0 * * * cd <repo-path> && claude -p "$(cat NIGHTLY_PROMPT.md)" --allowedTools "Read,Edit,Write,Bash" >> cron.log 2>&1`
   — noting that cron does not load the shell profile, so required environment variables (auth, PATH to `claude`) must be set explicitly in the crontab or a wrapper script.
4. Permissions: prefer scoped `--allowedTools` over `--dangerously-skip-permissions`; the bypass flag is acceptable only if this runs inside an isolated container/VM.
5. Verify before finishing: run the nightly prompt once manually (this counts as night one and may begin Phase 1), confirm `PROGRESS.md` and the first nightly report were produced, and confirm the schedule is registered.

### NIGHTLY_PROMPT.md (verbatim contents)

```
You are running an unattended overnight session. No human is available — never ask
questions; make the conservative choice and record it.

PROJECT: Build "slidekit" per the plan in ./PLAN.md (the agent-first slide builder).
Read PLAN.md fully before doing anything. It is the source of truth for scope,
architecture, phase order, hard gates, and acceptance criteria. Do not deviate from
it; if you believe it's wrong, record the objection in NOTES.md and follow it anyway.

STATE — do this first:
- If ./PROGRESS.md does not exist, this is night one: initialize a git repo (if not
  already one), create PROGRESS.md with a checklist of every phase and acceptance
  criterion from PLAN.md, and create NIGHTLY_REPORTS/ and NOTES.md.
- If PROGRESS.md exists, read it and the most recent file in NIGHTLY_REPORTS/, then
  resume from the first unchecked item. Trust the state files over your assumptions.

WORK RULES:
1. Phases strictly in PLAN.md order. Respect both hard gates: (a) if Phase 1
   calibration cannot reach the 2% threshold, STOP building — spend remaining time
   diagnosing, write findings to NIGHTLY_REPORTS/, and mark the gate BLOCKED in
   PROGRESS.md; do not start the layout engine. (b) Phase 8 never starts before
   Phase 4 is complete and its defect-fixture test passes.
2. Test-first per the plan's acceptance criteria. An item is only checked off in
   PROGRESS.md when its acceptance test passes in this session. Run the full test
   suite before checking anything off; never check off on "should work."
3. Commit small and often with descriptive messages (e.g. "phase1: kerning pairs for
   Calibri bold"). Never leave the repo in a non-building state at session end — if
   mid-feature when wrapping up, stash or commit to a branch and note it.
4. Never render slides to images for QA. The whole point of this project is
   deterministic verification; the only sanctioned rendering is the Phase 6 CI
   harness, built as specified.
5. If blocked (missing dependency, ambiguous spec, failing install): try two
   reasonable alternatives, then record the blocker in PROGRESS.md with what you
   tried, skip to the next unblocked item IN THE SAME PHASE only, and move on.
   Never skip ahead a phase to route around a blocker.
6. No scope additions. Features not in PLAN.md go in NOTES.md as proposals, not code.

SESSION WRAP-UP — reserve the final portion of your effort for this, always:
- Run the full test suite one last time; fix or revert anything broken.
- Update PROGRESS.md checkboxes to match reality exactly.
- Write NIGHTLY_REPORTS/<YYYY-MM-DD>.md: what was completed (with commit hashes),
  test results summary, any blockers or gate status, and the exact next task for
  tomorrow's session in one sentence.
- If the Phase 5 first-light demo became possible this session, build
  examples/demo-5.yaml -> demo-5.pptx and flag it prominently in the report.
```

### Operator notes (for the human, not the routine)

- **Read night one's report before letting night two fire.** The Phase 1 calibration gate is the project's kill-switch; if it's BLOCKED, subsequent unattended runs will correctly refuse to proceed and burn sessions on diagnosis. That first go/no-go decision should be a human one.
- Morning check is one file: the newest entry in `NIGHTLY_REPORTS/`.
- Watch for the first-light flag in reports — that's `demo-5.pptx`, the first openable deck (end of Phase 5).
- `claude -p` usage on subscription plans draws from a separate Agent SDK credit (effective June 15, 2026); verify limits at https://code.claude.com/docs/en/headless before relying on nightly runs.

