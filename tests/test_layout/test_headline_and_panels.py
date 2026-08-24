"""Tests for the theme `headline` colour role, two-panel `accent_side`, and the
un-bolded code title — all from the Claude Code deck feedback round (FB-091/096/102).
"""
from __future__ import annotations

from slidekit.ir.parse import loads
from slidekit.layout import resolve

BASE = """
version: 1
theme:
  palette:
    primary: "#19323C"
    surface: "#FFFFFF"
    accent: "#CC785C"
    text: "#1A1A2E"
    muted: "#8A8A9A"
{headline}
slides:
{slides}
"""


def _resolve(headline="", slides=""):
    return (lambda d: (d, resolve(d)))(loads(BASE.format(headline=headline, slides=slides)))


def _titles(rs):
    return [n for n in rs.nodes if n.node_id.startswith(("title", "sec_title"))]


# ── headline role (FB-091) ─────────────────────────────────────────────────────

def test_headline_role_colours_every_title():
    slides = (
        "  - component: bullet-list\n    title: T1\n    items: [a, b]\n"
        "  - component: this-vs-that\n    title: T2\n    left: {value: X, label: x}\n    right: {value: Y, label: y}\n"
        "  - component: section-divider\n    number: '01'\n    title: T3\n"
        "  - component: table-slide\n    title: T4\n    headers: [A, B]\n    rows: [[A, B]]\n"
    )
    deck, rd = _resolve(headline="  headline: accent\n", slides=slides)
    acc = deck.theme.palette.accent
    seen = 0
    for rs in rd.slides:
        for t in _titles(rs):
            assert t.text_color == acc, (rs.component, t.node_id, t.text_color)
            seen += 1
    assert seen >= 4


def test_headline_unset_keeps_default_title_colour():
    """Without a headline role, titles keep their prior colour (primary for
    _slide_title-based layouts, default for bullet lists) — no silent change."""
    slides = "  - component: table-slide\n    title: T\n    headers: [A, B]\n    rows: [[A, B]]\n"
    deck, rd = _resolve(headline="", slides=slides)
    title = _titles(rd.slides[0])[0]
    assert title.text_color == deck.theme.palette.primary


def test_headline_must_be_a_palette_role():
    import pytest
    with pytest.raises(ValueError, match="palette role"):
        loads(
            "version: 1\ntheme:\n  headline: turquoise\nslides:\n"
            "  - component: title-slide\n    title: X\n"
        )


# ── two-panel accent_side (FB-096) ─────────────────────────────────────────────

_PANEL = (
    "  - component: two-panel-list\n    title: T\n{acc}"
    "    left: {{title: L, items: [a]}}\n    right: {{title: R, items: [b]}}\n"
)


def _panel_head_colours(rs):
    lp = next(n.text_color for n in rs.nodes if n.node_id.startswith("lp_head") and n.node_type == "text")
    rp = next(n.text_color for n in rs.nodes if n.node_id.startswith("rp_head") and n.node_type == "text")
    return lp, rp


def test_accent_side_right_makes_right_accent():
    deck, rd = _resolve(slides=_PANEL.format(acc="    accent_side: right\n"))
    lp, rp = _panel_head_colours(rd.slides[0])
    assert rp == deck.theme.palette.accent
    assert lp == deck.theme.palette.muted


def test_accent_side_left_makes_left_accent():
    deck, rd = _resolve(slides=_PANEL.format(acc="    accent_side: left\n"))
    lp, rp = _panel_head_colours(rd.slides[0])
    assert lp == deck.theme.palette.accent
    assert rp == deck.theme.palette.muted


def test_accent_side_default_is_primary_left_muted_right():
    deck, rd = _resolve(slides=_PANEL.format(acc=""))
    lp, rp = _panel_head_colours(rd.slides[0])
    assert lp == deck.theme.palette.primary
    assert rp == deck.theme.palette.muted


# ── code title weight (FB-102) ─────────────────────────────────────────────────

def test_code_title_is_not_bold():
    slides = "  - component: code\n    title: My Script\n    code: |\n      x = 1\n"
    _, rd = _resolve(slides=slides)
    title = next(n for n in rd.slides[0].nodes if n.node_id.startswith("code_title"))
    assert title.bold is False
