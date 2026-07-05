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


# ── FB-028 (supersedes FB-023): this-vs-that is a bare typographic face-off ──────


def test_vs_is_plain_centred_text_no_box_no_accent():
    _, s = _slide("25_this_vs_that")
    assert not [n for n in s.nodes if n.node_type == "box"]  # no badge, no fills
    vs = next(n for n in s.nodes if n.text_content == "VS")
    assert vs.align == "center" and vs.is_caption
    values = _by_prefix(s, "vs_value")
    labels = _by_prefix(s, "vs_label")
    # all default text colour — no accent/primary on the numbers (operator: "all black")
    assert all(n.text_color is None for n in values + labels)
    # VS centred between the columns on the value+label block midline
    block_top = min(n.rect.y for n in values)
    block_bottom = max(n.rect.bottom() for n in labels)
    vs_mid = vs.rect.y + vs.rect.h / 2
    assert abs(vs_mid - (block_top + block_bottom) / 2) <= 2000
    assert abs((vs.rect.x + vs.rect.w / 2) - s.canvas_w / 2) <= 2000


# ── FB-026: never use bullets — list layouts emit no marker glyphs/boxes ─────────


def test_lists_have_no_bullet_markers():
    for name in ("19_bullet_list", "23_two_panel_list", "36_swot", "32_roadmap"):
        _, s = _slide(name)
        for n in s.nodes:
            if n.node_type == "box":
                # Only rules (wide, thin) and header bands are allowed — never small
                # square markers riding beside list items.
                assert n.rect.w >= 4 * n.rect.h, f"{name}: {n.node_id} looks like a bullet"


def test_bullet_list_items_flush_left_pure_typography():
    _, s = _slide("19_bullet_list")
    items = _by_prefix(s, "bl_item")
    title = _by_prefix(s, "title")[0]
    assert items and all(n.rect.x == title.rect.x for n in items)  # no marker indent
    # FB-030 ("drop the orange, ugly color line"): no rule, no boxes — nothing
    # but the title and the items.
    assert not [n for n in s.nodes if n.node_type != "text"]


# ── FB-027: code is syntax-coloured like a modern IDE (VS Code Dark+) ────────────


def test_code_runs_carry_ide_token_colours():
    from slidekit.layout.engine import (
        _CODE_COMMENT, _CODE_DECL, _CODE_FUNC, _CODE_STRING, _code_line_runs)
    runs = _code_line_runs('def main():')
    assert ("def", _CODE_DECL) == runs[0]
    assert ("main", _CODE_FUNC) in runs
    assert _code_line_runs("# hi") == [("# hi", _CODE_COMMENT)]
    assert ('"Hello, world!"', _CODE_STRING) in _code_line_runs('print("Hello, world!")')

    _, s = _slide("21_code")
    colours = {n.text_color for n in s.nodes if n.node_type == "text"}
    assert {_CODE_COMMENT, _CODE_DECL, _CODE_FUNC, _CODE_STRING} <= colours


def test_code_runs_tile_each_line_exactly():
    """Per-run nodes must reproduce the original line: concatenated run text equals
    the source line, and each run's glyph x-offset equals the measured prefix width."""
    from slidekit.layout.engine import _CODE_FONT
    from slidekit.metrics.measure import measure_text
    deck, s = _slide("21_code")
    size = deck.theme.type_scale.body
    by_y = {}
    for n in s.nodes:
        if n.node_id.startswith("code_run"):
            by_y.setdefault(n.rect.y, []).append(n)
    assert by_y, "no code runs emitted"
    for y, row in by_y.items():
        row.sort(key=lambda n: n.rect.x)
        x0 = row[0].rect.x
        prefix = ""
        for n in row:
            assert n.rect.x == x0 + measure_text(prefix, _CODE_FONT, size)
            prefix += n.text_content
# ── FB-024: kpi-grid tiles are compact and centred ───────────────────────────────


def test_kpi_grid_tiles_are_tight_and_centred():
    from slidekit.layout.engine import _RULE_GAP_EMU
    _, s = _slide("26_kpi_grid")
    inner = _RULE_GAP_EMU
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


# ── 2026-07-04 round (FB-030..FB-042) ─────────────────────────────────────────


