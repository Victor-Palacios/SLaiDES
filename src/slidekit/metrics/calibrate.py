"""Phase 1 calibration harness (throwaway, NOT part of the build loop).

Measures ~200 sample strings per font using PIL (ImageFont, which uses the same
TTF files our metric tables were extracted from), then compares against our
measure_text() implementation. Success criterion: all errors < 2%.

Usage: python -m slidekit.metrics.calibrate

This script produces a calibration_report.json with per-font statistics and
prints a human-readable summary. It is run once per environment change; the
result determines the Phase 1 go/no-go gate.

NOTE on ligatures: PIL/FreeType applies GSUB OpenType ligature substitution
automatically (e.g., 'fi' → fi-ligature glyph). PowerPoint does NOT apply
standard ligatures by default. Strings containing common ligature-forming
sequences (fi, fl, ff, ffi, ffl) are excluded from calibration so we compare
against equivalent rendering behaviour. This is documented in NOTES.md.
"""

from __future__ import annotations

import json
import random
import string
import sys
from pathlib import Path

from PIL import ImageFont

from slidekit.metrics.constants import EMU_PER_INCH, EMU_PER_PT, FONT_FILE_MAP
from slidekit.metrics.measure import measure_text

# Calibration sample size per font × variant.
SAMPLE_COUNT = 200
# Fixed seed for reproducibility.
SEED = 42
# Font size used for calibration measurements (points).
CALIBRATE_PT = 36

# Common OpenType ligature sequences excluded from comparison because PIL/FreeType
# applies GSUB substitution while PowerPoint leaves them as separate glyphs.
LIGATURE_SEQS = ("fi", "fl", "ff", "ffi", "ffl")

REPORT_PATH = Path(__file__).parent.parent.parent.parent / "ops" / "calibration_report.json"


def _pil_measure(text: str, ttf_path: str, size_pt: int) -> float:
    """Measure text width in EMU using PIL's actual font renderer."""
    # PIL uses pixels at 72 DPI by default; 1pt = 1px at 72 DPI.
    font = ImageFont.truetype(ttf_path, size=size_pt)
    # getlength returns width in pixels (= points at 72dpi).
    px_width = font.getlength(text)
    return px_width * EMU_PER_PT   # px → EMU (1pt = 12700 EMU)


def _sample_strings(rng: random.Random) -> list[str]:
    """Generate a varied set of test strings."""
    samples = []

    # Short common words.
    words = [
        "Hello", "World", "Slide", "Title", "Content", "Data",
        "Analysis", "Summary", "Report", "Chart", "Table", "Figure",
        "Introduction", "Conclusion", "Methodology", "Results", "Discussion",
        "The", "A", "An", "In", "Of", "To", "For", "With", "From", "By",
    ]
    samples.extend(rng.choices(words, k=30))

    # Random word-like strings (lowercase).
    for _ in range(30):
        length = rng.randint(4, 12)
        samples.append("".join(rng.choices(string.ascii_lowercase, k=length)))

    # Sentences.
    sentence_templates = [
        "The quick brown fox jumps",
        "Over the lazy dog",
        "Pack my box with five",
        "Dozen liquor jugs",
        "How vexingly quick",
        "Daft zebras jump",
        "Sphinx of black quartz",
        "Judge my vow",
        "Waltz nymph for quick jigs",
        "Glib jocks quiz",
    ]
    samples.extend(sentence_templates)

    # Mixed case.
    for _ in range(20):
        length = rng.randint(5, 15)
        samples.append("".join(rng.choices(string.ascii_letters, k=length)))

    # Single characters.
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        samples.append(ch)

    # Numbers.
    for _ in range(20):
        samples.append(str(rng.randint(100, 9999)))

    # Trim to sample count; pad if needed.
    while len(samples) < SAMPLE_COUNT:
        samples.append(rng.choice(words))
    return samples[:SAMPLE_COUNT]


def calibrate() -> dict:
    rng = random.Random(SEED)
    samples = _sample_strings(rng)

    results = {}
    all_errors = []

    for font_name, variants in FONT_FILE_MAP.items():
        font_results = {}
        for variant, ttf_path in variants.items():
            bold = "bold" in variant
            italic = "italic" in variant

            errors = []
            skipped_ligatures = 0
            for text in samples:
                if not text:
                    continue
                # Skip strings containing ligature-forming sequences — PIL applies
                # GSUB substitution but PowerPoint does not (see module docstring).
                text_lower = text.lower()
                if any(lig in text_lower for lig in LIGATURE_SEQS):
                    skipped_ligatures += 1
                    continue
                our_w = measure_text(text, font_name, CALIBRATE_PT, bold=bold, italic=italic)
                pil_w = _pil_measure(text, ttf_path, CALIBRATE_PT)

                if pil_w == 0:
                    continue
                err = abs(our_w - pil_w) / pil_w
                errors.append(err)

            if not errors:
                continue

            max_err = max(errors)
            mean_err = sum(errors) / len(errors)
            p95_err = sorted(errors)[int(0.95 * len(errors))]
            passes = all(e < 0.02 for e in errors)

            font_results[variant] = {
                "max_error": max_err,
                "mean_error": mean_err,
                "p95_error": p95_err,
                "n_samples": len(errors),
                "skipped_ligatures": skipped_ligatures,
                "passes_2pct": passes,
            }
            all_errors.extend(errors)

        results[font_name] = font_results

    # Overall gate.
    overall_max = max(all_errors) if all_errors else 0.0
    gate_passes = all(
        v["passes_2pct"]
        for font_results in results.values()
        for v in font_results.values()
    )

    report = {
        "gate_passes": gate_passes,
        "overall_max_error": overall_max,
        "calibrate_pt": CALIBRATE_PT,
        "sample_count": SAMPLE_COUNT,
        "fonts": results,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    return report


def _print_report(report: dict) -> None:
    gate = "PASS" if report["gate_passes"] else "FAIL"
    print(f"\n{'='*60}")
    print(f"Phase 1 Calibration — {gate}")
    print(f"Overall max error: {report['overall_max_error']*100:.3f}%  (limit: 2.00%)")
    print(f"{'='*60}")

    for font_name, variants in report["fonts"].items():
        for variant, stats in variants.items():
            status = "ok" if stats["passes_2pct"] else "FAIL"
            print(
                f"  {font_name:25s} {variant:12s}  "
                f"max={stats['max_error']*100:5.2f}%  "
                f"mean={stats['mean_error']*100:5.2f}%  "
                f"p95={stats['p95_error']*100:5.2f}%  [{status}]"
            )

    print(f"\nFull report: {REPORT_PATH}")


if __name__ == "__main__":
    report = calibrate()
    _print_report(report)
    sys.exit(0 if report["gate_passes"] else 1)
