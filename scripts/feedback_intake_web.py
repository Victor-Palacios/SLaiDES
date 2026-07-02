#!/usr/bin/env python3
"""Fold web/feedback-inbox/*.json submissions into FEEDBACK.yaml + FEEDBACK.md.

The feedback website commits one JSON file per submission to web/feedback-inbox/ (schema:
`{submitted_at, source, items: [{component, verdict, comment, severity}]}`). This script
canonicalises those into the same FEEDBACK.yaml the nightly consumes, reusing the tested
`slidekit.feedback.store` (so no schema logic is duplicated in the Netlify function), then
deletes the processed inbox files.

Verdict handling:
  * bad / note, or any non-empty comment  -> an actionable `open` comment in FEEDBACK.yaml
    (the comment text is prefixed with 👍/👎/📝 so the verdict survives)
  * a bare 👍 with no comment              -> positive signal, counted but not recorded as an
    open task (it would only add non-actionable noise for the nightly)

Unknown components (which the website can't produce, but a hand-crafted request could) are
skipped with a warning rather than failing the whole batch.

Run with no args to process the repo's inbox; `--dry-run` reports without writing/deleting.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slidekit.feedback import store  # noqa: E402
from slidekit.feedback.store import known_components  # noqa: E402

INBOX = ROOT / "web" / "feedback-inbox"

_PREFIX = {"good": "👍", "bad": "👎", "note": "📝"}
_DEFAULT_TEXT = {"good": "looks good", "bad": "needs work", "note": "note"}


def actionable_items(record: dict) -> tuple[list[dict], int, list[str]]:
    """Return (merge-items, positive-only count, skipped-component warnings) for one record."""
    known = known_components()
    items: list[dict] = []
    positives = 0
    skipped: list[str] = []
    source = f"web {record.get('submitted_at', '')}".strip()
    for it in record.get("items", []):
        comp = it.get("component")
        if comp not in known:
            skipped.append(str(comp))
            continue
        verdict = it.get("verdict") if it.get("verdict") in _PREFIX else "note"
        comment = (it.get("comment") or "").strip()
        if verdict == "good" and not comment:
            positives += 1
            continue
        text = comment or _DEFAULT_TEXT[verdict]
        severity = it.get("severity") if it.get("severity") in ("low", "med", "high") else "med"
        items.append(
            {
                "component": comp,
                "comment": f"{_PREFIX[verdict]} {text}",
                "severity": severity,
                "source": source,
            }
        )
    return items, positives, skipped


def _record_date(record: dict) -> str:
    stamp = record.get("submitted_at") or ""
    return stamp[:10] if len(stamp) >= 10 else datetime.date.today().isoformat()


def fold(
    inbox: Path = INBOX,
    feedback_yaml: Path = store.FEEDBACK_YAML,
    feedback_md: Path = store.FEEDBACK_MD,
    *,
    write: bool = True,
) -> dict:
    """Process every inbox JSON file into FEEDBACK.yaml/.md. Returns a summary dict."""
    files = sorted(inbox.glob("*.json"))
    fb = store.load(feedback_yaml)
    before = len(fb.comments)
    total_positive = 0
    all_skipped: list[str] = []
    processed: list[Path] = []

    for f in files:
        try:
            record = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"skip {f.name}: unreadable ({exc})", file=sys.stderr)
            continue
        items, positives, skipped = actionable_items(record)
        total_positive += positives
        all_skipped += skipped
        if items:
            fb = store.merge(fb, items, today=_record_date(record))
        processed.append(f)

    added = len(fb.comments) - before
    summary = {
        "files": len(processed),
        "added": added,
        "positive_only": total_positive,
        "skipped_unknown": all_skipped,
    }

    if write and processed:
        store.save(fb, feedback_yaml)
        feedback_md.write_text(store.render_markdown(fb), encoding="utf-8")
        for f in processed:
            f.unlink()

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report without writing or deleting")
    args = ap.parse_args()

    summary = fold(write=not args.dry_run)
    if summary["skipped_unknown"]:
        print(f"warning: skipped unknown components: {summary['skipped_unknown']}", file=sys.stderr)
    print(
        f"processed {summary['files']} file(s): "
        f"+{summary['added']} open comment(s), {summary['positive_only']} bare-positive mark(s)"
        + (" [dry-run]" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
