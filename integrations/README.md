# integrations/

## `agents/` — slidekit presentation agents

Agent definitions from slidekit's Phase 8 integration with
[agency-agents](https://github.com/msitarzewski/agency-agents). The full upstream
repo was originally **vendored** here as a 300-file point-in-time snapshot so the
integration could be authored and validated in-repo; on 2026-07-02 (operator-approved
cleanup) the snapshot was pruned to just the slidekit-relevant files:

- **slidekit-authored agents** (original work, written in the upstream template
  format): `specialized-deck-builder.md` (the Phase 8 deliverable),
  `specialized-aesthetic-director.md`, `specialized-slide-outline-architect.md`,
  `specialized-deck-repurposer.md`, `specialized-copy-tightener.md`,
  `specialized-brand-to-ir-translator.md`, `specialized-chart-spec-builder.md`.
- **Upstream files carrying slidekit edits**: `specialized-document-generator.md`
  (delegation note appended) and `testing-reality-checker.md` (deck-scoped
  certification language). These derive from upstream MIT-licensed content —
  see `LICENSE-upstream-MIT`.

These are documentation artifacts describing agent roles around the slidekit
pipeline; the *executable* selection path is `slidekit author` /
`slidekit.select.recommend` (see `docs/LAYOUT_SELECTION_GUIDE.md`). To use an agent
definition with the upstream project, copy the file into a checkout of
`msitarzewski/agency-agents`.
