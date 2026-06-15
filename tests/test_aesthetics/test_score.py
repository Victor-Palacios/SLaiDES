"""Tests for the Phase 10 aesthetic scorer (first cut)."""

from slidekit.aesthetics.score import (
    _balance,
    _contrast_ratio,
    _non_overlap,
    score_deck,
)
from slidekit.ir import load
from slidekit.layout import resolve
from slidekit.layout.models import Rect


class _N:
    """Minimal stand-in for a ResolvedNode (only rect is needed by geometry metrics)."""

    def __init__(self, x, y, w, h):
        self.rect = Rect(x, y, w, h)
        self.is_chrome = False
        self.node_type = "text"


def test_non_overlap_directional():
    a, b = _N(0, 0, 100, 100), _N(200, 0, 100, 100)  # disjoint
    assert _non_overlap([a, b]) == 1.0
    c = _N(0, 0, 100, 100)
    d = _N(0, 0, 100, 100)  # fully coincident
    assert _non_overlap([c, d]) < 1.0


def test_balance_centered_beats_corner():
    cw, ch = 1000, 1000
    centered = [_N(450, 450, 100, 100)]
    corner = [_N(0, 0, 100, 100)]
    assert _balance(centered, cw, ch) > _balance(corner, cw, ch)
    assert 0.0 <= _balance(corner, cw, ch) <= 1.0


def test_contrast_ratio_black_on_white():
    # Black/white is the maximum contrast ratio (21:1).
    assert round(_contrast_ratio("#000000", "#FFFFFF"), 1) == 21.0
    assert _contrast_ratio("#FFFFFF", "#FFFFFF") == 1.0


def test_score_deck_ranges_and_determinism():
    deck = load("examples/01_title_slide.yaml")
    rd = resolve(deck)
    r1 = score_deck(deck, rd)
    r2 = score_deck(deck, rd)
    assert r1.to_dict() == r2.to_dict()  # deterministic
    assert 0.0 <= r1.deck_score <= 100.0
    for s in r1.slides:
        assert 0.0 <= s.score <= 100.0
        assert all(0.0 <= v <= 1.0 for v in s.subscores.values())
        assert s.weakest in s.subscores
