"""Central location for slidekit measurement constants.

Slack margins absorb renderer variance between our computed geometry and
real PowerPoint/LibreOffice rendering. Tuned against the Phase 1 calibration
harness — do not adjust without re-running calibration.
"""

# Safety margin fractions applied to all fit checks.
SLACK_WIDTH_FRACTION = 0.04   # 4% of box width
SLACK_HEIGHT_HALF_LINE = 0.5  # 0.5 line-heights

# PowerPoint default text-box internal insets (inches → EMU at 914400 EMU/inch).
INSET_LEFT_EMU = int(0.1 * 914400)    # 91440
INSET_RIGHT_EMU = int(0.1 * 914400)   # 91440
INSET_TOP_EMU = int(0.05 * 914400)    # 45720
INSET_BOTTOM_EMU = int(0.05 * 914400) # 45720

# Line spacing: PowerPoint "single" = 1.2 × font size (approximation).
LINE_SPACING_SINGLE = 1.2

# EMU per inch and EMU per point (72pt/inch).
EMU_PER_INCH = 914400
EMU_PER_PT = EMU_PER_INCH // 72  # 12700

# Slide canvas sizes (EMU).
SLIDE_16_9_W = 12192000
SLIDE_16_9_H = 6858000
SLIDE_4_3_W = 9144000
SLIDE_4_3_H = 6858000

# Margin and gap enforcement.
MARGIN_MIN_EMU = int(0.5 * EMU_PER_INCH)   # 0.5" margin from slide edge
GAP_MIN_EMU = int(0.3 * EMU_PER_INCH)      # 0.3" minimum gap between siblings

# Font size floors/ranges (points).
BODY_FONT_FLOOR_PT = 32
CAPTION_FONT_RANGE = (24, 26)
BODY_FONT_RANGE = (32, 36)
HEADER_FONT_RANGE = (40, 44)
TITLE_FONT_RANGE = (54, 66)
PAGE_NUMBER_PT = 16  # chrome exception — not subject to the body floor

# Metric-safe font names (lowercase keys used in lookup tables).
SAFE_FONTS = frozenset({
    "arial",
    "calibri",
    "cambria",
    "times new roman",
    "courier new",
    "bookman old style",
    "century schoolbook",
})

# Map from metric-safe font names → backing TTF files used for metric extraction.
# Liberation fonts are metric-identical clones of the corresponding Microsoft fonts
# (same advance widths by design — they were built as drop-in replacements).
# For fonts without a metric-identical free substitute the closest available font
# is used; see NOTES.md for rationale.
FONT_FILE_MAP: dict[str, dict] = {
    "arial": {
        "regular":     "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "bold":        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "italic":      "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    },
    "times new roman": {
        "regular":     "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "bold":        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "italic":      "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
    },
    "courier new": {
        "regular":     "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "bold":        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "italic":      "/usr/share/fonts/truetype/liberation/LiberationMono-Italic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/liberation/LiberationMono-BoldItalic.ttf",
    },
    # DejaVu Sans is the closest freely available sans-serif; not metric-identical
    # to Calibri but used consistently so our extraction and calibration agree.
    "calibri": {
        "regular":     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold":        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "italic":      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    },
    "cambria": {
        "regular":     "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "bold":        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "italic":      "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
    },
    "bookman old style": {
        "regular":     "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "bold":        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
        "italic":      "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf",
    },
    "century schoolbook": {
        "regular":     "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "bold":        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
        "italic":      "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
        "bolditalic":  "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf",
    },
}
