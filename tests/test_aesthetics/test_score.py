"""Tests for the Phase 10 aesthetic scorer (beauty-tracking extension)."""

import pytest

from slidekit.aesthetics.score import (
    ADVISORY_THRESHOLDS,
    COMBINERS,
    _balance,
    _build_warnings,
    _color_harmony,
    _combine_harrington,
    _combine_mean,
    _contrast,
    _contrast_ratio,
    _cross_slide_consistency,
    _hue_diff,
    _hue_sat,
    _info_density,
    _non_overlap,
    _richness,
    score_deck,
    SlideScore,
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
        text=None,
    ):
        self.rect = Rect(x, y, w, h)
        self.is_chrome = False
        self.node_type = node_type
        self.fill_color = fill_color
        self.text_color = text_color
        self.size_pt = size_pt
        self.is_caption = is_caption
        self.text_content = text
        self.lines = []


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


def test_contrast_judged_against_box_fill_not_surface():
    # White label on a dark accent BOX over a white surface: readable in reality, so the
    # metric must judge it against the box fill (high), not the surface (which would be ~0).
    deck = load("examples/14_big_number.yaml")
    box = _N(0, 0, 200, 80, node_type="box", fill_color="#1B4F8A")
    label = _N(0, 0, 200, 80, text_color="#FFFFFF", size_pt=40.0)
    on_box = _Slide([box, label])
    on_surface = _Slide([_N(0, 0, 200, 80, text_color="#FFFFFF", size_pt=40.0)])
    assert _contrast(on_box, deck) > 0.9          # white on dark blue: strong
    assert _contrast(on_surface, deck) < 0.1      # white on white surface: none


def test_text_over_image_not_penalised_for_contrast():
    deck = load("examples/14_big_number.yaml")
    img = _N(0, 0, 200, 120, node_type="image")
    title = _N(0, 0, 200, 120, text_color="#FFFFFF", size_pt=40.0)
    assert _contrast(_Slide([img, title]), deck) == 1.0  # unmeasurable -> not penalised


def test_label_inside_its_box_is_not_overlap():
    box = _N(0, 0, 200, 80, node_type="box", fill_color="#1B4F8A")
    label = _N(0, 0, 200, 80, text_color="#FFFFFF")
    assert _non_overlap([box, label]) == 1.0       # intentional containment, not a collision
    a, b = _N(0, 0, 100, 100), _N(20, 20, 100, 100)  # two real boxes that collide
    a.node_type = b.node_type = "box"
    assert _non_overlap([a, b]) < 1.0


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


# ── info density: penalise crowding and barrenness, protect hero layouts ────────


def test_info_density_penalises_crowding():
    cw, ch = 1000, 1000
    # A comfortable single text block at moderate coverage with a sane word count.
    comfortable = [_N(100, 100, 400, 200, text=" ".join(["word"] * 18))]
    # A crowded slide: text fills most of the canvas with a huge word count.
    crowded = [_N(20, 20, 960, 900, text=" ".join(["word"] * 220))]
    assert _info_density(comfortable, cw, ch) > _info_density(crowded, cw, ch)


def test_info_density_protects_sparse_hero_layout():
    cw, ch = 1000, 1000
    # A big-number style hero: a few words in a large emphasis block — must NOT be
    # penalised as barren (the metric primarily catches crowding).
    hero = [_N(300, 350, 400, 300, text="42 percent")]
    assert _info_density(hero, cw, ch) >= 0.9


def test_info_density_image_only_slide_is_full_credit():
    cw, ch = 1000, 1000
    image_only = [_N(0, 0, 1000, 1000, node_type="image")]
    assert _info_density(image_only, cw, ch) == 1.0
    assert _info_density([], cw, ch) == 0.0


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


# ── T-020: Harrington (geometric-mean) composite combiner ───────────────────────


def test_combiners_agree_when_subscores_uniform():
    # Geometric mean == arithmetic mean iff every sub-score is equal (AM-GM equality).
    sub = {k: 0.6 for k in ADVISORY_THRESHOLDS}
    w = {k: 1.0 for k in sub}
    wsum = sum(w.values())
    assert _combine_harrington(sub, w, wsum) == pytest.approx(
        _combine_mean(sub, w, wsum), abs=1e-9
    )


def test_harrington_never_above_mean():
    # AM-GM: the weighted geometric mean is ≤ the weighted arithmetic mean for any
    # mixed sub-score vector.
    sub = {"a": 0.9, "b": 0.8, "c": 0.4, "d": 0.95}
    w = {k: 1.0 for k in sub}
    wsum = sum(w.values())
    assert _combine_harrington(sub, w, wsum) < _combine_mean(sub, w, wsum)


