#!/usr/bin/env python3
"""Build the combined example review PDF: every examples/*.yaml deck → one PDF.

The per-deck PDFs in `examples/pdf/<name>.pdf` remain the canonical, source-
traceable artifacts (one file per deck, built by `slidekit build --pdf`). This
script adds a single *review* aggregate — `examples/pdf/combined/all-examples.pdf`
— so the whole library can be opened at once, WITHOUT deleting the singletons.

Determinism: decks are processed in sorted filename order and the PDF is written
in reportlab `invariant` mode (fixed timestamp + document id), so re-running on an
unchanged tree yields a byte-stable file — the same spirit as the layout goldens
and the board renderer. The filename is stable (no timestamp), so regeneration
overwrites in place rather than orphaning a dated blob.

Usage:
  python scripts/build_combined_pdf.py            # (re)write the combined PDF
  python scripts/build_combined_pdf.py --check     # verify it is present & in sync
"""
import re
import sys
from pathlib import Path

from slidekit.emit.pdf_emitter import emit_combined_pdf
from slidekit.ir import load
from slidekit.layout import resolve

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
OUT = ROOT / "examples" / "pdf" / "combined" / "all-examples.pdf"

_COUNT_RE = re.compile(rb"/Count\s+(\d+)")


def _decks():
    """(name, deck, resolved) for every example deck, in sorted filename order."""
    for yaml_path in sorted(EXAMPLES_DIR.glob("*.yaml")):
        deck = load(yaml_path)
        yield yaml_path.stem, deck, resolve(deck)


def _expected_pages() -> int:
    return sum(len(rd.slides) for _, _, rd in _decks())


def _committed_page_count() -> int | None:
    """Page-tree /Count from the committed combined PDF, or None if unreadable.

    Read from raw bytes because no PDF *reader* library imports in this
    environment; the page tree's /Count is the largest /Count in the file.
    """
    if not OUT.exists():
        return None
    data = OUT.read_bytes()
    counts = [int(m.group(1)) for m in _COUNT_RE.finditer(data)]
    return max(counts) if counts else None


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    expected = _expected_pages()

    if check_only:
        if not OUT.exists():
            print(f"{OUT.relative_to(ROOT)} is missing — run "
                  "`python scripts/build_combined_pdf.py`", file=sys.stderr)
            return 1
        data = OUT.read_bytes()
        if not (data.startswith(b"%PDF") and data.rstrip().endswith(b"%%EOF")):
            print(f"{OUT.relative_to(ROOT)} is not a well-formed PDF", file=sys.stderr)
            return 1
        actual = _committed_page_count()
        if actual != expected:
            print(
                f"{OUT.relative_to(ROOT)} is stale: has {actual} pages, examples now "
                f"total {expected} slides — run `python scripts/build_combined_pdf.py`",
                file=sys.stderr,
            )
            return 1
        print(f"combined PDF present and in sync ({expected} pages).")
        return 0

    pages = emit_combined_pdf(((d, rd) for _, d, rd in _decks()), OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({pages} pages from "
          f"{len(list(EXAMPLES_DIR.glob('*.yaml')))} decks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
