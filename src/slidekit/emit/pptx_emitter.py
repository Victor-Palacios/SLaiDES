"""PPTX emitter — places every resolved node at its EMU rect.

Auto-fit is disabled (our layout already did the fitting). Word-wrap is enabled
to match the wrap() assumptions. Theme colors are written as literal RGB — no
reliance on the pptx theme part.

Text in a layout is emitted as a real placeholder, so a slide that picks the
layout up in PowerPoint or Google Slides gets editable text slots rather than a
flat picture; the boxes and icons stay as the design's fixed structure.

Slide layouts: python-pptx's default template ships 11 stock Office layouts, and
we keep them. On top we clone one layout per slidekit component, named after the
design and carrying that design's art, and attach every slide to the layout for
its component. That is what makes the designs show up (and be selectable) under
Google Slides' Slide > Edit theme — previously every slide pointed at "Blank",
so the theme editor listed only the stock Office layouts.

The layout art is decoration for the theme editor only: slides still draw all of
their own content, so slides carry showMasterSp="0" to suppress inherited layout
graphics and keep the rendered slide byte-for-byte what it was before.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.opc.constants import CONTENT_TYPE as CT
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.parts.slide import SlideLayoutPart
from pptx.shapes.shapetree import SlideShapes
from pptx.slide import SlideLayout
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

# Layout ids must be unique and >= 2147483648; the stock 11 occupy ...649-...659.
_LAYOUT_ID_BASE = 2147483700

# Our layouts sit alongside the 11 stock Office ones, so they carry a prefix: it
# groups them together in the theme editor's list and keeps our "Title Slide" from
# colliding with the stock layout of the same name.
_LAYOUT_NAME_PREFIX = "slidekit \u00b7 "

# Component key -> the label Google Slides shows in Edit Theme. Anything not listed
# is title-cased from its key ("stat-callout" -> "Stat Callout").
_LAYOUT_NAME_OVERRIDES: dict[str, str] = {
    "swot": "SWOT",
    "kpi-grid": "KPI Grid",
    "this-vs-that": "This vs That",
    "table-slide": "Table",
    "code": "Code Block",
}

# Slide-number/date/footer placeholder indices in the stock template — a promoted
# text placeholder must not reuse them.
_RESERVED_PH_IDX = {10, 11, 12}

# Node types promoted to placeholders in a layout, so a slide built from the
# design can edit them. Images are excluded: a picture is a <p:pic>, not a shape.
_PROMOTABLE = ("text", "box", "ellipse", "icon")

# Placeholders inherited from the stock Blank layout. slidekit binds no content to
# placeholders and their geometry is sized for the template's 4:3 canvas, so they
# would render as stray boxes in the theme editor. Drop them from our layouts.
_INHERITED_PH_TAGS = ("dt", "ftr", "sldNum")


def _layout_name(component: str) -> str:
    """Human-readable layout label for a component key."""
    override = _LAYOUT_NAME_OVERRIDES.get(component)
    stem = override or " ".join(w.capitalize() for w in component.split("-"))
    return _LAYOUT_NAME_PREFIX + stem


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


class _LayoutCanvas:
    """Adapter that lets the slide-drawing helpers paint into a slide *layout*.

    ``_emit_node`` and friends only need a ``.shapes`` that speaks the SlideShapes
    API. python-pptx's ``LayoutShapes`` is read-only (no ``add_shape``/``add_textbox``),
    so bind a real ``SlideShapes`` to the layout's own spTree instead — that reuses
    every existing draw path rather than growing a second one for layouts.
    """

    def __init__(self, layout: SlideLayout):
        self._layout = layout
        self.shapes = SlideShapes(layout._element.spTree, layout)

    @property
    def part(self):
        return self._layout.part


def _strip_inherited_placeholders(layout_el) -> None:
    """Remove the stock Blank layout's date/footer/slide-number placeholders."""
    for sp in list(layout_el.spTree.iter(qn("p:sp"))):
        ph = sp.find(qn("p:nvSpPr") + "/" + qn("p:nvPr") + "/" + qn("p:ph"))
        if ph is not None and ph.get("type") in _INHERITED_PH_TAGS:
            sp.getparent().remove(sp)


def _promote_to_placeholder(sp, ph_type: str, idx: Optional[int]) -> None:
    """Turn a drawn shape on a layout into a real placeholder.

    A plain shape on a layout is decoration: it renders on any slide using the
    layout, but it cannot be selected there, so its color and size cannot be
    changed. Only placeholders are cloned onto a slide as real, selectable shapes
    — and the clone inherits this shape's geometry, position and fill — which is
    what makes a design usable as a template rather than a picture.
    """
    nvSpPr = sp.find(qn("p:nvSpPr"))
    nvPr = nvSpPr.find(qn("p:nvPr"))

    ph = nvPr.makeelement(qn("p:ph"), {})
    ph.set("type", ph_type)
    if idx is not None:
        ph.set("idx", str(idx))
    nvPr.insert(0, ph)  # p:ph must lead p:nvPr

    # A placeholder is not a free-floating text box; drop the marker so renderers
    # treat it as the placeholder it now is.
    cNvSpPr = nvSpPr.find(qn("p:cNvSpPr"))
    if cNvSpPr is not None:
        cNvSpPr.attrib.pop("txBox", None)

    # python-pptx gives autoshapes a <p:style> pointing at theme accent1. The clone
    # on the slide carries an empty spPr and inherits from here, and that style
    # would win over our literal fill — the design's colors would come out as the
    # stock Office blue. The explicit solidFill stays; the style has to go.
    style = sp.find(qn("p:style"))
    if style is not None:
        sp.remove(style)

    # Note: the empty <p:txBody> is deliberately kept even on shapes that hold no
    # text. Dropping it renders stray glyph marks at the shape edge.


