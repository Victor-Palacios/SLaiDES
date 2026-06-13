"""Text measurement and greedy line breaking.

All widths and heights are in EMU (English Metric Units).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from slidekit.metrics.constants import (
    EMU_PER_INCH,
    EMU_PER_PT,
    INSET_BOTTOM_EMU,
    INSET_LEFT_EMU,
    INSET_RIGHT_EMU,
    INSET_TOP_EMU,
    LINE_SPACING_SINGLE,
    SAFE_FONTS,
    SLACK_WIDTH_FRACTION,
)

DATA_DIR = Path(__file__).parent / "data"


class FontSpec(NamedTuple):
    font: str   # lowercase, e.g. "arial"
    size_pt: float
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class Line:
    text: str
    width_emu: int
    height_emu: int   # line height including line spacing
    overflows: bool = False   # token wider than box that cannot be broken


class TextMeasureError(ValueError):
    pass


# ── metric table loading ───────────────────────────────────────────────────────

@lru_cache(maxsize=64)
def _load_table(font: str, bold: bool, italic: bool) -> dict:
    variant = "bolditalic" if bold and italic else "bold" if bold else "italic" if italic else "regular"
    safe_name = font.replace(" ", "_")
    path = DATA_DIR / f"{safe_name}_{variant}.json"
    if not path.exists():
        raise TextMeasureError(f"No metric table for font '{font}' variant '{variant}' at {path}")
    with open(path) as f:
        return json.load(f)


def _scale(raw_units: int, units_per_em: int, size_pt: float) -> int:
    """Convert design-space units → EMU at given point size."""
    # 1pt = EMU_PER_PT EMU; advance in design units scaled to pt then to EMU.
    return round(raw_units * size_pt * EMU_PER_PT / units_per_em)


# ── public API ─────────────────────────────────────────────────────────────────

def measure_text(text: str, font: str, size_pt: float, bold: bool = False, italic: bool = False) -> int:
    """Return the rendered width of text in EMU including kerning.

    Raises TextMeasureError if the font is not in the metric-safe set.
    """
    font_lower = font.lower()
    if font_lower not in SAFE_FONTS:
        raise TextMeasureError(
            f"Font '{font}' is not in the metric-safe set. "
            f"Allowed: {', '.join(sorted(SAFE_FONTS))}."
        )

    if not text:
        return 0

    table = _load_table(font_lower, bold, italic)
    upm = table["units_per_em"]
    advances: dict[str, int] = table["advances"]
    kerning: dict[str, int] = table["kerning"]

    total = 0
    chars = list(text)
    for i, ch in enumerate(chars):
        cp = str(ord(ch))
        adv = advances.get(cp, 0)
        total += adv

        if i < len(chars) - 1:
            next_cp = str(ord(chars[i + 1]))
            kern_key = f"{cp},{next_cp}"
            total += kerning.get(kern_key, 0)

    return _scale(total, upm, size_pt)


def line_height_emu(font: str, size_pt: float, bold: bool = False, italic: bool = False,
                    line_spacing: float = LINE_SPACING_SINGLE) -> int:
    """Return the line height in EMU for the given font spec."""
    return round(size_pt * line_spacing * EMU_PER_PT)


def wrap(
    text: str,
    font: str,
    size_pt: float,
    box_width_emu: int,
    bold: bool = False,
    italic: bool = False,
    line_spacing: float = LINE_SPACING_SINGLE,
    inset_left: int = INSET_LEFT_EMU,
    inset_right: int = INSET_RIGHT_EMU,
) -> list[Line]:
    """Greedy line breaking matching PowerPoint's behavior.

    Breaks at spaces and hyphens; no hyphenation. Long unbreakable tokens
    that exceed the box width are placed on their own line and flagged with
    Line.overflows = True.

    Returns a list of Line objects; an empty text returns one empty Line.
    """
    font_lower = font.lower()
    if font_lower not in SAFE_FONTS:
        raise TextMeasureError(
            f"Font '{font}' is not in the metric-safe set. "
            f"Allowed: {', '.join(sorted(SAFE_FONTS))}."
        )

    usable_width = box_width_emu - inset_left - inset_right
    lh = line_height_emu(font_lower, size_pt, bold, italic, line_spacing)

    if not text.strip():
        return [Line("", 0, lh)]

    # Tokenize at spaces and after hyphens so break-points are preserved.
    tokens = _tokenize(text)
    lines: list[Line] = []
    current_tokens: list[str] = []
    current_width = 0

    for token in tokens:
        tok_w = measure_text(token, font_lower, size_pt, bold, italic)

        if not current_tokens:
            # Starting a new line.
            stripped = token.lstrip(" ")
            stripped_w = measure_text(stripped, font_lower, size_pt, bold, italic) if stripped else 0
            if stripped_w > usable_width:
                # Single token wider than the box: emit as overflow line.
                lines.append(Line(stripped, stripped_w, lh, overflows=True))
            else:
                current_tokens = [stripped] if stripped else []
                current_width = stripped_w
        else:
            # Try adding token to current line.
            tentative_text = "".join(current_tokens) + token
            tentative_w = current_width + tok_w
            if tentative_w <= usable_width:
                current_tokens.append(token)
                current_width = tentative_w
            else:
                # Flush current line.
                line_text = "".join(current_tokens).rstrip(" ")
                line_w = measure_text(line_text, font_lower, size_pt, bold, italic)
                lines.append(Line(line_text, line_w, lh))

                # Start a new line with this token (strip leading space).
                stripped = token.lstrip(" ")
                stripped_w = measure_text(stripped, font_lower, size_pt, bold, italic) if stripped else 0
                if stripped_w > usable_width:
                    lines.append(Line(stripped, stripped_w, lh, overflows=True))
                    current_tokens = []
                    current_width = 0
                else:
                    current_tokens = [stripped] if stripped else []
                    current_width = stripped_w

    # Flush final line.
    if current_tokens:
        line_text = "".join(current_tokens).rstrip(" ")
        line_w = measure_text(line_text, font_lower, size_pt, bold, italic)
        lines.append(Line(line_text, line_w, lh))

    return lines if lines else [Line("", 0, lh)]


def total_text_height_emu(
    lines: list[Line],
    inset_top: int = INSET_TOP_EMU,
    inset_bottom: int = INSET_BOTTOM_EMU,
) -> int:
    """Total box height needed to contain the given lines including insets."""
    return inset_top + sum(l.height_emu for l in lines) + inset_bottom


# ── internal helpers ───────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Split text into tokens at spaces and after hyphens."""
    tokens: list[str] = []
    current = ""
    for ch in text:
        if ch == " ":
            current += ch
            tokens.append(current)
            current = ""
        elif ch == "-":
            current += ch
            tokens.append(current)
            current = ""
        else:
            current += ch
    if current:
        tokens.append(current)
    return tokens
