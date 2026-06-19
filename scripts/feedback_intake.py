#!/usr/bin/env python3
"""Turn a *Layout feedback* issue into a FEEDBACK.yaml entry (run by feedback-intake.yml).

Reads the issue body/number from the environment (the workflow passes them as env vars,
never interpolated into a shell command, so an untrusted body can't inject), parses the
issue form, validates the layout against the registry, and merges one new comment into
FEEDBACK.yaml + regenerates FEEDBACK.md. On a parse/validation failure it writes nothing
and exits non-zero with an operator-facing message (the workflow then comments that
message on the issue). The author-is-owner gate lives in the workflow `if:`, not here.

Env:
  ISSUE_BODY    - the submitted issue-form body (required)
  ISSUE_NUMBER  - the issue number, for provenance (optional)
  FEEDBACK_DATE - YYYY-MM-DD to stamp (optional; defaults to today, UTC)
"""
import datetime as _dt
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from slidekit.feedback import store  # noqa: E402
from slidekit.feedback.intake import FeedbackParseError, parse_issue_form  # noqa: E402


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    number = os.environ.get("ISSUE_NUMBER", "").strip()
    today = os.environ.get("FEEDBACK_DATE") or _dt.date.today().isoformat()

    try:
        item = parse_issue_form(body)
    except FeedbackParseError as exc:
        print(f"FEEDBACK_INTAKE_ERROR: {exc}", file=sys.stderr)
        return 1

    item["source"] = f"issue #{number}" if number else None
    fb = store.load()
    merged = store.merge(fb, [item], today=today)
    store.save(merged)
    store.FEEDBACK_MD.write_text(store.render_markdown(merged), encoding="utf-8")

    new_id = merged.comments[-1].id
    # GitHub Actions output (consumed by the workflow's confirmation comment).
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"feedback_id={new_id}\n")
            fh.write(f"component={item['component']}\n")
    print(f"recorded {new_id} for layout '{item['component']}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