def test_code_background_is_the_original_deep_teal():
    """FB-031: token colours stay VS Code Dark+, but the panel returns to the
    original deep-teal background the operator preferred."""
    from slidekit.layout.engine import _CODE_BG
    assert _CODE_BG == "#0C1A1C"
    _, s = _slide("21_code")
    assert s.background == _CODE_BG


def test_vs_text_is_header_tier():
    """FB-032 then FB-043 ("a little bigger" twice): the bare VS lands on the
    header tier (still muted so the numbers dominate)."""
    deck, s = _slide("25_this_vs_that")
    vs = next(n for n in s.nodes if n.text_content == "VS")
    assert vs.size_pt == deck.theme.type_scale.header
    assert vs.is_caption  # muted colour keeps the numbers dominant


def test_table_headers_hug_the_rule():
    """FB-033 + the 2026-07-05 global style rule: headers hug the accent rule."""
    from slidekit.layout.engine import _RULE_GAP_EMU
    _, s = _slide("29_table_slide")
    inner = _RULE_GAP_EMU
    ths = _by_prefix(s, "th")
    rule = next(n for n in s.nodes if n.node_type == "box")
    assert ths and all(rule.rect.y - th.rect.bottom() == inner for th in ths)
    assert rule.group_id == ths[0].group_id  # intentional tight pair (E_GAP-exempt)


def test_metric_comparison_shares_one_vertical_rhythm():
    """FB-034: values/labels/chips align across columns and centre in them."""
    _, s = _slide("30_metric_comparison")
    values = _by_prefix(s, "metric_val")
    labels = _by_prefix(s, "metric_label")
    chips = _by_prefix(s, "metric_chip")
    assert len({n.rect.y for n in values}) == 1  # one value row
    assert len({n.rect.y for n in labels}) == 1  # one label row
    assert len({n.rect.y for n in chips}) == 1   # one chip row
    assert all(n.align == "center" for n in values + labels)
    for chip in chips:  # chips centred under their column
        col = next(v for v in values if v.rect.x <= chip.rect.x < v.rect.right())
        chip_mid = chip.rect.x + chip.rect.w / 2
        col_mid = col.rect.x + col.rect.w / 2
        assert abs(chip_mid - col_mid) <= 1000


def test_process_steps_are_typographic_not_chips():
    """FB-035: large accent numerals + hairline rules — no filled chip badges."""
    deck, s = _slide("31_process_steps")
    nums = _by_prefix(s, "ps_num")
    assert nums and all(n.text_content == f"{i + 1:02d}" for i, n in enumerate(nums))
    assert all(n.size_pt == deck.theme.type_scale.header for n in nums)
    for b in (n for n in s.nodes if n.node_type == "box"):
        assert b.rect.w >= 4 * b.rect.h  # thin rules only, never square chips


def test_roadmap_items_pack_tight():
    """FB-036: items stack at the minimum gap instead of spreading down the lane."""
    _, s = _slide("32_roadmap")
    from slidekit.metrics.constants import GAP_MIN_EMU
    for prefix in ("rm0", "rm1", "rm2"):
        items = _by_prefix(s, f"{prefix}_item")
        assert len(items) >= 2
        for a, b in zip(items, items[1:]):
            assert b.rect.y - a.rect.bottom() == GAP_MIN_EMU


# (the FB-037 matrix-2x2 test was removed with the layout itself — FB-044)


def test_swot_rejects_multiple_items_per_category():
    """FB-038: the IR enforces exactly one statement per quadrant."""
    import pytest
    from slidekit.ir.models import SwotSlide
    SwotSlide(component="swot", strengths=["a"], weaknesses=["b"],
              opportunities=["c"], threats=["d"])
    with pytest.raises(Exception):
        SwotSlide(component="swot", strengths=["a", "extra"], weaknesses=["b"],
                  opportunities=["c"], threats=["d"])


def test_comparison_matrix_highlights_cells_not_categories():
    """FB-039: no coloured category boxes; accent belongs to the ≤2 highlight
    chips (plus the thin header rule)."""
    deck, s = _slide("37_comparison_matrix")
    accent = deck.theme.palette.accent
    boxes = [n for n in s.nodes if n.node_type == "box"]
    rules = [b for b in boxes if b.rect.w >= 4 * b.rect.h]
    chips = _by_prefix(s, "cm_hl")
    assert len(rules) == 1 and len(chips) == 2
    assert len(boxes) == len(rules) + len(chips)  # nothing else is filled
    assert all(b.fill_color == accent for b in boxes)
    heads = _by_prefix(s, "cm_head")
    crits = _by_prefix(s, "cm_crit")
    # category text is plain DEFAULT-colour text — never boxed, never tinted
    # (FB-045: "too many colors — just stick with the red and black")
    assert heads and crits
    assert all(n.node_type == "text" for n in heads + crits)
    assert all(n.text_color is None for n in heads + crits)


