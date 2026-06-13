"""One-time metric extraction via fonttools.

Run:  python -m slidekit.metrics.extract
Writes JSON tables to slidekit/metrics/data/<font>_<variant>.json

This script is throwaway calibration tooling — it is NOT part of the build
loop. The JSON files it produces are vendored and committed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont

from slidekit.metrics.constants import FONT_FILE_MAP

DATA_DIR = Path(__file__).parent / "data"


def _variant_key(bold: bool, italic: bool) -> str:
    if bold and italic:
        return "bolditalic"
    if bold:
        return "bold"
    if italic:
        return "italic"
    return "regular"


def extract_font_metrics(ttf_path: str, font_name: str, variant: str) -> dict[str, Any]:
    """Extract glyph advances, kerning, and vertical metrics from a TTF."""
    font = TTFont(ttf_path)

    # Horizontal metrics.
    hmtx = font["hmtx"].metrics            # {glyph_name: (advance, lsb)}
    units_per_em = font["head"].unitsPerEm

    # Build cmap: unicode codepoint → glyph name.
    cmap = font.getBestCmap()              # {int codepoint: glyph_name}

    # Per-glyph advance widths keyed by unicode codepoint.
    advances: dict[str, int] = {}
    for cp, glyph_name in (cmap or {}).items():
        if glyph_name in hmtx:
            advance, _ = hmtx[glyph_name]
            advances[str(cp)] = advance

    # Kerning pairs (GPOS or kern table).
    kerning: dict[str, int] = {}
    if "kern" in font:
        for table in font["kern"].kernTables:
            for (left_glyph, right_glyph), value in table.kernTable.items():
                # Only include pairs where both glyphs have codepoints.
                left_cp = _glyph_to_cp(cmap, left_glyph)
                right_cp = _glyph_to_cp(cmap, right_glyph)
                if left_cp is not None and right_cp is not None:
                    key = f"{left_cp},{right_cp}"
                    kerning[key] = value

    # Vertical metrics (ascent, descent, line gap) from OS/2 then hhea.
    if "OS/2" in font:
        os2 = font["OS/2"]
        ascent = os2.sTypoAscender
        descent = os2.sTypoDescender   # usually negative
        line_gap = os2.sTypoLineGap
    else:
        hhea = font["hhea"]
        ascent = hhea.ascent
        descent = hhea.descent
        line_gap = hhea.lineGap

    font.close()

    return {
        "font_name": font_name,
        "variant": variant,
        "source_ttf": ttf_path,
        "units_per_em": units_per_em,
        "ascent": ascent,
        "descent": descent,
        "line_gap": line_gap,
        "advances": advances,
        "kerning": kerning,
    }


def _glyph_to_cp(cmap: dict[int, str] | None, glyph: str) -> int | None:
    """Reverse lookup: glyph name → first matching codepoint."""
    if not cmap:
        return None
    for cp, g in cmap.items():
        if g == glyph:
            return cp
    return None


def extract_all() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for font_name, variants in FONT_FILE_MAP.items():
        for variant, ttf_path in variants.items():
            safe_name = font_name.replace(" ", "_")
            out_path = DATA_DIR / f"{safe_name}_{variant}.json"

            print(f"Extracting {font_name} ({variant}) from {ttf_path} ...", end=" ", flush=True)
            try:
                data = extract_font_metrics(ttf_path, font_name, variant)
                out_path.write_text(json.dumps(data, separators=(",", ":")))
                print(f"ok  ({len(data['advances'])} glyphs, {len(data['kerning'])} pairs)")
            except Exception as exc:
                print(f"FAILED: {exc}", file=sys.stderr)

    print(f"\nMetric tables written to {DATA_DIR}")


if __name__ == "__main__":
    extract_all()
