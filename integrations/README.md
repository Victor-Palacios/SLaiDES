# integrations/

## `agency-agents/` — vendored copy

A **point-in-time snapshot** of [github.com/msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents),
vendored here so slidekit's Phase 8 integration (PLAN.md) can be authored and
validated entirely inside this repo without cross-repo access.

- Upstream commit: see `agency-agents/.VENDORED_FROM`.
- License: upstream is **MIT** (`agency-agents/LICENSE`) — preserved unmodified.
- This is a copy, not a submodule: it does **not** track upstream updates.

### What slidekit adds to this tree

- `agency-agents/specialized/specialized-deck-builder.md` — the Deck Builder
  agent (slidekit's Phase 8 deliverable). Authored in the repo's own template
  format and validated with `agency-agents/scripts/lint-agents.sh`.
- A delegation note appended to `agency-agents/specialized/specialized-document-generator.md`
  (the compatibility shim from PLAN.md Phase 8, task 4).

### Upstreaming (optional, later)

To contribute the Deck Builder agent back to the original project, open a PR
against `msitarzewski/agency-agents` adding only
`specialized/specialized-deck-builder.md` (and the Document Generator note).
Nothing here pushes upstream automatically.
