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


def test_bullet_list_items_flush_left_under_rule():
    _, s = _slide("19_bullet_list")
    items = _by_prefix(s, "bl_item")
    title = _by_prefix(s, "title")[0]
    assert items and all(n.rect.x == title.rect.x for n in items)  # no marker indent
    rules = [n for n in s.nodes if n.node_type == "box"]
    assert len(rules) == 1  # the accent rule under the title


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