def _placeholder_plan(nodes: list) -> list:
    """Assign a placeholder role to each promotable node, in draw order.

    Exactly one node may be the title (OOXML allows a single title per layout);
    everything else becomes a body placeholder with a unique index.
    """
    title_at = next(
        (
            i
            for i, n in enumerate(nodes)
            if n.node_type == "text" and str(n.node_id).startswith("title")
        ),
        None,
    )

    plan, idx = [], 1
    for i, _node in enumerate(nodes):
        if i == title_at:
            plan.append(("title", None))
            continue
        while idx in _RESERVED_PH_IDX:
            idx += 1
        plan.append(("body", idx))
        idx += 1
    return plan


def _strip_cloned_placeholders(slide) -> None:
    """Drop the empty placeholders add_slide() clones from the layout.

    Now that layouts carry real placeholders, python-pptx copies them onto every
    new slide. Our slides draw all of their own content, so those clones are empty
    strays that would sit on the slide (and can surface as prompt text). The
    placeholders belong to the layout, for slides the user creates from it.
    """
    spTree = slide.shapes._spTree
    for sp in list(spTree.iter(qn("p:sp"))):
        if sp.find(qn("p:nvSpPr") + "/" + qn("p:nvPr") + "/" + qn("p:ph")) is not None:
            sp.getparent().remove(sp)


def _add_layout(prs: Presentation, blank: SlideLayout, name: str, index: int) -> SlideLayout:
    """Clone the Blank layout into a new, named layout part wired to the master.

    python-pptx has no public API for adding a layout, so this assembles the part
    by hand: clone the XML, register it in the package, relate it both ways with
    the master, and append a ``<p:sldLayoutId>``. Content-type overrides are derived
    from the part list at save time, so ``[Content_Types].xml`` needs no edit.
    """
    master_part = prs.slide_masters[0].part

    layout_el = copy.deepcopy(blank._element)
    layout_el.set("type", "blank")
    layout_el.set("preserve", "1")  # keep it even when unused by any slide
    layout_el.cSld.set("name", name)
    _strip_inherited_placeholders(layout_el)

    partname = PackURI("/ppt/slideLayouts/slideLayout%d.xml" % index)
    part = SlideLayoutPart(partname, CT.PML_SLIDE_LAYOUT, prs.part.package, layout_el)
    part.relate_to(master_part, RT.SLIDE_MASTER)
    rId = master_part.relate_to(part, RT.SLIDE_LAYOUT)

    sldLayoutIdLst = master_part._element.find(qn("p:sldLayoutIdLst"))
    entry = sldLayoutIdLst.makeelement(qn("p:sldLayoutId"), {})
    entry.set("id", str(_LAYOUT_ID_BASE + index))
    entry.set(qn("r:id"), rId)
    sldLayoutIdLst.append(entry)

    return SlideLayout(layout_el, part)


def _build_component_layouts(prs: Presentation, deck: "Deck") -> dict:
    """One named, art-carrying layout per slidekit component.

    Returns ``{component: SlideLayout}``. The art comes from resolving a canonical
    prototype slide per component with *this deck's* theme, so the layouts in the
    theme editor match the palette and font of the deck they ship in.
    """
    from slidekit.emit.prototypes import resolved_prototypes

    palette = deck.theme.palette
    blank = _blank_layout(prs)
    first_index = len(prs.slide_layouts) + 1

    layouts: dict = {}
    for offset, rs in enumerate(resolved_prototypes(deck.theme).slides):
        layout = _add_layout(
            prs, blank, _layout_name(rs.component), first_index + offset
        )

        fill = layout.background.fill
        fill.solid()
        r, g, b = _hex_to_rgb(rs.background or palette.surface)
        fill.fore_color.rgb = RGBColor(r, g, b)

        canvas = _LayoutCanvas(layout)
        drawn = []
        for node in rs.nodes + rs.chrome:
            before = len(canvas.shapes._spTree)
            _emit_node(canvas, node, palette)
            # Text, boxes, ellipses and icons all become placeholders, so a slide
            # using this design can retype the copy and recolor/resize the shapes.
            # Pictures are left alone: a <p:pic> is not a shape placeholder.
            if node.node_type in _PROMOTABLE and len(canvas.shapes._spTree) > before:
                drawn.append((node, canvas.shapes._spTree[-1]))

        plan = _placeholder_plan([n for n, _sp in drawn])
        for (_node, sp), (ph_type, idx) in zip(drawn, plan):
            _promote_to_placeholder(sp, ph_type, idx)

        layouts[rs.component] = layout

    return layouts


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
    # The default template is 4:3 and python-pptx leaves the type attribute alone
    # when the size is overridden, so the package claimed "On-screen Show (4:3)"
    # while measuring 16:9. Say what we actually are.
    prs.part._element.sldSz.set("type", "screen16x9")

    component_layouts = _build_component_layouts(prs, deck)
    blank = _blank_layout(prs)
    palette = deck.theme.palette

    for rs in resolved.slides:
        slide = prs.slides.add_slide(component_layouts.get(rs.component, blank))
        # Slides draw all of their own content, so suppress inherited master/layout
        # graphics — the layout art exists for the theme editor, not the slide.
        slide._element.set("showMasterSp", "0")
        _strip_cloned_placeholders(slide)

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
