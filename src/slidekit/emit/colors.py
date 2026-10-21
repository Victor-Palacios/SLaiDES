"""Which colour each resolved node paints — one source of truth.

The pptx, pdf and html emitters all decide a node's colour the same way, and the
linter's colour-count check (E_COLOR_COUNT) must decide it identically: a check that
models the emitters separately drifts from them, which is how a grey "vs" caption
once shipped past a hand-written colour audit. Everything here is pure and maps a
node plus the palette to a hex string.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from slidekit.ir.models import Palette
    from slidekit.layout.models import ResolvedNode, ResolvedSlide


def text_hex(node: "ResolvedNode", palette: "Palette") -> str:
    """An explicit text_color wins; otherwise chrome and captions are muted and all
    other text is the body ink."""
    if node.text_color:
        return node.text_color
    if node.is_chrome or node.is_caption:
        return palette.muted
    return palette.text


def shape_hex(node: "ResolvedNode", palette: "Palette") -> str:
    """Fill of a box or ellipse: the layout's literal hex, else the theme primary."""
    return node.fill_color or palette.primary


def icon_hex(node: "ResolvedNode", palette: "Palette") -> str:
    """Fill of an icon disc: the layout's literal hex, else the theme accent."""
    return node.fill_color or palette.accent


def background_hex(slide: "ResolvedSlide", palette: "Palette") -> str:
    """The slide's own backdrop if it has one, else the theme surface."""
    return getattr(slide, "background", None) or palette.surface


def slide_colors(slide: "ResolvedSlide", palette: "Palette") -> set[str]:
    """Every distinct colour the slide paints, as upper-case hex.

    Counts the background, every non-chrome text node that draws characters, and
    every non-chrome shape and icon. Excluded on purpose:

    - chrome (the page number and the Source link): the operator ruled that chrome
      does not count as a slide colour;
    - image and chart pixels: a screenshot or photo is content shown as captured,
      not a choice of palette.
    """
    colours = {background_hex(slide, palette).upper()}
    for node in slide.all_nodes():
        if node.is_chrome:
            continue
        kind = node.node_type
        if kind == "text":
            if (node.text_content or "").strip():
                colours.add(text_hex(node, palette).upper())
        elif kind in ("box", "ellipse"):
            colours.add(shape_hex(node, palette).upper())
        elif kind == "icon":
            colours.add(icon_hex(node, palette).upper())
    return colours
