"""Round-trip tests: emit → reopen → assert geometry matches resolved layout.

Positions and sizes must be exact integer EMU values (no floating-point drift).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from slidekit.ir import load
from slidekit.layout import resolve
from slidekit.emit.pptx_emitter import emit_pptx
from slidekit.emit.html_preview import emit_html

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def _text_box_rects(pptx_path: Path, slide_idx: int) -> set[tuple[int, int, int, int]]:
    """Return set of (left, top, width, height) for text-bearing shapes on a slide.

    Placeholders count too: the page number is emitted as a slide-number
    placeholder (so it renumbers), not a plain text box, but it is still a
    resolved text node that must land at its exact rect.
    """
    prs = Presentation(str(pptx_path))
    slide = prs.slides[slide_idx]
    return {
        (s.left, s.top, s.width, s.height)
        for s in slide.shapes
        if s.shape_type in (MSO_SHAPE_TYPE.TEXT_BOX, MSO_SHAPE_TYPE.PLACEHOLDER)
    }


def _expected_text_rects(resolved_slide) -> set[tuple[int, int, int, int]]:
    """Return set of (x, y, w, h) for all text nodes in a resolved slide."""
    all_nodes = resolved_slide.nodes + resolved_slide.chrome
    return {
        (n.rect.x, n.rect.y, n.rect.w, n.rect.h)
        for n in all_nodes
        if n.node_type == "text"
    }


def _assert_text_boxes_cover_nodes(resolved_slide, pptx_path: Path, slide_idx: int):
    """Every resolved text node must map to an emitted box that preserves its anchor.

    The emitter widens single-line boxes so Google Slides (which ignores wrap="none")
    can't re-wrap a box sized to our exact metrics. That means box width — and, for
    centred text, box x — may grow, so byte-exact rect equality is not the invariant.
    The real guarantee is: the emitted box sits on the same baseline (y, height
    identical) and horizontally COVERS the node's original span (left ≤ node.left and
    right ≥ node.right), so the glyphs still land where the layout placed them.
    """
    boxes = _text_box_rects(pptx_path, slide_idx)
    for n in resolved_slide.nodes + resolved_slide.chrome:
        if n.node_type != "text":
            continue
        nx, ny, nw, nh = n.rect.x, n.rect.y, n.rect.w, n.rect.h
        covering = [
            (bx, bw) for (bx, by, bw, bh) in boxes
            if by == ny and bh == nh and bx <= nx and bx + bw >= nx + nw
        ]
        assert covering, (
            f"Slide {slide_idx}: no emitted box covers text node at "
            f"(x={nx}, y={ny}, w={nw}, h={nh}); boxes={sorted(boxes)}"
        )


@pytest.fixture
def tmp_output(tmp_path):
    return tmp_path


class TestRoundTrip:
    def test_slide_count_matches(self, tmp_output):
        deck = load(EXAMPLES_DIR / "01_title_slide.yaml")
        rd = resolve(deck)
        out = emit_pptx(deck, rd, tmp_output / "rt.pptx")
        prs = Presentation(str(out))
        assert len(prs.slides) == len(rd.slides)

    def test_canvas_size_preserved(self, tmp_output):
        deck = load(EXAMPLES_DIR / "01_title_slide.yaml")
        rd = resolve(deck)
        out = emit_pptx(deck, rd, tmp_output / "rt.pptx")
        prs = Presentation(str(out))
        assert prs.slide_width == rd.slides[0].canvas_w
        assert prs.slide_height == rd.slides[0].canvas_h

    def test_text_positions_exact(self, tmp_output):
        """Every text node must map to an emitted box that preserves its anchor
        (same baseline, covering its horizontal span — see the helper's docstring)."""
        deck = load(EXAMPLES_DIR / "01_title_slide.yaml")
        rd = resolve(deck)
        out = emit_pptx(deck, rd, tmp_output / "rt.pptx")

        for i, rs in enumerate(rd.slides):
            _assert_text_boxes_cover_nodes(rs, out, i)

    def test_multi_slide_deck_positions(self, tmp_output):
        """Full deck round-trip: all 10 examples combined are clean."""
        yaml_path = EXAMPLES_DIR / "09_full_deck.yaml"
        deck = load(yaml_path)
        rd = resolve(deck)
        out = emit_pptx(deck, rd, tmp_output / "full.pptx")

        for i, rs in enumerate(rd.slides):
            _assert_text_boxes_cover_nodes(rs, out, i)

    def test_output_file_created(self, tmp_output):
        deck = load(EXAMPLES_DIR / "04_stat_callout.yaml")
        rd = resolve(deck)
        out = emit_pptx(deck, rd, tmp_output / "stat.pptx")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_html_preview_created(self, tmp_output):
        deck = load(EXAMPLES_DIR / "05_comparison_columns.yaml")
        rd = resolve(deck)
        out = emit_html(deck, rd, tmp_output / "preview.html")
        assert out.exists()
        content = out.read_text()
        assert "<!DOCTYPE html>" in content
        assert "node-text" in content

    def test_all_example_decks_emit(self, tmp_output):
        """Smoke test: every example deck emits without error."""
        for yaml_path in sorted(EXAMPLES_DIR.glob("*.yaml")):
            deck = load(yaml_path)
            rd = resolve(deck)
            out = tmp_output / f"{yaml_path.stem}.pptx"
            emit_pptx(deck, rd, out)
            assert out.exists(), f"No pptx for {yaml_path.name}"
