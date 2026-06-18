"""Guards for the combined example review PDF (examples/pdf/combined/all-examples.pdf).

Mirrors the layout golden-file / board sync pattern: the aggregate is committed and
a test asserts it stays in sync with the example decks, so it can never silently
drift. Page count (== total slides across all example decks) is the sync signal;
byte-identity is intentionally NOT asserted because reportlab output can vary across
library versions even in invariant mode — but invariance IS checked within a run.

No PDF *reader* library imports in this environment (the crypto backend is broken),
so structure is verified from raw bytes, exactly as scripts/build_combined_pdf.py does.
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


def test_combined_pdf_exists_and_valid():
    data = bcp.OUT.read_bytes()
    assert data.startswith(b"%PDF"), "combined PDF missing or not a PDF"
    assert data.rstrip().endswith(b"%%EOF"), "combined PDF is truncated"


def test_combined_pdf_in_sync():
    """Committed page count must equal the total slides across all example decks."""
    assert bcp._committed_page_count() == bcp._expected_pages(), (
        "combined PDF is stale — run `python scripts/build_combined_pdf.py` and commit it"
    )


def test_combined_pdf_is_deterministic():
    """Two fresh builds of the same decks produce byte-identical output."""
    decks = [(d, rd) for _, d, rd in bcp._decks()]
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.pdf", Path(td) / "b.pdf"
        bcp.emit_combined_pdf(decks, a)
        bcp.emit_combined_pdf(decks, b)
        assert a.read_bytes() == b.read_bytes()
