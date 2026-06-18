"""Guards for the dated combined-example PDF archive (examples/pdf/combined/).

Mirrors the layout golden / board sync pattern: the archive is committed and these
tests assert it stays in sync with the example decks, so it can never silently drift.

- The newest snapshot named in manifest.json exists and is a well-formed PDF whose
  page count matches the manifest.
- The newest snapshot's layout fingerprint equals the CURRENT resolved geometry — i.e.
  if a deck/engine change alters layouts without a fresh `build_combined_pdf.py` run,
  this fails (run the builder to mint a new dated snapshot).
- INDEX.md is a faithful render of manifest.json (like BOARD.md ↔ board.yaml).
- emit_combined_pdf is byte-deterministic within a run (invariant mode).

No PDF *reader* library imports in this environment (broken crypto backend), so PDF
structure is checked from raw bytes, exactly as scripts/build_combined_pdf.py does.
"""

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "build_combined_pdf", ROOT / "scripts" / "build_combined_pdf.py"
)
bcp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bcp)


def test_latest_snapshot_exists_and_valid():
    manifest = bcp._load_manifest()
    assert manifest, "manifest.json should list at least one snapshot"
    latest = manifest[-1]
    snap = bcp._snapshot_path(latest["date"])
    data = snap.read_bytes()
    assert data.startswith(b"%PDF"), f"{snap.name} is not a PDF"
    assert data.rstrip().endswith(b"%%EOF"), f"{snap.name} is truncated"
    assert bcp._page_count(snap) == latest["pages"]


def test_archive_in_sync_with_layouts():
    """Newest snapshot's fingerprint must equal the current resolved geometry."""
    fingerprint, _ = bcp._layout_fingerprint()
    manifest = bcp._load_manifest()
    assert manifest[-1]["layout_hash"] == fingerprint, (
        "layouts changed without a new snapshot — run "
        "`python scripts/build_combined_pdf.py` and commit the dated PDF + manifest + INDEX"
    )


def test_index_in_sync_with_manifest():
    manifest = bcp._load_manifest()
    committed = bcp.INDEX.read_text(encoding="utf-8")
    assert committed == bcp._render_index(manifest), (
        "INDEX.md is stale — run `python scripts/build_combined_pdf.py`"
    )


def test_emit_is_deterministic():
    _, decks = bcp._layout_fingerprint()
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.pdf", Path(td) / "b.pdf"
        bcp.emit_combined_pdf(decks, a)
        bcp.emit_combined_pdf(decks, b)
        assert a.read_bytes() == b.read_bytes()