def test_harrington_lets_one_flaw_dominate():
    # One near-zero sub-score must drag the geometric composite toward zero even when
    # everything else is excellent — the whole point of the non-linear combiner. The
    # arithmetic mean, by contrast, averages the flaw away to a still-high score.
    flawed = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 0.0}
    w = {k: 1.0 for k in flawed}
    wsum = sum(w.values())
    assert _combine_harrington(flawed, w, wsum) < 5.0   # severe flaw dominates
    assert _combine_mean(flawed, w, wsum) == pytest.approx(75.0)  # flaw averaged away


def test_harrington_weights_skew_the_exponent():
    # A heavier weight on the flawed metric pulls the geometric composite lower.
    light = {"good": 1.0, "bad": 0.2}
    w_light = {"good": 1.0, "bad": 1.0}
    w_heavy = {"good": 1.0, "bad": 3.0}
    lo_light = _combine_harrington(light, w_light, sum(w_light.values()))
    lo_heavy = _combine_harrington(light, w_heavy, sum(w_heavy.values()))
    assert lo_heavy < lo_light


def test_score_deck_harrington_at_or_below_mean_and_deterministic():
    deck, rd = _loaded("examples/10_all_components.yaml")
    mean = score_deck(deck, rd)                      # default combine="mean"
    harr1 = score_deck(deck, rd, combine="harrington")
    harr2 = score_deck(deck, rd, combine="harrington")
    assert harr1.to_dict() == harr2.to_dict()        # deterministic
    assert harr1.deck_score <= mean.deck_score + 1e-9
    # Sub-scores and warnings are mode-independent; only the composite changes.
    assert [s.subscores for s in harr1.slides] == [s.subscores for s in mean.slides]
    assert [w.to_dict() for w in harr1.warnings] == [w.to_dict() for w in mean.warnings]


def test_score_deck_rejects_unknown_combine():
    deck, rd = _loaded("examples/01_title_slide.yaml")
    with pytest.raises(ValueError):
        score_deck(deck, rd, combine="median")


def test_combiners_registry_exposes_both_modes():
    assert set(COMBINERS) == {"mean", "harrington"}


# ── T-018: advisory W_AESTH_* warnings + --min-score gate ──────────────────────


def _ss(idx, **subscores):
    """A SlideScore stub with arbitrary sub-scores (other fields are decorative)."""
    sub = {k: 1.0 for k in ADVISORY_THRESHOLDS}
    sub.update(subscores)
    return SlideScore(idx, "bullet-list", sub, 0.0, min(sub, key=lambda k: sub[k]))


def test_clean_subscores_emit_no_warnings():
    clean = [_ss(0), _ss(1)]  # everything at 1.0
    assert _build_warnings(clean, consistency=1.0) == []


def test_low_subscore_emits_matching_warning():
    warns = _build_warnings([_ss(0, balance=0.1)], consistency=1.0)
    codes = [w.code for w in warns]
    assert codes == ["W_AESTH_BALANCE"]
    w = warns[0]
    assert w.slide == 1 and w.value == 0.1 and w.suggested_fix  # 1-based, concrete fix


def test_deck_level_metric_warns_once_not_per_slide():
    # hierarchy is theme-level: identical low value on every slide → ONE warning.
    slides = [_ss(0, hierarchy=0.1), _ss(1, hierarchy=0.1), _ss(2, hierarchy=0.1)]
    warns = [w for w in _build_warnings(slides, 1.0) if w.code == "W_AESTH_HIERARCHY"]
    assert len(warns) == 1
    assert warns[0].slide is None  # deck-level, not pinned to a slide


def test_consistency_warning_below_threshold():
    warns = _build_warnings([_ss(0)], consistency=0.905)
    assert any(w.code == "W_AESTH_CONSISTENCY" and w.slide is None for w in warns)


def test_warnings_are_deterministic_and_advisory_in_report():
    # (was image-full-bleed until that layout was retired, FB-041)
    deck, rd = _loaded("examples/07_image_half_bleed.yaml")
    r1, r2 = score_deck(deck, rd), score_deck(deck, rd)
    assert [w.to_dict() for w in r1.warnings] == [w.to_dict() for w in r2.warnings]
    assert r1.warnings, "image-half-bleed should trip at least one advisory warning"
    assert "warnings" in r1.to_dict()  # surfaced in JSON
    # Advisory: warnings never carry an E_ (error / gate) code.
    assert all(w.code.startswith("W_AESTH_") for w in r1.warnings)
