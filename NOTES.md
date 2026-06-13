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
