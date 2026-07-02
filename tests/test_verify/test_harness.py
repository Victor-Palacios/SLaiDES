"""Phase 6 verification-harness tests.

The render-pipeline tests need LibreOffice (``soffice``) + ``pdftoppm`` and are
skipped when those tools are absent (e.g. a dev box without LibreOffice). The pure
unit tests run everywhere.

This harness is the CI drift detector, NOT part of deck generation — see
``slidekit.verify``.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path

import pytest

from slidekit.ir import load
from slidekit.layout import resolve
from slidekit.emit.pptx_emitter import emit_pptx
from slidekit.verify.harness import (
    VerifyConfig,
    _collect_rects,
    _hex_to_rgb,
    check_slide,
    render_pptx_to_pngs,
    tools_available,
    verify_deck_yaml,
)

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
ALL_EXAMPLES = sorted(EXAMPLES_DIR.glob("*.yaml"))

_TOOLS_OK, _TOOLS_REASON = tools_available()
requires_render = pytest.mark.skipif(
    not _TOOLS_OK, reason=f"render tools unavailable ({_TOOLS_REASON})"
)


# --- pure unit tests (always run) -------------------------------------------

def test_hex_to_rgb():
    assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert _hex_to_rgb("000000") == (0, 0, 0)
    assert _hex_to_rgb("#1B4F8A") == (27, 79, 138)


def test_collect_rects_recurses():
    deck = load(EXAMPLES_DIR / "09_full_deck.yaml")
    rd = resolve(deck)
    slide = rd.slides[0]
    flat = _collect_rects(slide.nodes)
    # at least one rect per top-level node, more once children are flattened
    assert len(flat) >= len(slide.nodes)
    assert all(hasattr(r, "x") and hasattr(r, "w") for r in flat)


def test_tools_available_shape():
    ok, reason = tools_available()
    assert isinstance(ok, bool)
    assert isinstance(reason, str)
    assert ok == (reason == "")


# --- render-pipeline tests (skipped without soffice/pdftoppm) ---------------

@requires_render
@pytest.mark.parametrize("deck_path", ALL_EXAMPLES, ids=lambda p: p.stem)
def test_example_deck_passes_harness(deck_path):
    """ACCEPTANCE: every example deck renders clean under the pixel heuristics.

    A clean (lint-passing) deck must not trip the drift detector.
    """
    result = verify_deck_yaml(deck_path)
    assert result.error is None, f"{deck_path.name}: {result.error}"
    failing = [s for s in result.slides if not s.passed]
    assert result.passed, (
        f"{deck_path.name} failed harness: "
        + "; ".join(f"slide {s.slide_index}: {s.failures}" for s in failing)
    )


@requires_render
def test_harness_detects_overflow(tmp_path):
    """Sensitivity check: the harness must FAIL when geometry doesn't match pixels.

    Render a real deck, then check the rendered slide against artificially shrunk
    geometry (rects at 30% size). The rendered ink now lies far outside the claimed
    rects, so the stray-ink heuristic must fire. Proves the heuristic discriminates
    rather than trivially passing.
    """
    deck = load(EXAMPLES_DIR / "05_comparison_columns.yaml")
    rd = resolve(deck)
    pptx = emit_pptx(deck, rd, tmp_path / "rt.pptx")
    pngs = render_pptx_to_pngs(pptx, tmp_path, dpi=VerifyConfig().dpi)
    surface = _hex_to_rgb(deck.theme.palette.surface)

    rs = rd.slides[0]
    png = pngs[0]

    # baseline: true geometry passes
    good = check_slide(png, rs, surface, VerifyConfig())
    assert good.passed, f"true geometry should pass: {good.failures}"

    # shrink every rect toward the origin to 30% size — pixels now fall outside
    shrunk = _shrink_slide(rs, 0.3)
    bad = check_slide(png, shrunk, surface, VerifyConfig())
    assert not bad.passed, "shrunk geometry should be flagged by the harness"
    assert any("ink_outside_rects" in f for f in bad.failures)


def _shrink_slide(rs, factor: float):
    """Deep-copy a ResolvedSlide with every rect scaled to ``factor`` of its size."""
    clone = copy.deepcopy(rs)

    def shrink(nodes):
        for n in nodes:
            n.rect = replace(
                n.rect,
                w=max(1, int(n.rect.w * factor)),
                h=max(1, int(n.rect.h * factor)),
            )
            if n.children:
                shrink(n.children)

    shrink(clone.nodes)
    shrink(clone.chrome)
    return clone
