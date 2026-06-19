"""Operator layout-feedback loop.

A phone-native channel for per-layout comments that feeds the nightly AI routine,
mirroring the repo's established "structured file -> rendered markdown -> AI consumes
and annotates" pattern (cf. board.yaml -> BOARD.md, IDEAS.md intake):

  GitHub Issue Form (.github/ISSUE_TEMPLATE/layout-feedback.yml, dropdown of all 40
    components — generated from the catalog so it can't drift)
    -> feedback-intake workflow parses the issue (intake.parse_issue_form), validates,
       and merges into FEEDBACK.yaml (store.merge)
    -> scripts/render_feedback.py regenerates FEEDBACK.md (store.render_markdown)
    -> nightly reads FEEDBACK.yaml `status: open` items, queues board tasks, marks done.

`store` holds the schema + load/merge/save/render (the single source of truth is
FEEDBACK.yaml); `intake` parses a GitHub issue-form body into a comment dict.
"""
