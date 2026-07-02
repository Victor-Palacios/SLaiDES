#!/usr/bin/env python3
"""Fold web/feedback-inbox/*.json submissions into FEEDBACK.yaml/.md + review state.

The feedback website commits one JSON file per submission to web/feedback-inbox/ (schema:
`{submitted_at, source, items: [{component, verdict, comment, severity}]}`). This script
canonicalises those into the same FEEDBACK.yaml the build sessions consume, reusing the
tested `slidekit.feedback.store` (so no schema logic is duplicated in the Netlify
function), maintains the website's review state (web/data/state.json), then deletes the
processed inbox files.

Verdict handling — FEEDBACK.yaml (the build sessions' work queue):
  * bad / note, or any non-empty comment  -> an actionable `open` comment in FEEDBACK.yaml
    (the comment text is prefixed with 👍/👎/📝 so the verdict survives)
  * a bare 👍 with no comment              -> positive signal only; not recorded as an open
    task (it would only add non-actionable noise)

Verdict handling — state.json (the website's review queue; THIS SCRIPT IS ITS ONLY
WRITER — build sessions must never edit it):
  * 👍 -> status "approved": the layout leaves the site's main (review) page and shows a
    ✓ chip in the gallery. Clears any earlier flag + before-snapshot.
  * 👎 -> status "flagged": snapshots the layout's CURRENT preview fragment (from
    web/data/previews.json) as the "before". When a fix later regenerates previews.json,
    the main page renders before vs current side by side until the operator approves.
    A repeat 👎 refreshes the snapshot — "before" is always what the operator last rejected.
  * note (comment, no verdict) -> FEEDBACK.yaml only; state untouched.
  * components no longer in the catalog are dropped from state on write (a layout that was
    deleted can't be reviewed).

Unknown components are skipped with a warning rather than failing the whole batch.

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
STATE_JSON = ROOT / "web" / "data" / "state.json"
PREVIEWS_JSON = ROOT / "web" / "data" / "previews.json"

_PREFIX = {"good": "👍", "bad": "👎", "note": "📝"}
_DEFAULT_TEXT = {"good": "looks good", "bad": "needs work", "note": "note"}
_FRAGMENT_KEYS = ("width_px", "height_px", "background", "nodes_html")


# ── review state (web/data/state.json) ─────────────────────────────────────────────

def load_state(path: Path = STATE_JSON) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("components", {})


def dumps_state(components: dict) -> str:
    body = {
        "note": ("Operator review state — maintained ONLY by scripts/feedback_intake_web.py. "
                 "approved = off the review page; flagged = show before/after until approved."),
        "components": {k: components[k] for k in sorted(components)},
    }
    return json.dumps(body, indent=2, ensure_ascii=False) + "\n"


def _load_fragments(previews_path: Path) -> dict:
    if not previews_path.exists():
        return {}
    data = json.loads(previews_path.read_text(encoding="utf-8"))
    return {
        c["component"]: {k: c[k] for k in _FRAGMENT_KEYS}
        for c in data.get("components", [])
    }


def apply_state(state: dict, comp: str, verdict: str, comment: str, date: str,
                fragments: dict) -> None:
    """Apply one verdict to the review state (mutates `state`)."""
    if verdict == "good":
        state[comp] = {"status": "approved", "date": date}
    elif verdict == "bad":
        entry = {"status": "flagged", "date": date, "comment": comment or _DEFAULT_TEXT["bad"]}
        frag = fragments.get(comp)
        if frag:
            entry["before"] = frag
        state[comp] = entry
    # "note" leaves state untouched.


# ── feedback ledger items ──────────────────────────────────────────────────────────

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
    state_json: Path = STATE_JSON,
    previews_json: Path = PREVIEWS_JSON,
    *,
    write: bool = True,
) -> dict:
    """Process every inbox JSON file into FEEDBACK.yaml/.md + state.json. Returns a summary."""
    files = sorted(inbox.glob("*.json"))
    fb = store.load(feedback_yaml)
    before_count = len(fb.comments)
    state = load_state(state_json)
    fragments = _load_fragments(previews_json)
    known = known_components()
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
        # Review state: every valid verdict (including bare 👍) updates state.
        date = _record_date(record)
        for it in record.get("items", []):
            comp = it.get("component")
            verdict = it.get("verdict")
            if comp in known and verdict in ("good", "bad"):
                apply_state(state, comp, verdict, (it.get("comment") or "").strip(),
                            date, fragments)
        processed.append(f)

    # A deleted layout can't be reviewed — drop stale state entries.
    stale = [c for c in state if c not in known]
    for c in stale:
        del state[c]

    added = len(fb.comments) - before_count
    summary = {
        "files": len(processed),
        "added": added,
        "positive_only": total_positive,
        "skipped_unknown": all_skipped,
        "approved": sorted(c for c, s in state.items() if s["status"] == "approved"),
        "flagged": sorted(c for c, s in state.items() if s["status"] == "flagged"),
        "state_dropped": sorted(stale),
    }

    if write and (processed or stale):
        store.save(fb, feedback_yaml)
        feedback_md.write_text(store.render_markdown(fb), encoding="utf-8")
        state_json.parent.mkdir(parents=True, exist_ok=True)
        state_json.write_text(dumps_state(state), encoding="utf-8")
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
    if summary["state_dropped"]:
        print(f"note: dropped state for deleted layouts: {summary['state_dropped']}", file=sys.stderr)
    print(
        f"processed {summary['files']} file(s): "
        f"+{summary['added']} open comment(s), {summary['positive_only']} bare-positive mark(s); "
        f"state: {len(summary['approved'])} approved, {len(summary['flagged'])} flagged"
        + (" [dry-run]" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
