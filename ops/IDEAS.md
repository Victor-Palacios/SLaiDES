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
- [x] **(approved → done)** Generated example inventory instead of hand-maintained lists — a tiny
  `scripts/` generator (mirroring `render_board.py`) that emits the example→slide-count /
  component index, with a sync test. Kills the exact staleness failure mode PR #6
  introduces and gives reviewers a single source of truth for "what's in `examples/`."
  _(effort: S; area: tooling/docs)_
  → **Done 2026-06-18 (board T-031):** `scripts/build_examples_index.py` →
  `docs/EXAMPLES_INDEX.md` (+`--check`), guarded by `tests/test_examples_index`.
- [x] **(approved)** Close Phase 9's last open acceptance — run + record the verify harness
  across all 42 example decks. PROGRESS.md line 114 ("verify harness passes on all new
  example decks") stays unchecked because `soffice`/`pdftoppm` aren't in the nightly image
  (47 skips). A one-shot CI job (or recorded operator run) with LibreOffice installed would
  let that box be checked honestly rather than perpetually skipped. _(effort: S–M; area:
  Phase 6/9 verify)_
  → **Done 2026-06-18 (board T-032):** the `verify-render` CI run (LibreOffice + poppler)
  rendered every example deck and passed the pixel harness — run 27781859805 on commit
  27817bb. PROGRESS line 114 now checked; **Phase 9 acceptance is complete.**
- [x] **(approved → done)** Adopt the area-weighted moment-of-balance formulation for the `_balance`
  sub-score (refs #16 Lok/Feiner/Ngai, #18 Zhang & Xue), behind a designed-beats-plain
  regression guard. The 2026-06-18 nightly report already logged this integration direction
  ("balance as a moment about the layout centre"; current `_balance` uses centroid distance,
  a special case) but left it unapplied — fully deterministic, no render, grounded in
  verified citations. _(effort: M; area: Phase 10 aesthetics)_
  → **Done 2026-06-18 (board T-030):** `_balance` now scores horizontal + vertical moment
  imbalance separately; RESEARCH_TRACE updated; designed-beats-plain guard green
  (big-number 85.6 > agents-in-ai 83.9 > all-components 82.0).
- [ ] **(rejected)** Deterministic slidekit-native component catalog —
  `slidekit catalog` that lays out component thumbnails via the **real** layout/emit engine
  (not ReportLab) into one reviewable deck/PDF. This captures the genuinely useful part of
  PR #6's "contact-sheet" idea (spotting duplicate design patterns across 40 components)
  while staying source-traceable and render-free. Flag as nice-to-have, not plan scope —
  only if the operator wants a gallery artifact. _(effort: M; area: emit/tooling)_
  → **Rejected 2026-06-18 (operator):** redundant with the dated combined-PDF review
  archive (already a full visual of every example), and true multi-up thumbnails would need
  rasterisation/down-scaling that the no-render, font-metric engine doesn't do — the
  distinctive feature is the architecturally awkward part. Not pursued.

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

## 2026-06-19

**No open PRs this run** (`gh pr list --state open` → `[]`; PR #6, evaluated on 2026-06-18,
is no longer open). Light ideation pass from current repo state: Phase 9 + the north-star
selection pipeline are complete; Phase 10 is in progress (T-019 `info_density` landed
2026-06-19 → **9 aesthetic sub-metrics**; **T-020** Harrington combiner is queued next;
**T-021** weight calibration stays DEFERRED for want of a human-labelled set); the standing
research task reached its **20/20 verified** reference target.

### PR evaluations

- _No open PRs._ Nothing to triage this run.

### Ideas to consider

- [ ] **(proposed)** Golden snapshot test for the 9 aesthetic sub-scores — commit a per-deck
  sub-score table (the same `examples/` decks already used for the designed-beats-plain
  guard) as a golden file, asserted byte-for-byte like the layout/resolved-JSON goldens.
  Today the invariant is only an *ordering* inequality (big-number > agents-in-ai >
  all-components); a value snapshot would surface silent drift in any one sub-metric as a
  reviewable diff, not just a rank flip. Pure arithmetic, no render. _(effort: S; area:
  Phase 10 scoring)_
- [ ] **(proposed)** Per-sub-score monotonicity property tests — for each of the 9 metrics, a
  test that programmatically degrades the underlying quantity (add overlap, crowd text,
  skew balance, clash hues) and asserts the score moves the correct direction. This is the
  deterministic analog of the Phase 6 verify-harness *sensitivity* test (which proved the
  pixel heuristic discriminates rather than trivially passing) applied to aesthetics — it
  guards against a metric that looks plausible but is effectively constant. _(effort: M;
  area: Phase 10 scoring)_
- [ ] **(proposed)** `slidekit score --explain` — per-slide attribution naming the lowest sub-score,
  the node(s) responsible, and a concrete fix sentence, in the same `{code, slide,
  node_path, message, suggested_fix}` shape lint errors use. This is what lets the Phase 7
  agent fix-loop act on aesthetic warnings (`W_AESTH_*`) the way it already acts on `E_`
  lint errors — closing the gap between "we compute 9 sub-scores" and "the agent can
  improve them without rendering." Builds on T-018's advisory warnings. _(effort: M; area:
  Phase 10 scoring + Phase 7 agent interface)_
- [ ] **(proposed)** Synthetic-degradation ranking benchmark as an interim guard for T-021 — since
  weight calibration is rightly DEFERRED (no human labels, and the honesty guard forbids a
  human-correlation claim), add a render-free benchmark that takes one clean deck, emits N
  deterministically-degraded variants, and asserts the *combiner* ranks clean-above-degraded
  monotonically. It gives confidence the weights/combiner discriminate without claiming
  human agreement — and pairs naturally with T-020 (the Harrington min-biased mode should
  make a single severe degradation dominate, which this benchmark would demonstrate).
  _(effort: M; area: Phase 10 scoring)_
- [ ] **(proposed)** RESEARCH_TRACE HEURISTIC-tolerance audit, now that the 20/20 reference target
  is reached — a one-pass check that every sub-metric row in `RESEARCH_TRACE.md` correctly
  distinguishes what is *sourced* (the metric's existence/direction) from what is still
  HEURISTIC (specific bands/tolerances), with a small test asserting each scored metric has
  a trace row. Keeps the "prove from source" claim honest as the bibliography stops growing
  and attention shifts to tightening provenance. _(effort: S; area: research/docs)_
