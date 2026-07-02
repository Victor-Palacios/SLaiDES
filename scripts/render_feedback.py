#!/usr/bin/env python3
"""Render operator layout feedback: FEEDBACK.yaml (source of truth) -> FEEDBACK.md.

FEEDBACK.yaml is filed via the feedback website (folded in by the
web-feedback-intake workflow) and driven by the nightly; FEEDBACK.md is the generated,
committed view. Deterministic by construction (comments sorted by id, `last change`
from max(updated) — never wall-clock), and a test (tests/test_feedback) asserts
FEEDBACK.md stays in sync, the same spirit as BOARD.md / the layout goldens.

Usage:
  python scripts/render_feedback.py            # validate + (re)write FEEDBACK.md
  python scripts/render_feedback.py --check     # validate only; non-zero exit if stale
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from slidekit.feedback import store  # noqa: E402


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    try:
        fb = store.load()
    except Exception as exc:  # noqa: BLE001 — clean message to the operator
        print(f"FEEDBACK.yaml invalid: {exc}", file=sys.stderr)
        return 1
    out = store.render_markdown(fb)
    if check_only:
        current = store.FEEDBACK_MD.read_text(encoding="utf-8") if store.FEEDBACK_MD.exists() else ""
        if current != out:
            print(
                "FEEDBACK.md is out of sync with FEEDBACK.yaml — run "
                "`python scripts/render_feedback.py`",
                file=sys.stderr,
            )
            return 1
        print("FEEDBACK.yaml valid and FEEDBACK.md in sync.")
        return 0
    store.FEEDBACK_MD.write_text(out, encoding="utf-8")
    print(f"wrote {store.FEEDBACK_MD.relative_to(ROOT)} ({len(fb.comments)} comments)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
