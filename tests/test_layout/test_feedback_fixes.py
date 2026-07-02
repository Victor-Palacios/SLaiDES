"""Geometry assertions codifying the 2026-07-02 operator feedback round (FB-018..FB-025).

Goldens pin the exact output; these tests pin the *intent*, so a future refactor can't
silently regress the property the operator asked for while still updating the goldens.
"""
from pathlib import Path

from slidekit.ir import load
from slidekit.layout import resolve
from slidekit.layout.engine import _BIG_NUMBER_VALUE_SCALE
from slidekit.metrics.constants import EMU_PER_INCH

ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES = ROOT / "examples"


def _slide(name: str):
    deck = load(EXAMPLES / f"{name}.yaml")
    return deck, resolve(deck).slides[0]


def _by_prefix(slide, prefix):
    return [n for n in slide.nodes if n.node_id.startswith(prefix)]


# ── FB-018: title-slide title block is left-aligned + vertically centred ──────────


def test_title_slide_block_vertically_centred():
    _, s = _slide("01_title_slide")
    title = _by_prefix(s, "title")[0]
    block = [n for n in s.nodes]
    top = min(n.rect.y for n in block)
    bottom = max(n.rect.bottom() for n in block)
    mid = (top + bottom) / 2
    # centred on the canvas midline (within half a line of rounding slack)
    assert abs(mid - s.canvas_h / 2) < 0.35 * EMU_PER_INCH
    assert title.align is None  # horizontally LEFT-aligned (the "left" in left-center)


# ── FB-019: big-number dominates and everything is centred ───────────────────────


def test_big_number_value_scale_and_centering():
    deck, s = _slide("14_big_number")
    value = _by_prefix(s, "value")[0]
    assert value.size_pt == deck.theme.type_scale.title * _BIG_NUMBER_VALUE_SCALE
    assert _BIG_NUMBER_VALUE_SCALE >= 1.5  # operator: "double or 1.5 bigger"
    texts = [n for n in s.nodes if n.node_type == "text"]
    assert texts and all(n.align == "center" for n in texts)
    rules = [n for n in s.nodes if n.node_type == "box"]
    assert len(rules) == 1  # the centred accent rule (non-text media)
    rule = rules[0]
    rule_mid = rule.rect.x + rule.rect.w / 2
    value_mid = value.rect.x + value.rect.w / 2
    assert abs(rule_mid - value_mid) <= 1000  # EMU rounding slack


# ── FB-023: this-vs-that badge proportions and placement ─────────────────────────


def test_vs_badge_proportions_and_centering():
    _, s = _slide("25_this_vs_that")
    badge = next(n for n in s.nodes if n.node_type == "box")
    vs = next(n for n in s.nodes if n.text_content == "VS")
    assert badge.rect.w == badge.rect.h == int(0.75 * EMU_PER_INCH)
    # the VS glyphs are centred inside the badge on both axes
    assert vs.align == "center"
    assert vs.rect.x == badge.rect.x and vs.rect.w == badge.rect.w
    vs_mid = vs.rect.y + vs.rect.h / 2
    badge_mid = badge.rect.y + badge.rect.h / 2
    assert abs(vs_mid - badge_mid) <= 1000
    # badge centred on the value+label block, not the value line alone
    values = _by_prefix(s, "vs_value")
    labels = _by_prefix(s, "vs_label")
    block_top = min(n.rect.y for n in values)
    block_bottom = max(n.rect.bottom() for n in labels)
    assert abs(badge_mid - (block_top + block_bottom) / 2) <= 2000


# ── FB-024: kpi-grid tiles are compact and centred ───────────────────────────────


def test_kpi_grid_tiles_are_tight_and_centred():
    _, s = _slide("26_kpi_grid")
    inner = int(0.12 * EMU_PER_INCH)
    values = _by_prefix(s, "kpi_val")
    rules = _by_prefix(s, "kpi_rule")
    labels = _by_prefix(s, "kpi_label")
    assert len(values) == len(rules) == len(labels) == 6
    for v, r, l in zip(values, rules, labels):
        assert r.rect.y - v.rect.bottom() == inner   # tight intra-tile gaps
        assert l.rect.y - r.rect.bottom() == inner
        # rule centred under the value column
        v_mid = v.rect.x + v.rect.w / 2
        r_mid = r.rect.x + r.rect.w / 2
        assert abs(v_mid - r_mid) <= 1000
        assert v.align == "center" and l.align == "center"
