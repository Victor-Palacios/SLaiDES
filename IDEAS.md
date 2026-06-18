# IDEAS — PR triage & brainstorm inbox

A scheduled second session (`.github/workflows/pr-brainstorm.yml`, 15:00 UTC — 6 hours
after the nightly build) reads the open pull requests, evaluates each for utility against
`PLAN.md`, and appends a dated section below with its assessment and brainstormed ideas.

This file is an **inbox for the operator to review and approve** — nothing here is acted
on automatically. The brainstorm session is advisory only: it never merges, comments on,
or modifies PRs, and never changes product code.

## How to use it

Each idea is a checkbox with a status tag. To triage, edit the line in place:

- `- [ ] **(proposed)** …` — awaiting your decision (the session writes these).
- `- [x] **(approved)** …` — you approve; hand it to the build nightly / board when ready.
- `- [ ] **(rejected)** …` — declined; kept for the record (optionally add a why).

The session appends new dated sections and **never edits or deletes** items you have
already approved or rejected.

---

<!-- The 15:00 UTC pr-brainstorm session appends dated sections below. -->

_No brainstorm run has appended to this file yet. The first scheduled run (or a manual
`workflow_dispatch` of pr-brainstorm-slidekit) will add a `## <YYYY-MM-DD>` section here._
