# NOTES — objections and out-of-scope proposals

Per PLAN.md work rule 6: features not in PLAN.md are recorded here as
proposals, not code. Objections to the plan are recorded here and the plan
is followed anyway.

## Deviations recorded at setup (2026-06-13)

- **Scheduling mechanism.** PLAN.md prefers Claude Code's built-in scheduled
  tasks (`/schedule` Routines) and falls back to a crontab entry. This project
  is hosted in Claude Code on the web, where each session runs in an ephemeral
  container: a crontab written here would vanish when the container is
  reclaimed, and Routines cannot be registered from inside a session. The
  durable equivalent chosen instead is a scheduled GitHub Actions workflow
  (`.github/workflows/nightly.yml`) running Claude Code headless with the
  verbatim NIGHTLY_PROMPT.md, scoped to `--allowedTools "Read,Edit,Write,Bash"`
  as the plan specifies. Requires the `CLAUDE_CODE_OAUTH_TOKEN` repo secret
  (subscription auth, per operator decision 2026-06-13; `ANTHROPIC_API_KEY`
  is the API-billing alternative) — see README. The operator may alternatively
  register a Routine from the Claude Code UI pointing at this repo with the
  same prompt; if so, disable the workflow to avoid double runs.

## Deviations recorded during Phase 6 (2026-06-13, session 2)

- **CI workflow originally shipped under `ci/`, now installed.** The Phase 6
  verification harness needs its own GitHub Actions workflow. The unattended
  nightly bot authenticates as a GitHub App whose token lacks the `workflows`
  permission, so `git push` is rejected when the diff creates or edits any file
  under `.github/workflows/`. The bot therefore parked it at `ci/verify.yml`.
  RESOLVED 2026-06-13 (session 2 follow-up): installed to
  `.github/workflows/verify.yml` from an operator-scoped session that carries the
  `workflows` permission; the `ci/` parking directory was removed.

- **Icon emitter changed from text label to colored circle.** The Phase 5 icon
  emitter rendered an unmeasured `[name]` text label, centered with word-wrap off,
  into the icon slot. The Phase 6 harness caught this as ~1.7% stray ink on
  icon-bearing decks: in LibreOffice the label overflowed its slot symmetrically.
  Per PLAN.md's rule that harness/linter disagreements are fixed in emit/layout
  (never a per-deck visual loop), the emitter now draws a colored circle inscribed
  in the slot — which is what the Phase 2 spec specified for icons all along
  ("rendered into a colored circle"). Round-trip tests are unaffected (they inspect
  text-box shapes only); all example decks now pass the harness.

## Phase 8 approach (2026-06-13, operator-directed)