# ── 2026-07-05 round 2 (operator chat: deletions, numbered-steps, rule gaps) ──


def test_numbered_steps_are_typographic_not_chips():
    """Reimagined numbered-steps: accent numerals in a left rail, no chip boxes."""
    deck, s = _slide("22_numbered_steps")
    assert not [n for n in s.nodes if n.node_type == "box"]
    nums = _by_prefix(s, "step_num")
    assert nums and all(n.text_content == f"{i + 1:02d}" for i, n in enumerate(nums))
    assert all(n.size_pt == deck.theme.type_scale.header for n in nums)
    assert all(n.text_color == deck.theme.palette.accent for n in nums)


def test_rules_hug_their_text():
    """Operator style rule (2026-07-05): every rule drawn under text sits exactly
    _RULE_GAP_EMU below the text it underlines — 'make the text and line close
    together' — across every layout that draws one."""
    from slidekit.layout.engine import _RULE_GAP_EMU
    for name in ("12_agenda", "14_big_number", "23_two_panel_list", "26_kpi_grid",
                 "29_table_slide", "31_process_steps", "36_swot",
                 "37_comparison_matrix"):
        _, s = _slide(name)
        rules = [n for n in s.nodes if n.node_type == "box" and n.rect.w >= 4 * n.rect.h]
        assert rules, f"{name}: expected at least one rule"
        for r in rules:
            above = [n for n in s.nodes if n.node_type == "text"
                     and n.rect.bottom() <= r.rect.y
                     and n.rect.x < r.rect.right() and r.rect.x < n.rect.right()]
            assert above, f"{name}: rule {r.node_id} has no text above it"
            nearest = max(above, key=lambda n: n.rect.bottom())
            gap = r.rect.y - nearest.rect.bottom()
            assert gap == _RULE_GAP_EMU, f"{name}: {r.node_id} gap {gap} EMU"


def test_nested_circles_nest_and_share_a_bottom_tangent():
    """Operator-requested layout (2026-07-05, from their own job-search slide):
    circles nest strictly (each inside the previous), all tangent at one bottom
    point, fills cycling muted → accent → primary, white text per stage."""
    deck, s = _slide("43_nested_circles")
    circles = [n for n in s.nodes if n.node_type == "ellipse"]
    assert len(circles) == 3
    pal = deck.theme.palette
    assert [c.fill_color for c in circles] == [pal.muted, pal.accent, pal.primary]
    bottoms = {c.rect.bottom() for c in circles}
    assert len(bottoms) == 1  # shared bottom tangent
    centres = {c.rect.x + c.rect.w // 2 for c in circles}
    assert len(centres) == 1  # concentric on the vertical axis
    for outer, inner in zip(circles, circles[1:]):
        assert inner.rect.w < outer.rect.w  # strictly narrowing
        assert inner.rect.x > outer.rect.x and inner.rect.right() < outer.rect.right()
        assert inner.rect.y > outer.rect.y  # fully inside (given shared tangent)
    values = _by_prefix(s, "nc_value")
    labels = _by_prefix(s, "nc_label")
    assert len(values) == len(labels) == 3
    for n in values + labels:
        assert n.align == "center" and n.text_color == pal.surface
    # Operator-calibrated stage sizes (third round, explicit spec:
    # "50pt, 44pts / 42pt, 36pts / 34pt, 28pts").
    from slidekit.metrics.constants import INSET_BOTTOM_EMU, INSET_TOP_EMU
    assert [v.size_pt for v in values] == [50.0, 42.0, 34.0]
    assert [l.size_pt for l in labels] == [44.0, 36.0, 28.0]
    snug = INSET_BOTTOM_EMU + INSET_TOP_EMU
    for v, l in zip(values, labels):
        # label rides INSIDE the emitters' dead-air insets (operator, twice:
        # "too far apart") — boxes overlap by exactly the two insets.
        assert l.rect.y == v.rect.bottom() - snug
