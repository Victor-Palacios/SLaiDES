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

    def all_nodes(self) -> list[ResolvedNode]:
        """Flat list of all nodes including chrome."""
        return self.nodes + self.chrome

    def to_dict(self) -> dict:
        return {
            "slide_index": self.slide_index,
            "page_number": self.page_number,
            "component": self.component,
            "canvas_w": self.canvas_w,
            "canvas_h": self.canvas_h,
            "nodes": [n.to_dict() for n in self.nodes],
            "chrome": [c.to_dict() for c in self.chrome],
        }


@dataclass
class ResolvedDeck:
    """Fully resolved deck — every node annotated with absolute EMU rect."""

    slides: list[ResolvedSlide] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"slides": [s.to_dict() for s in self.slides]}

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent)
