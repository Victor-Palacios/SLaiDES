"""Operator layout-feedback loop.

A phone-native channel for per-layout comments that feeds the unattended build sessions,
mirroring the repo's established "structured file -> rendered markdown -> AI consumes
and annotates" pattern (cf. ops/board.yaml -> ops/BOARD.md):

  Feedback website (password-gated Netlify site under web/ — a gallery of all 40
    layouts with a good/bad verdict + comment per layout)
    -> netlify/functions/submit-feedback.js commits each submission as JSON under
       web/feedback-inbox/
    -> the web-feedback-intake workflow runs scripts/feedback_intake_web.py, which
       folds inbox files into ops/FEEDBACK.yaml (store.merge) and regenerates
       ops/FEEDBACK.md (store.render_markdown)
    -> build sessions read `status: open` items, queue board tasks, mark them done.

`store` holds the schema + load/merge/save/render; ops/FEEDBACK.yaml is the single
source of truth. (An earlier GitHub issue-form channel — form generator, body parser,
intake workflow — was retired 2026-07-02 in favour of the website.)
"""
