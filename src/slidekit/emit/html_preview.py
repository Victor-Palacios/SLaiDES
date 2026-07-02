"""HTML debug preview — absolute-positioned divs from resolved geometry.

Purely for human spot-check. Never used by the agent loop.

At 96 DPI: 1 inch = 96 px, 1 EMU = 1/914400 inch, so 1 EMU = 96/914400 px.
A 16:9 slide (12192000 × 6858000 EMU) renders at 1280 × 720 px.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from slidekit.metrics.constants import LINE_SPACING_SINGLE

if TYPE_CHECKING:
    from slidekit.ir.models import Deck
    from slidekit.layout.models import ResolvedDeck, ResolvedNode

_EMU_PER_PX = 914400 / 96  # 9525.0 EMU per pixel at 96 DPI


def _px(emu: int) -> str:
    return f"{emu / _EMU_PER_PX:.2f}px"


def emit_html(
    deck: "Deck",
    resolved: "ResolvedDeck",
    output_path: Union[str, Path],
) -> Path:
    """Emit a single-file HTML debug preview. Returns the output path."""
    output_path = Path(output_path)
    slides_html = "\n".join(_slide_html(rs, deck) for rs in resolved.slides)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>slidekit debug preview</title>
<style>
  body {{ background: #555; margin: 0; padding: 24px; font-family: Arial, sans-serif; }}
  .slide-wrap {{ margin-bottom: 24px; display: inline-block; }}
  .slide-label {{ color: #ccc; font-size: 12px; margin-bottom: 4px; }}
  .slide {{ position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.4); }}
  .node {{ position: absolute; box-sizing: border-box; }}
  .node-text {{ overflow: visible; white-space: pre-wrap; }}
  .node-icon {{ text-align: center; font-weight: bold; border: 2px dashed currentColor;
                display: flex; align-items: center; justify-content: center; font-size: 12px; }}
  .node-image {{ background: #ddd; border: 1px solid #bbb;
                 display: flex; align-items: center; justify-content: center;
                 color: #888; font-size: 12px; }}
  .node-chrome {{ opacity: 0.6; }}
</style>
</head>
<body>
{slides_html}
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _slide_html(rs, deck: "Deck") -> str:
    palette = deck.theme.palette
    surface_color = rs.background or palette.surface

    slide_w_px = rs.canvas_w / _EMU_PER_PX
    slide_h_px = rs.canvas_h / _EMU_PER_PX
    label = f"Slide {rs.slide_index + 1}: {rs.component}"
    if rs.page_number is not None:
        label += f" (page {rs.page_number})"

    nodes_html = "\n".join(
        _node_html(n, palette)
        for n in rs.nodes + rs.chrome
    )

    return f"""<div class="slide-wrap">
  <div class="slide-label">{label}</div>
  <div class="slide" style="width:{slide_w_px:.2f}px;height:{slide_h_px:.2f}px;background:{surface_color}">
{nodes_html}
  </div>
</div>"""


def _node_html(node: "ResolvedNode", palette) -> str:
    rect = node.rect
    left = _px(rect.x)
    top = _px(rect.y)
    width = _px(rect.w)
    height = _px(rect.h)

    chrome_cls = " node-chrome" if node.is_chrome else ""

    if node.node_type == "text":
        if node.is_chrome or node.is_caption:
            color = palette.muted
        else:
            color = palette.text
        font_name = (node.font or "arial").title()
        size_px = (node.size_pt or 32) * 96 / 72  # pt → px at 96 DPI
        weight = "bold" if node.bold else "normal"
        # line-height MUST be pinned to slidekit's own line-spacing so the browser
        # reproduces the box math exactly. Left to the browser default ("normal")
        # it varies by fallback font and overflows the tightly-measured box, which
        # (with clipping) chops descenders off single-line rows (g/p/y). Vertical
        # padding is 0: a resolved text rect is exactly its content height (insets,
        # where present, are already baked into rect.h), so any top/bottom padding on
        # a border-box would steal a line's worth of space and clip. Horizontal inset
        # only.
        style = (
            f"left:{left};top:{top};width:{width};height:{height};"
            f"color:{color};font-family:'{font_name}',Arial;font-size:{size_px:.1f}px;"
            f"line-height:{LINE_SPACING_SINGLE};font-weight:{weight};"
            f"padding:0 9px;"  # horizontal INSET only; vertical baked into rect.h
        )
        text = (node.text_content or "").replace("&", "&amp;").replace("<", "&lt;")
        return (
            f'    <div class="node node-text{chrome_cls}" style="{style}">'
            f'{text}</div>'
        )

    elif node.node_type == "icon":
        color = palette.accent
        style = (
            f"left:{left};top:{top};width:{width};height:{height};color:{color};"
        )
        label = (node.text_content or "icon").replace("&", "&amp;").replace("<", "&lt;")
        return (
            f'    <div class="node node-icon{chrome_cls}" style="{style}">'
            f'[{label}]</div>'
        )

    elif node.node_type == "image":
        style = f"left:{left};top:{top};width:{width};height:{height};"
        path = node.text_content or "image"
        return (
            f'    <div class="node node-image{chrome_cls}" style="{style}">'
            f'[img: {path}]</div>'
        )

    return ""
