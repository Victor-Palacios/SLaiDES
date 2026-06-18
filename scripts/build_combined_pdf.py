#!/usr/bin/env python3
"""Build the combined example review PDF as a DATED, retained archive.

The per-deck PDFs in `examples/pdf/<name>.pdf` remain the canonical, source-traceable
artifacts (one file per deck, built by `slidekit build --pdf`). This script adds a
single *review* aggregate of every example deck — but keeps a dated history of it so
the repo's visual evolution is preserved:

    examples/pdf/combined/all-examples_<YYYY-MM-DD>.pdf   # one snapshot per change-day
    examples/pdf/combined/manifest.json                  # {date, pages, layout_hash}[]
    examples/pdf/combined/INDEX.md                        # generated evolution log

A new dated snapshot is minted ONLY when the example decks' resolved layout actually
changes. "Layout" is fingerprinted by hashing each deck's resolved geometry
(`ResolvedDeck.to_json()` with non-deterministic node ids stripped, exactly as the
layout golden test does); if that fingerprint matches the most recent snapshot, this
script is a no-op. So re-running on an unchanged tree never creates duplicate or
spurious snapshots, and the archive stays meaningful (one entry per real change).

Each PDF is written in reportlab `invariant` mode, so its bytes are deterministic for
a given layout; the dated *filename* is the human-facing "when".

Usage:
  python scripts/build_combined_pdf.py            # snapshot today IF layout changed
  python scripts/build_combined_pdf.py --force     # snapshot today even if unchanged
  python scripts/build_combined_pdf.py --check     # verify the archive is in sync
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from slidekit.emit.pdf_emitter import emit_combined_pdf
from slidekit.ir import load
from slidekit.layout import resolve

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
OUT_DIR = ROOT / "examples" / "pdf" / "combined"
MANIFEST = OUT_DIR / "manifest.json"
INDEX = OUT_DIR / "INDEX.md"

# Node ids come from a global counter and vary run-to-run; strip them before hashing,
# the same normalization the layout golden test uses.
_NODE_ID_RE = re.compile(r'"node_id": "[^"]*"')
_COUNT_RE = re.compile(rb"/Count\s+(\d+)")


def _snapshot_path(date: str) -> Path:
    return OUT_DIR / f"all-examples_{date}.pdf"


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _decks():
    """(deck, ResolvedDeck) for every example deck, in sorted filename order."""
    for yaml_path in sorted(EXAMPLES_DIR.glob("*.yaml")):
        deck = load(yaml_path)
        yield deck, resolve(deck)


def _layout_fingerprint():
    """Return (sha256 of all decks' node-id-stripped resolved JSON, [(deck, rd), ...])."""
    decks, parts = [], []
    for deck, rd in _decks():
        decks.append((deck, rd))
        parts.append(_NODE_ID_RE.sub('"node_id": ""', rd.to_json()))
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest, decks


def _load_manifest() -> list:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return []


def _save_manifest(entries: list) -> None:
    MANIFEST.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _render_index(entries: list) -> str:
    lines = [
        "# Combined example PDFs — evolution log",
        "",
        "_Generated from `manifest.json` by `scripts/build_combined_pdf.py` — do not "
        "hand-edit. Each row is a dated snapshot `all-examples_<date>.pdf`, minted only "
        "when the example decks' resolved layout changed. Older snapshots are kept as the "
        "repo's visual history; the per-deck `examples/pdf/<name>.pdf` files stay canonical._",
        "",
        "| Snapshot | Pages | Layout fingerprint |",
        "|---|---|---|",
    ]
    for e in sorted(entries, key=lambda x: x["date"], reverse=True):
        lines.append(
            f"| `all-examples_{e['date']}.pdf` | {e['pages']} | `{e['layout_hash'][:12]}` |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _page_count(path: Path):
    """Page-tree /Count read from raw bytes (no PDF reader lib imports in this env)."""
    if not path.exists():
        return None
    counts = [int(m.group(1)) for m in _COUNT_RE.finditer(path.read_bytes())]
    return max(counts) if counts else None


def _check(fingerprint: str, manifest: list) -> int:
    problems = []
    if not manifest:
        problems.append("manifest.json is empty — run `python scripts/build_combined_pdf.py`")
    else:
        latest = manifest[-1]
        if latest["layout_hash"] != fingerprint:
            problems.append(
                f"layouts changed since the last snapshot ({latest['date']}) — run "
                "`python scripts/build_combined_pdf.py` to add a new dated snapshot"
            )
        snap = _snapshot_path(latest["date"])
        data = snap.read_bytes() if snap.exists() else b""
        if not (data.startswith(b"%PDF") and data.rstrip().endswith(b"%%EOF")):
            problems.append(f"{snap.name} is missing or not a well-formed PDF")
        elif _page_count(snap) != latest["pages"]:
            problems.append(f"{snap.name} page count != manifest ({latest['pages']})")
        current_index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if current_index != _render_index(manifest):
            problems.append("INDEX.md is out of sync with manifest.json")
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    latest = manifest[-1]
    print(f"combined archive in sync (latest {latest['date']}, {latest['pages']} pages).")
    return 0


def main(argv: list) -> int:
    fingerprint, decks = _layout_fingerprint()
    manifest = _load_manifest()

    if "--check" in argv:
        return _check(fingerprint, manifest)

    latest = manifest[-1] if manifest else None
    if latest and latest["layout_hash"] == fingerprint and "--force" not in argv:
        print(f"no layout change since {latest['date']} — no new snapshot written.")
        return 0

    date = _today()
    out = _snapshot_path(date)
    pages = emit_combined_pdf(decks, out)
    # Upsert today's entry (overwrite same-day rather than duplicate); keep date order.
    manifest = [e for e in manifest if e["date"] != date]
    manifest.append({"date": date, "pages": pages, "layout_hash": fingerprint})
    manifest.sort(key=lambda x: x["date"])
    _save_manifest(manifest)
    INDEX.write_text(_render_index(manifest), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({pages} pages); "
          f"archive now has {len(manifest)} snapshot(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
