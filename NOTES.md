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

- **CI workflow ships under `ci/`, not `.github/workflows/`.** The Phase 6
  verification harness needs its own GitHub Actions workflow. The unattended
  nightly bot authenticates as a GitHub App whose token lacks the `workflows`
  permission, so `git push` is rejected when the diff creates or edits any file
  under `.github/workflows/`. The workflow is therefore committed to
  `ci/verify.yml` with install instructions in `ci/README.md`; an operator (or a
  token carrying `workflows` scope) copies it into `.github/workflows/` once. The
  harness code, CLI (`slidekit verify`), and test suite (`tests/test_verify`) are
  fully functional locally and in any CI that installs the workflow — only the
  one-line install of the workflow file is gated on the permission.

- **Icon emitter changed from text label to colored circle.** The Phase 5 icon
  emitter rendered an unmeasured `[name]` text label, centered with word-wrap off,
  into the icon slot. The Phase 6 harness caught this as ~1.7% stray ink on
  icon-bearing decks: in LibreOffice the label overflowed its slot symmetrically.
  Per PLAN.md's rule that harness/linter disagreements are fixed in emit/layout
  (never a per-deck visual loop), the emitter now draws a colored circle inscribed
  in the slot — which is what the Phase 2 spec specified for icons all along
  ("rendered into a colored circle"). Round-trip tests are unaffected (they inspect
  text-box shapes only); all example decks now pass the harness.

## Proposals

(none yet)
