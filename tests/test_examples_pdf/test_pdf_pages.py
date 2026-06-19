"""Guard: every committed per-example PDF matches its deck's slide count.

The standalone `examples/pdf/<stem>.pdf` artifacts are rendered from `examples/<stem>.yaml`
and committed. A byte-level sync test isn't possible (the reportlab emitter is not
byte-deterministic — two fresh renders of the same deck differ in metadata), but the PAGE
COUNT is a stable, meaningful signal: one slide must render to exactly one page. This test
asserts that invariant so a stale PDF (e.g. one left carrying a removed title-slide cover,
2 pages where the YAML now has 1 slide) can't slip through again.

When it fails, re-render the offending decks:
    slidekit build examples/<stem>.yaml --pdf -o examples/pdf/<stem>.pdf
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES = ROOT / "examples"
PDF_DIR = EXAMPLES / "pdf"

# reportlab marks each page object with `/Type /Page` (never `/Pages`); count those.
_PAGE_RE = re.compile(rb"/Type\s*/Page(?![s])")


def _pdf_page_count(path: Path) -> int:
    return len(_PAGE_RE.findall(path.read_bytes()))


def _slide_count(deck_yaml: Path) -> int:
    return len(yaml.safe_load(deck_yaml.read_text(encoding="utf-8")).get("slides", []))


_DECKS = sorted(EXAMPLES.glob("*.yaml"))


@pytest.mark.parametrize("deck", _DECKS, ids=lambda p: p.stem)
def test_example_pdf_page_count_matches_slides(deck):
    pdf = PDF_DIR / f"{deck.stem}.pdf"
    assert pdf.exists(), (
        f"missing {pdf.relative_to(ROOT)} — render it with "
        f"`slidekit build {deck.relative_to(ROOT)} --pdf -o {pdf.relative_to(ROOT)}`"
    )
    slides = _slide_count(deck)
    pages = _pdf_page_count(pdf)
    assert pages == slides, (
        f"{pdf.relative_to(ROOT)} has {pages} page(s) but {deck.name} has {slides} "
        f"slide(s) — the PDF is stale; re-render it with "
        f"`slidekit build {deck.relative_to(ROOT)} --pdf -o {pdf.relative_to(ROOT)}`"
    )


def test_every_example_has_a_pdf():
    """No example deck may lack a committed PDF (catches a deck added without rendering)."""
    missing = [d.stem for d in _DECKS if not (PDF_DIR / f"{d.stem}.pdf").exists()]
    assert not missing, f"examples without a committed PDF: {missing}"
