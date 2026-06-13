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
- ALSO write a complementary executive summary next to that report, named
  NIGHTLY_REPORTS/<same-report-basename>-exec-summary.md (e.g. report
  2026-06-14.md -> 2026-06-14-exec-summary.md; if you suffix the report like
  -session2, mirror it). It must have exactly two sections for a NON-TECHNICAL
  reader: first "## ELI5" (explain-like-I'm-5: short, plain language, analogies
  welcome, no jargon — no code names, file paths, or tool names), then
  "## Broad strokes" (still non-technical, a few short paragraphs on what happened
  this session and why it matters). Every report gets one; never skip it.
- If the Phase 5 first-light demo became possible this session, build
  examples/demo-5.yaml -> demo-5.pptx and flag it prominently in the report.

=== PHASE 8 ADDENDUM (added 2026-06-13; branch agency-agents-integration) ===
State of the build has advanced: slidekit Phases 1-7 are COMPLETE. The only
remaining work is Phase 8, and it is being done on the branch
`agency-agents-integration` (NOT claude/busy-rubin-mzpvfu). If you are running on
this branch, commit and push Phase 8 work HERE.

Phase 8 environment (already set up — do not redo):
- The agency-agents repo is VENDORED at `integrations/agency-agents/` (MIT, a
  point-in-time snapshot; see integrations/README.md). Do NOT re-clone it and do
  NOT edit files in that tree except the three integration artifacts below.
- The Deck Builder agent is authored and lint-clean:
  `integrations/agency-agents/specialized/specialized-deck-builder.md`.
- The Document Generator delegation note is added.

Validate ANY agent-markdown you add or edit with the repo's own linter:
  `bash integrations/agency-agents/scripts/lint-agents.sh <file>`
  (and `check-agent-originality.sh <file>`); both must PASS before you check an
  item off. Run the slidekit test suite too — never regress Phases 1-7.

Remaining Phase 8 items are the `[~]` and `[ ]` lines in PROGRESS.md "Phase 8".
Work them in order:
1. Orchestrator worked example under examples/: a Brand Guardian theme fixture +
   a Visual Storyteller outline fixture (markdown, per the Deck Builder agent's
   handoff-seam shapes) + the resulting deck.yaml built lint-clean to .pptx.
2. Apply the Reality-Checker certification language (from the Deck Builder agent's
   "To Reality Checker" seam) into
   integrations/agency-agents/testing/testing-reality-checker.md, scoped to decks
   only — leave Evidence Collector / screenshot QA for UI work untouched.
3. ACCEPTANCE (automate as tests, no screenshots): (a) feed the outline fixture
   through `slidekit build`; assert exit 0, empty lint errors, zero render calls.
   (b) build the worked-example deck from the theme fixture, reopen the .pptx, and
   assert the emitted RGB/fonts equal the theme block exactly (extend the existing
   round-trip test style).
Never render slides to images for QA — the Deck Builder contract forbids it.
