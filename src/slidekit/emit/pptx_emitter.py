"""PPTX emitter — places every resolved node at its EMU rect.

Auto-fit is disabled (our layout already did the fitting). Word-wrap is enabled
to match the wrap() assumptions. Theme colors are written as literal RGB — no
reliance on the pptx theme part.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.util import Emu, Pt

if TYPE_CHECKING:
    from slidekit.ir.models import Deck
    from slidekit.layout.models import ResolvedDeck, ResolvedNode

from slidekit.metrics.constants import (
    INSET_LEFT_EMU,
    INSET_RIGHT_EMU,
    INSET_TOP_EMU,
    INSET_BOTTOM_EMU,
)

# Map lowercase internal font names → PowerPoint display names.
_PPTX_FONT_NAME: dict[str, str] = {
    "arial": "Arial",
    "calibri": "Calibri",
    "cambria": "Cambria",
    "times new roman": "Times New Roman",
    "courier new": "Courier New",
    "bookman old style": "Bookman Old Style",
    "century schoolbook": "Century Schoolbook",
}

_BLANK_LAYOUT_IDX = 6  # index in default python-pptx template


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Parse #RRGGBB → (r, g, b) integers."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _blank_layout(prs: Presentation):
    """Return the Blank slide layout; fall back to index 0 if not found."""
    for layout in prs.slide_layouts:
        if layout.name == "Blank":
            return layout
    return prs.slide_layouts[_BLANK_LAYOUT_IDX]


def emit_pptx(
    deck: "Deck",
    resolved: "ResolvedDeck",
    output_path: Union[str, Path],
) -> Path:
    """Emit a .pptx file from a fully-resolved deck. Returns the output path."""
    output_path = Path(output_path)

    prs = Presentation()
    canvas_w = resolved.slides[0].canvas_w if resolved.slides else 12192000
    canvas_h = resolved.slides[0].canvas_h if resolved.slides else 6858000
    prs.slide_width = Emu(canvas_w)
    prs.slide_height = Emu(canvas_h)

    layout = _blank_layout(prs)
    palette = deck.theme.palette

    for rs in resolved.slides:
        slide = prs.slides.add_slide(layout)

        # Solid slide background: the slide's own backdrop if set, else the theme surface.
        bg = slide.background
        fill = bg.fill
        fill.solid()
        r, g, b = _hex_to_rgb(rs.background or palette.surface)
        fill.fore_color.rgb = RGBColor(r, g, b)

        for node in rs.nodes + rs.chrome:
            _emit_node(slide, node, palette)

    prs.save(str(output_path))
    return output_path


def _emit_node(slide, node: "ResolvedNode", palette) -> None:
    rect = node.rect
    if node.node_type == "box":
        _emit_box(slide, node, palette)
    elif node.node_type == "ellipse":
        _emit_box(slide, node, palette, shape=MSO_SHAPE.OVAL)
    elif node.node_type == "text":
        _emit_text(slide, node, palette)
    elif node.node_type == "icon":
        _emit_icon(slide, node, palette)
    elif node.node_type == "image":
        _emit_image(slide, node)
    # spacer: no visual output


def _emit_box(slide, node: "ResolvedNode", palette, shape=None) -> None:
    """Emit a filled shape for deterministic designs (funnel, pyramid, swot rules,
    nested circles, etc.) — a rectangle by default, or the MSO shape passed in
    (ellipse nodes pass OVAL). Fill comes from node.fill_color (a literal hex
    resolved from a palette role at layout time); falls back to the theme primary."""
    rect = node.rect
    # A box with a corner_radius becomes a rounded rectangle (e.g. the file-tree
    # panel). The ellipse path passes its own shape and ignores the radius.
    if shape is None and node.corner_radius:
        shape = MSO_SHAPE.ROUNDED_RECTANGLE
    shape = slide.shapes.add_shape(
        shape or MSO_SHAPE.RECTANGLE, Emu(rect.x), Emu(rect.y), Emu(rect.w), Emu(rect.h)
    )
    if node.corner_radius and shape.adjustments:
        # PowerPoint's rounded-rect adjustment is the radius as a fraction of the
        # shorter side (0–0.5).
        short = min(rect.w, rect.h) or 1
        shape.adjustments[0] = min(0.5, node.corner_radius / short)
    hex_color = node.fill_color or palette.primary
    r, g, b = _hex_to_rgb(hex_color)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(r, g, b)
    shape.line.fill.background()  # no border
    shape.shadow.inherit = False


def _emit_text(slide, node: "ResolvedNode", palette) -> None:
    rect = node.rect
    txBox = slide.shapes.add_textbox(
        Emu(rect.x), Emu(rect.y), Emu(rect.w), Emu(rect.h)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = Emu(INSET_LEFT_EMU)
    tf.margin_right = Emu(INSET_RIGHT_EMU)
    tf.margin_top = Emu(INSET_TOP_EMU)
    tf.margin_bottom = Emu(INSET_BOTTOM_EMU)

    # Color precedence: an explicit text_color override (e.g. a label sitting on a
    # dark shape) wins; otherwise chrome/caption use muted and the rest use text.
    if node.text_color:
        hex_color = node.text_color
    elif node.is_chrome or node.is_caption:
        hex_color = palette.muted
    else:
        hex_color = palette.text

    r, g, b = _hex_to_rgb(hex_color)
    font_name = _PPTX_FONT_NAME.get(node.font or "arial", "Arial")
    size_pt = node.size_pt or 32.0

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER if node.align == "center" else PP_ALIGN.LEFT
    run = p.add_run()
    run.text = node.text_content or ""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = node.bold
    run.font.italic = node.italic
    run.font.color.rgb = RGBColor(r, g, b)
    # A hyperlinked text node (e.g. the bottom-right "Source" citation) becomes a
    # clickable run; underline gives the usual link affordance. The node's own
    # text_color is preserved (set above) rather than PowerPoint's default link blue.
    if node.href:
        run.hyperlink.address = node.href
        run.font.underline = True


def _emit_icon(slide, node: "ResolvedNode", palette) -> None:
    """Emit icon as a colored circle inscribed in its slot (Phase 2 spec).

    A circle of diameter min(w, h), centered in the slot and filled with the theme
    accent. Drawn strictly inside the resolved rect so it can never overflow — the
    earlier text-label placeholder rendered an unmeasured ``[name]`` string that
    spilled past the slot in real renderers (caught by the Phase 6 harness).
    """
    rect = node.rect
    diameter = min(rect.w, rect.h)
    cx = rect.x + (rect.w - diameter) // 2
    cy = rect.y + (rect.h - diameter) // 2

    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Emu(cx), Emu(cy), Emu(diameter), Emu(diameter)
    )
    r, g, b = _hex_to_rgb(node.fill_color or palette.accent)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(r, g, b)
    shape.line.fill.background()  # no border
    shape.shadow.inherit = False


def _emit_image(slide, node: "ResolvedNode") -> None:
    """Insert image if path exists; skip silently if not found."""
    if not node.text_content:
        return
    path = Path(node.text_content)
    if not path.exists():
        return
    rect = node.rect
    slide.shapes.add_picture(
        str(path),
        Emu(rect.x), Emu(rect.y), Emu(rect.w), Emu(rect.h),
    )
