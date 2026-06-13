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

        # Solid slide background from theme surface color.
        bg = slide.background
        fill = bg.fill
        fill.solid()
        r, g, b = _hex_to_rgb(palette.surface)
        fill.fore_color.rgb = RGBColor(r, g, b)

        for node in rs.nodes + rs.chrome:
            _emit_node(slide, node, palette)

    prs.save(str(output_path))
    return output_path


def _emit_node(slide, node: "ResolvedNode", palette) -> None:
    rect = node.rect
    if node.node_type == "text":
        _emit_text(slide, node, palette)
    elif node.node_type == "icon":
        _emit_icon(slide, node, palette)
    elif node.node_type == "image":
        _emit_image(slide, node)
    # spacer: no visual output


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

    # Color: chrome and caption-tier nodes use muted; everything else uses text.
    if node.is_chrome or node.is_caption:
        hex_color = palette.muted
    else:
        hex_color = palette.text

    r, g, b = _hex_to_rgb(hex_color)
    font_name = _PPTX_FONT_NAME.get(node.font or "arial", "Arial")
    size_pt = node.size_pt or 32.0

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = node.text_content or ""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = node.bold
    run.font.italic = node.italic
    run.font.color.rgb = RGBColor(r, g, b)


def _emit_icon(slide, node: "ResolvedNode", palette) -> None:
    """Emit icon as a text box placeholder (icon name as label)."""
    rect = node.rect
    txBox = slide.shapes.add_textbox(
        Emu(rect.x), Emu(rect.y), Emu(rect.w), Emu(rect.h)
    )
    tf = txBox.text_frame
    tf.word_wrap = False
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    r, g, b = _hex_to_rgb(palette.accent)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = f"[{node.text_content or 'icon'}]"
    run.font.name = "Arial"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(r, g, b)


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
