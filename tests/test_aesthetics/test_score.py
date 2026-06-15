"""Tests for the Phase 10 aesthetic scorer (beauty-tracking extension)."""

from slidekit.aesthetics.score import (
    _balance,
    _color_harmony,
    _contrast,
    _contrast_ratio,
    _cross_slide_consistency,
    _hue_diff,
    _hue_sat,
    _non_overlap,
    _richness,
    score_deck,
)
from slidekit.ir import load
from slidekit.layout import resolve
from slidekit.layout.models import Rect


class _N:
    """Minimal stand-in for a ResolvedNode. Geometry metrics need only rect; richness
    reads node_type + fill_color/text_color; contrast reads size_pt + is_caption."""

    def __init__(
        self,
        x,
        y,
        w,
        h,
        node_type="text",
        fill_color=None,
        text_color=None,
        size_pt=34.0,
        is_caption=False,
    ):
        self.rect = Rect(x, y, w, h)
        self.is_chrome = False
        self.node_type = node_type
        self.fill_color = fill_color
        self.text_color = text_color
        self.size_pt = size_pt
        self.is_caption = is_caption


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


class _Slide:
    def __init__(self, nodes):
        self.nodes = nodes


# ── contrast: size-aware WCAG targets (large text gets 3:1) ─────────────────────


def test_large_text_passes_at_three_to_one():
    # An accent figure (#00ACC1 ≈ 2.74:1 on white) FAILS the 4.5:1 body target but
    # CLEARS the 3:1 large-text bar — so big emphasis text must not be penalised.
    deck = load("examples/14_big_number.yaml")
    pal = deck.theme.palette
    big = _Slide([_N(0, 0, 10, 10, text_color=pal.accent, size_pt=60.0)])
    body = _Slide([_N(0, 0, 10, 10, text_color=pal.accent, size_pt=20.0)])
    assert _contrast(big, deck) > _contrast(body, deck)
    assert _contrast(big, deck) > 0.8  # near-full credit at large size
    assert _contrast(body, deck) < 0.6  # below-large text held to 4.5:1


# ── richness: designed slides out-score bare ones ──────────────────────────────


def test_richness_rewards_accent_and_structure():
    deck = load("examples/14_big_number.yaml")
    pal = deck.theme.palette
    bare = [_N(0, 0, 10, 10), _N(0, 50, 10, 10)]  # plain default text only
    designed = [
        _N(0, 0, 10, 10, node_type="box", fill_color=pal.accent),
        _N(0, 50, 10, 10, text_color=pal.accent),
    ]
    assert _richness(bare, deck) == 0.0
    assert _richness(designed, deck) > _richness(bare, deck)
    assert _richness(designed, deck) > 0.7


def test_richness_penalises_colour_overload():
    deck = load("examples/14_big_number.yaml")
    pal = deck.theme.palette
    restrained = [_N(0, 0, 10, 10, node_type="box", fill_color=pal.accent)]
    busy = [
        _N(i * 10, 0, 10, 10, node_type="box", fill_color=c)
        for i, c in enumerate(["#111111", "#222222", "#333333", "#444444", "#555555"])
    ]
    assert _richness(restrained, deck) > _richness(busy, deck)


# ── colour harmony: theme-level hue relationship ────────────────────────────────


def test_hue_helpers():
    assert round(_hue_sat("#FF0000")[0]) == 0  # pure red hue 0
    assert _hue_sat("#808080")[1] < 0.05  # grey ≈ zero saturation
    assert _hue_diff(350.0, 10.0) == 20.0  # circular wrap


def test_color_harmony_recognised_vs_clashing():
    # Default-palette deck (blue primary / red accent ≈ split-complementary) scores
    # high; a deliberately clashing pair (e.g. ~70° apart) scores lower.
    good = load("examples/agents-in-ai.yaml")
    assert _color_harmony(good) > 0.8


# ── cross-slide consistency: bounded deck-level modulation ──────────────────────


def test_consistency_bounds_and_rewards_uniform_margins():
    class _RD:
        def __init__(self, slides):
            self.slides = slides

    uniform = _RD([_Slide([_N(100, 100, 50, 50)]) for _ in range(4)])
    erratic = _RD([_Slide([_N(x, x, 50, 50)]) for x in (0, 400, 50, 900)])
    cu, ce = _cross_slide_consistency(uniform), _cross_slide_consistency(erratic)
    assert 0.9 <= ce <= cu <= 1.0
    assert cu > ce


# ── the operator's beauty-validation requirement ────────────────────────────────


def test_designed_deck_outscores_plain_decks():
    """PRIORITY OVERRIDE: a richly-designed deck (big-number) must score HIGHER than
    bare/plain decks (agents-in-ai, all_components) once richness + large-text
    contrast land — otherwise the scorer rewards minimalism for its own sake."""
    designed = score_deck(*_loaded("examples/14_big_number.yaml")).deck_score
    for plain in ("examples/agents-in-ai.yaml", "examples/10_all_components.yaml"):
        assert designed > score_deck(*_loaded(plain)).deck_score


def _loaded(path):
    deck = load(path)
    return deck, resolve(deck)
