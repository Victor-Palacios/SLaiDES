# IDEAS — PR triage & brainstorm inbox

A scheduled second session (`.github/workflows/pr-brainstorm.yml`, 13:30 UTC — 4.5 hours
after the nightly build) reads the open pull requests, evaluates each for utility against
`PLAN.md`, and appends a dated section below with its assessment and brainstormed ideas.

This file is an **inbox for the operator to review and approve** — nothing here is acted
on automatically. The brainstorm session is advisory only: it never merges, comments on,
or modifies PRs, and never changes product code.

## How to use it

Each idea is a checkbox with a status tag. To triage, edit the line in place:

- `- [ ] **(proposed)** …` — awaiting your decision (the brainstorm session writes these).
- `- [x] **(approved)** …` — you approve it.
- `- [ ] **(rejected)** …` — declined; kept for the record (optionally add a why).

**The loop:** once you mark an item `(approved)`, the **build nightly** picks it up — it is
the sanctioned channel for work beyond `PLAN.md`. The build session queues it onto the board
(`epic: ideas`) and annotates the line here in place: `… → queued as T-NNN`, then
`… → done (commit <hash>)` once it lands. You never have to file the task yourself.

The brainstorm session appends new dated sections and **never edits** items you have already
approved or rejected; the build session only *annotates* approved items with their queue/done
status — neither ever changes your `(approved)`/`(rejected)` decision.

---

<!-- The 13:30 UTC pr-brainstorm session appends dated sections below. -->

## 2026-06-18

First brainstorm run to append here. One open PR (#6); evaluated below plus a small
ideation pass from repo state (Phase 9 complete, Phase 10 in progress, research 18/20).

### PR evaluations

- **PR #6 — "Add PDF slide repetition summary"** (`codex/explain-multiple-pages-in-pdf-examples`,
  @Victor-Palacios) — **CLOSE** (or REVISE hard if the prose insight is wanted). Adds
  `docs/pdf-slide-repetition-summary.md` (analysis of why example PDFs are multi-page +
  three "reduce sameness" redesign proposals) and a committed binary
  `docs/pdf-slide-repetition-summary.pdf` generated with **ReportLab**.
  - *Accurate core:* the central finding is correct and source-traceable — a PDF's page
    count equals its deck's slide count because the emitter loops `resolved.slides` and
    calls `showPage()` per slide. That much fits the "prove from source" ethos.
  - *Against ethos / why CLOSE:* (1) it commits a **ReportLab-generated binary** into the
    repo — slidekit's PDFs come from its own deterministic pipeline, not a freehand
    third-party renderer; a binary PDF can't be diff-reviewed and just duplicates the
    `.md` prose. (2) The hardcoded page-count inventory (`11_…` through `42_testimonial`,
    specific counts) will rot the moment the example library changes — no test keeps it
    honest. (3) The "one-page specimen / drop the cover" alternatives push *against* the
    intentional per-deck `title-slide` cover convention, which exists for golden-file +
    verify-harness traceability — the doc itself concedes the repetition is "useful for
    test stability." No tests, no code change; net utility is one already-implicit
    sentence wrapped in a stale-prone doc + an off-ethos binary.
  - *If anything is salvaged:* keep only the one-line emitter insight (as a comment in
    `src/slidekit/emit/pdf_emitter.py` or a sentence in an existing doc); drop the binary;
    do not pursue the cover-removal redesigns.

### Ideas to consider

- [ ] **(rejected)** Document the per-deck `title-slide` cover as an intentional convention —
  a short note in `NOTES.md`/`docs/` stating that pairing a reusable cover with each
  component example is deliberate (golden + verify traceability), so future PRs don't
  re-propose removing it (as #6 did). _(effort: S; area: docs/conventions)_
  → **Rejected 2026-06-18 (operator): the opposite was decided.** The cover was never a
  real convention (undocumented since Phase 2; nothing depends on it) and repeating it on 39
  examples is redundant against the ethos. Covers were STRIPPED from the 39 single-component
  specimens (each is now a single unique-layout slide); the convention is now documented the
  other way in `NIGHTLY_PROMPT.md`/`docs/SLIDE_DESIGNS.md`/`SKILL.md`. PR #6's "one-page
  specimen" instinct was right (its binary-PDF execution was not).
- [ ] **(proposed)** Generated example inventory instead of hand-maintained lists — a tiny
  `scripts/` generator (mirroring `render_board.py`) that emits the example→slide-count /
  component index, with a sync test. Kills the exact staleness failure mode PR #6
  introduces and gives reviewers a single source of truth for "what's in `examples/`."
  _(effort: S; area: tooling/docs)_
- [ ] **(proposed)** Close Phase 9's last open acceptance — run + record the verify harness
  across all 42 example decks. PROGRESS.md line 114 ("verify harness passes on all new
  example decks") stays unchecked because `soffice`/`pdftoppm` aren't in the nightly image
  (47 skips). A one-shot CI job (or recorded operator run) with LibreOffice installed would
  let that box be checked honestly rather than perpetually skipped. _(effort: S–M; area:
  Phase 6/9 verify)_
- [ ] **(proposed)** Adopt the area-weighted moment-of-balance formulation for the `_balance`
  sub-score (refs #16 Lok/Feiner/Ngai, #18 Zhang & Xue), behind a designed-beats-plain
  regression guard. The 2026-06-18 nightly report already logged this integration direction
  ("balance as a moment about the layout centre"; current `_balance` uses centroid distance,
  a special case) but left it unapplied — fully deterministic, no render, grounded in
  verified citations. _(effort: M; area: Phase 10 aesthetics)_
- [ ] **(proposed, speculative)** Deterministic slidekit-native component catalog —
  `slidekit catalog` that lays out component thumbnails via the **real** layout/emit engine
  (not ReportLab) into one reviewable deck/PDF. This captures the genuinely useful part of
  PR #6's "contact-sheet" idea (spotting duplicate design patterns across 40 components)
  while staying source-traceable and render-free. Flag as nice-to-have, not plan scope —
  only if the operator wants a gallery artifact. _(effort: M; area: emit/tooling)_

## 2026-06-18 (16:45 UTC re-run)

Re-run of the brainstorm session a few minutes after the earlier 2026-06-18 section was
committed (`4a5202e`, 16:42 UTC). **Nothing changed in the interval — no new section is
warranted.** Recorded here only as an audit trail that the automation fired.

### PR evaluations

- **PR #6 — "Add PDF slide repetition summary"** — unchanged since the earlier evaluation
  (last touched 2026-06-18T02:51Z; still 1 commit, OPEN). Recommendation stands: **CLOSE**
  (or REVISE hard). See the full reasoning in the 2026-06-18 section above — not repeated
  here.

### Ideas to consider

- _None._ No new PRs and no repo-state change since the prior section; its five proposed
  ideas already cover the current surface. Deliberately not duplicating them.