- **agency-agents vendored into this repo on a dedicated branch.** Per operator
  decision, Phase 8 is done entirely inside slaides rather than against the external
  `msitarzewski/agency-agents` repo (which this session can't write to). The repo is
  copied to `integrations/agency-agents/` (MIT, point-in-time snapshot; upstream SHA
  in `.VENDORED_FROM`) on branch `agency-agents-integration`, kept off the slidekit
  dev branch so the foreign tree doesn't tangle with slidekit's source. Nothing is
  pushed upstream; contributing the Deck Builder agent back to msitarzewski is a
  separate, optional fork-and-PR step.

- **NIGHTLY_PROMPT.md is no longer strictly verbatim.** PLAN.md's setup said to keep
  it verbatim, but the operator directed changing the instructions so an unattended
  Opus session can finish Phase 8. A clearly-marked "PHASE 8 ADDENDUM" was appended
  (the original prompt body is unchanged above it). It tells the routine that Phase 8
  lives on `agency-agents-integration`, where the vendored repo and Deck Builder agent
  are, how to validate agent files (`lint-agents.sh`), and the remaining items.

- **Phase 8 runs on `agency-agents-integration`, not `claude/busy-rubin-mzpvfu`.** To
  have Opus finish Phase 8, dispatch the nightly workflow against this branch (same
  mechanism used for runs 6-8). The scheduled cron only picks up Phase 8 automatically
  if this branch is made the default branch; otherwise drive it by dispatch.

## Proposals

(none yet)

## Phase 9 scope expansion + research-access blocker (2026-06-14, operator-directed)

- **Scope expansion beyond original PLAN.md.** The operator directed growing the
  component library from 8 to **40 core slide designs**. This is past the v1 plan's
  scope, so per work rule 6 it is recorded here; it is operator-authorized, not an
  unsanctioned addition. Blueprint: `docs/SLIDE_DESIGNS.md`; tracked as Phase 9 in
  PROGRESS.md; build instructions appended to NIGHTLY_PROMPT.md.

- **Research sources unreachable.** The operator provided a ChatGPT share and a Grok
  share to inform the 40-design catalog. The execution environment's network egress
  allowlist blocks `chatgpt.com` and `grok.com` ("Host not in allowlist"), so neither
  WebFetch nor curl can read them. The catalog was therefore built from established
  presentation-design practice. To integrate the research, add those hosts to the
  environment's egress settings (see code.claude.com/docs/en/claude-code-on-the-web)
  or paste the content; then reconcile against docs/SLIDE_DESIGNS.md.

## Phase 10: computational-aesthetics research integrated (2026-06-14, operator-provided)

- The operator pasted a research synthesis (the chatgpt.com/grok.com shares being
  egress-blocked) arguing slide aesthetics are mathematically definable/measurable.
  Integrated as Phase 10: a deterministic aesthetic scoring layer over the
  ResolvedDeck (balance, alignment, whitespace, non-overlap, contrast, color
  harmony, density, hierarchy, cross-slide consistency). Spec: `docs/AESTHETICS.md`.
- Fit rationale: slidekit already computes exact element geometry, so these metrics
  are arithmetic over existing data — no screenshots, consistent with the project
  thesis. Scoring is ADVISORY (warnings + 0–100 score); the linter remains the gate.
- Honesty guard recorded in the spec: do not claim human-judgment correlation
  without a labeled slide-pair dataset (calibration deferred).

## Nightly cron re-enabled + standing research task (2026-06-14, operator-directed)

- **Cron re-enabled.** The schedule in `.github/workflows/nightly.yml` (07:00 UTC ≈
  midnight Pacific) was re-enabled to continue the work: each run advances the current
  build phase (Phase 9 designs → Phase 10 aesthetics) AND the standing research task.
  Recurring Opus spend resumes (~$7–50/session) — operator-accepted.
  *(Update 2026-06-16: shifted 2h later to 09:00 UTC ≈ 02:00 Pacific, operator request.)*
- **Web tools added to the nightly allowlist.** `claude_args` now includes
  `WebSearch,WebFetch` (added to Read/Edit/Write/Bash) so the unattended session can
  discover and verify new research online. GitHub runners have open egress (unlike the
  Claude-Code-web environment whose allowlist blocks chatgpt.com/grok.com).
- **Standing research task.** Every session grows `docs/REFERENCES.md` toward ~20
  VERIFIED references on mathematical/aesthetic slide design and integrates concrete
  deterministic metrics into Phase 10. Verify before citing; keep all metrics
  render-free; never gate the build on a learned score.

## North-star realignment (2026-06-18, operator-directed)

An operator audit re-anchored the project on its core goal: **~40 slide layouts that render
reproducibly from recorded geometry, with an LLM (no vision) picking which layout per slide
for a given topic.** Three read-only audits found: (1) the deterministic render/geometry core
is exactly on-goal and done; (2) "40 distinct layouts" was padded — only ~25 are structurally
distinct skeletons, ~15 are styled variants; (3) the LLM-selection half of the pipeline did
not exist in-repo (only un-wired agency-agent scaffolds). Recent advisory/meta work
(aesthetic scorer, research bibliography, board, brainstorm, dated PDF archive, example index)
was disciplined but did not advance (2) or (3).

Fix (operator decisions: consolidate to an honest taxonomy; build BOTH an LLM selection
guide + `slidekit author` AND a deterministic recommender):
- `src/slidekit/catalog/registry.py` — single source of truth: 40 components → 25 distinct
  families + 15 variants, plus selection metadata; fields derived from the IR models.
- `docs/LAYOUT_TAXONOMY.md` (honest count) and `docs/LAYOUT_SELECTION_GUIDE.md` +
  `slidekit catalog --json` (LLM picks layouts, vision-free), both generated + sync-tested.
- `src/slidekit/select/recommend.py` (content-shape → component) and `slidekit author`
  (outline → recommend/validate → lint → render), with `examples/author-demo/`.
The aesthetic scorer and standing research are now BACKGROUND (kept, not deleted). See the
NIGHTLY_PROMPT "NORTH-STAR PRIORITY" section.
