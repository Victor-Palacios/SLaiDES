"""Native PDF emitter — draws the resolved geometry directly with reportlab.

Mirrors the pptx emitter (same node → visual mapping: surface background, filled
boxes, icon circles, and text drawn from slidekit's own pre-wrapped line boxes),
so a PDF is produced deterministically with NO LibreOffice/headless renderer.
Origin note: slidekit geometry is top-left in EMU; PDF is bottom-left in points
(1 pt = 12700 EMU).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from reportlab.pdfgen import canvas as _canvas

if TYPE_CHECKING:
    from slidekit.ir.models import Deck
    from slidekit.layout.models import ResolvedDeck, ResolvedNode

from slidekit.metrics.constants import INSET_LEFT_EMU, INSET_TOP_EMU

_EMU_PER_PT = 12700.0


def _pt(emu: float) -> float:
    return emu / _EMU_PER_PT


def _rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255


def _pdf_font(name: str | None, bold: bool, italic: bool) -> str:
    n = (name or "arial").lower()
    if n == "courier new":
        base, b, i, bi = "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique"
    elif n in ("times new roman", "cambria", "bookman old style", "century schoolbook"):
        base, b, i, bi = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
    else:  # arial / calibri → Helvetica
        base, b, i, bi = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"
    if bold and italic:
        return bi
    if bold:
        return b
    if italic:
        return i
    return base


def _draw_slide(c, rs, palette, page_w: float, page_h: float) -> None:
    """Paint one resolved slide onto the canvas: background fill, then every node."""
    c.setFillColorRGB(*_rgb(getattr(rs, "background", None) or palette.surface))
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
    for node in rs.nodes + rs.chrome:
        _draw_node(c, node, palette, page_h)


def emit_pdf(deck: "Deck", resolved: "ResolvedDeck", output_path: Union[str, Path]) -> Path:
    """Emit a PDF from a fully-resolved deck (one page per slide). Returns the path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    palette = deck.theme.palette

    cw = resolved.slides[0].canvas_w if resolved.slides else 12192000
    ch = resolved.slides[0].canvas_h if resolved.slides else 6858000
    page_w, page_h = _pt(cw), _pt(ch)

    c = _canvas.Canvas(str(output_path), pagesize=(page_w, page_h))
    for rs in resolved.slides:
        _draw_slide(c, rs, palette, page_w, page_h)
        c.showPage()
    c.save()
    return output_path


def emit_combined_pdf(decks_resolved, output_path: Union[str, Path]) -> int:
    """Emit ONE PDF aggregating many decks — a single review artifact.

    `decks_resolved` is an iterable of `(deck, ResolvedDeck)` pairs, drawn in the
    order given. Each slide is painted with ITS OWN deck's palette and canvas size
    (palette is deck-wide and not stored on a resolved slide), reusing the exact
    same drawing path as `emit_pdf`, so a page here is identical to that deck's own
    per-deck PDF. Built in reportlab `invariant` mode (fixed timestamp + document
    id) so the output is byte-deterministic and can be regenerated/guarded.

    Returns the total page count written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = _canvas.Canvas(str(output_path), invariant=True)
    pages = 0
    for deck, resolved in decks_resolved:
        palette = deck.theme.palette
        for rs in resolved.slides:
            page_w, page_h = _pt(rs.canvas_w), _pt(rs.canvas_h)
            c.setPageSize((page_w, page_h))
            _draw_slide(c, rs, palette, page_w, page_h)
            c.showPage()
            pages += 1
    c.save()
    return pages


def _draw_node(c, node: "ResolvedNode", palette, page_h: float) -> None:
    rect = node.rect
    x, w, h = _pt(rect.x), _pt(rect.w), _pt(rect.h)
    # Top edge of the rect in PDF (bottom-left origin) coordinates.
    top = page_h - _pt(rect.y)

    if node.node_type == "box":
        c.setFillColorRGB(*_rgb(node.fill_color or palette.primary))
        if node.corner_radius:
            radius = min(node.corner_radius / _EMU_PER_PT, w / 2, h / 2)
            c.roundRect(x, top - h, w, h, radius, stroke=0, fill=1)
        else:
            c.rect(x, top - h, w, h, stroke=0, fill=1)

    elif node.node_type == "ellipse":
        # Filled ellipse inscribed in the node rect (nested-circles funnel).
        c.setFillColorRGB(*_rgb(node.fill_color or palette.primary))
        c.ellipse(x, top - h, x + w, top, stroke=0, fill=1)

    elif node.node_type == "icon":
        d = min(w, h)
        icx = x + (w - d) / 2
        icy = top - (h + d) / 2  # center y
        c.setFillColorRGB(*_rgb(node.fill_color or palette.accent))
        c.circle(x + w / 2, top - h / 2, d / 2, stroke=0, fill=1)

    elif node.node_type == "image":
        if node.text_content and Path(node.text_content).exists():
            try:
                c.drawImage(node.text_content, x, top - h, w, h, preserveAspectRatio=True, mask="auto")
                return
            except Exception:
                pass
        # placeholder box for a missing/unresolvable image
        c.setFillColorRGB(0.87, 0.87, 0.87)
        c.rect(x, top - h, w, h, stroke=0, fill=1)

    elif node.node_type == "text":
        _draw_text(c, node, palette, page_h)


def _draw_text(c, node: "ResolvedNode", palette, page_h: float) -> None:
    if node.text_color:
        hex_color = node.text_color
    elif node.is_chrome or node.is_caption:
        hex_color = palette.muted
    else:
        hex_color = palette.text
    c.setFillColorRGB(*_rgb(hex_color))

    size = node.size_pt or 32.0
    font = _pdf_font(node.font, node.bold, node.italic)
    c.setFont(font, size)

    x = _pt(node.rect.x) + _pt(INSET_LEFT_EMU)
    top = page_h - _pt(node.rect.y) - _pt(INSET_TOP_EMU)
    centered = node.align == "center"

    lines = node.lines or []
    if not lines:
        # Fallback: single line from text_content.
        if centered:
            c.drawCentredString(_pt(node.rect.x) + _pt(node.rect.w) / 2,
                                top - size * 0.85, node.text_content or "")
        else:
            c.drawString(x, top - size * 0.85, node.text_content or "")
        return

    cur = top
    for ln in lines:
        line_h = _pt(ln.height_emu) if ln.height_emu else size * 1.2
        baseline = cur - size * 0.85  # ascent approximation
        if centered:
            # Center each measured line on the rect midline (insets cancel out).
            c.drawCentredString(_pt(node.rect.x) + _pt(node.rect.w) / 2, baseline, ln.text)
        else:
            c.drawString(x, baseline, ln.text)
        cur -= line_h

    # A hyperlinked text node (e.g. the bottom-right "Source" citation) gets a
    # clickable link rect covering its whole box plus a thin underline for the
    # usual affordance. The text was already drawn above in the node's colour.
    if node.href:
        rx0 = _pt(node.rect.x)
        rx1 = _pt(node.rect.x + node.rect.w)
        ry1 = page_h - _pt(node.rect.y)
        ry0 = page_h - _pt(node.rect.y + node.rect.h)
        c.linkURL(node.href, (rx0, ry0, rx1, ry1), relative=0, thickness=0)
        # Underline just under the first (single) line's baseline.
        ul_y = top - size * 0.95
        c.setLineWidth(0.5)
        c.line(x, ul_y, x + c.stringWidth(node.text_content or "", font, size), ul_y)
