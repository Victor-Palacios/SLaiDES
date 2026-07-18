"""Resolved layout models — every node has an absolute EMU rect.

These are the outputs of the layout engine. Serializable to JSON
so agents and tests can inspect geometry without rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from slidekit.metrics.measure import Line


@dataclass
class Rect:
    """Absolute position and size in EMU."""

    x: int
    y: int
    w: int
    h: int

    def right(self) -> int:
        return self.x + self.w

    def bottom(self) -> int:
        return self.y + self.h

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    def intersects(self, other: "Rect") -> bool:
        """True if two rects overlap (share interior area)."""
        return (
            self.x < other.right()
            and other.x < self.right()
            and self.y < other.bottom()
            and other.y < self.bottom()
        )


@dataclass
class ResolvedNode:
    """A single layout node with its resolved absolute rect."""

    node_id: str
    node_type: str
    rect: Rect
    lines: list[Line] = field(default_factory=list)
    children: list["ResolvedNode"] = field(default_factory=list)
    font: Optional[str] = None
    size_pt: Optional[float] = None
    bold: bool = False
    italic: bool = False
    text_content: Optional[str] = None
    is_chrome: bool = False
    is_caption: bool = False
    group_id: Optional[str] = None
    component: Optional[str] = None
    slot_type: Optional[str] = None
    # box nodes carry a literal fill color (resolved from a palette role at layout
    # time); text nodes may override their default color with text_color.
    fill_color: Optional[str] = None
    text_color: Optional[str] = None
    # Horizontal paragraph alignment inside the rect: None (= left) or "center".
    # The rect stays the geometry contract; align only affects glyph placement
    # within it, identically in every emitter.
    align: Optional[str] = None
    # Box nodes only: corner radius in EMU for a rounded rectangle (e.g. the
    # file-tree panel). None = square corners. Purely cosmetic — the rect is
    # still the geometry contract, so lint/measurement are unaffected.
    corner_radius: Optional[int] = None

    def to_dict(self) -> dict:
        d: dict = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "rect": self.rect.to_dict(),
        }
        if self.text_content is not None:
            d["text_content"] = self.text_content
        if self.lines:
            d["lines"] = [
                {
                    "text": ln.text,
                    "width_emu": ln.width_emu,
                    "height_emu": ln.height_emu,
                    "overflows": ln.overflows,
                }
                for ln in self.lines
            ]
        if self.font:
            d["font"] = self.font
            d["size_pt"] = self.size_pt
            d["bold"] = self.bold
            d["italic"] = self.italic
        if self.is_chrome:
            d["is_chrome"] = True
        if self.is_caption:
            d["is_caption"] = True
        if self.group_id:
            d["group_id"] = self.group_id
        if self.component:
            d["component"] = self.component
        if self.slot_type:
            d["slot_type"] = self.slot_type
        if self.fill_color:
            d["fill_color"] = self.fill_color
        if self.text_color:
            d["text_color"] = self.text_color
        if self.align:
            d["align"] = self.align
        if self.corner_radius:
            d["corner_radius"] = self.corner_radius
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


@dataclass
class ResolvedSlide:
    """A fully resolved slide with all node rects in absolute EMU."""

    slide_index: int
    page_number: Optional[int]
    component: str
    canvas_w: int
    canvas_h: int
    nodes: list[ResolvedNode] = field(default_factory=list)
    chrome: list[ResolvedNode] = field(default_factory=list)
    # First-class slide backdrop (hex). None = use the deck surface colour. Painted by the
    # emitter across the whole canvas before any content — a true background, so it is NOT a
    # content node and is exempt from margin/overlap rules by design (e.g. the code layout).
    background: Optional[str] = None

    def all_nodes(self) -> list[ResolvedNode]:
        """Flat list of all nodes including chrome."""
        return self.nodes + self.chrome

    def to_dict(self) -> dict:
        d = {
            "slide_index": self.slide_index,
            "page_number": self.page_number,
            "component": self.component,
            "canvas_w": self.canvas_w,
            "canvas_h": self.canvas_h,
            "nodes": [n.to_dict() for n in self.nodes],
            "chrome": [c.to_dict() for c in self.chrome],
        }
        if self.background is not None:
            d["background"] = self.background
        return d


@dataclass
class ResolvedDeck:
    """Fully resolved deck — every node annotated with absolute EMU rect."""

    slides: list[ResolvedSlide] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"slides": [s.to_dict() for s in self.slides]}

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent)
