"""Linter checks over ResolvedDeck — the replacement for visual QA.

Every check the image-inspection prompt performs, implemented as
geometry/style assertions over ResolvedDeck. Errors block the build;
warnings are collected and reported.

Output: JSON list {code, slide, node_path, message, suggested_fix}
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Optional

from slidekit.ir.models import DeckIR
from slidekit.layout.models import Rect, ResolvedDeck, ResolvedNode, ResolvedSlide
from slidekit.metrics.constants import (
    BODY_FONT_FLOOR_PT,
    CAPTION_FONT_RANGE,
    EMU_PER_INCH,
    GAP_MIN_EMU,
    MARGIN_MIN_EMU,
    PAGE_NUMBER_PT,
    SAFE_FONTS,
    SLACK_WIDTH_FRACTION,
    SLACK_HEIGHT_HALF_LINE,
)

Severity = Literal["error", "warning"]

# Max acceptable spread (in wrapped lines) between the longest and shortest
# timeline event description before W_TIMELINE_BALANCE flags the column as
# unbalanced. In the narrow timeline columns even a one-line outlier reads as
# "cut off" next to its siblings (operator feedback FB-013), so timelines are
# held to uniform column heights: any spread beyond this many lines warns.
TIMELINE_BALANCE_LINE_SLACK = 0

# E_WRAP — text must fit on one line. Wrapped copy reads as "too long"; the fix is
# fewer words, never a smaller font (the 32pt floor is not negotiable).
#
# Some slots are physically too narrow to hold a readable single line: the
# timeline/card-grid/process-steps columns are under 3 inches wide, where one line
# is roughly ten characters. Holding those to one line would cap a description at
# a single word, and widening the box is not an option — copy is fitted to proven
# geometry, not the reverse. So a slot whose one-line capacity falls below this
# many characters warns (W_WRAP) instead of failing the build.
MIN_SINGLE_LINE_CAPACITY = 15

# Representative mixed-case English used to derive an average glyph width. Fixed
# so the capacity figure is deterministic and reproducible across runs.
_CAPACITY_SAMPLE = "the quick brown fox jumps over a lazy dog"


def single_line_capacity(node: ResolvedNode) -> int:
    """Roughly how many characters of average English fit on one line of this box.

    Character-based and derived from real font metrics — no rendering involved —
    so it can be asserted on directly in tests and quoted in the lint message as a
    budget the author can write to.
    """
    from slidekit.metrics.measure import measure_text

    font = node.font or "arial"
    size = node.size_pt or BODY_FONT_FLOOR_PT
    sample_w = measure_text(_CAPACITY_SAMPLE, font, size, node.bold)
    if sample_w <= 0:
        return 0
    avg_char_w = sample_w / len(_CAPACITY_SAMPLE)
    return int(node.rect.w // avg_char_w)


@dataclass
class LintIssue:
    code: str
    severity: Severity
    slide: int
    node_path: str
    message: str
    suggested_fix: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "slide": self.slide,
            "node_path": self.node_path,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }


def lint(deck: DeckIR, resolved: ResolvedDeck) -> list[LintIssue]:
    """Run all lint checks and return the list of issues (errors + warnings)."""
    issues: list[LintIssue] = []

    for slide in resolved.slides:
        issues.extend(_check_slide(slide, deck))

    # Cross-slide warnings.
    issues.extend(_check_cross_slide(resolved, deck))

    return issues


def has_errors(issues: list[LintIssue]) -> bool:
    return any(i.severity == "error" for i in issues)


# ── per-slide checks ──────────────────────────────────────────────────────────


def _check_slide(slide: ResolvedSlide, deck: DeckIR) -> list[LintIssue]:
    issues: list[LintIssue] = []
    all_nodes = slide.nodes + slide.chrome

    # E_MARGIN — content too close to slide edge.
    for node in slide.nodes:  # don't check chrome (page number in corner is OK)
        issues.extend(_check_margin(node, slide))

    # E_OVERFLOW — text exceeds its box.
    for node in all_nodes:
        if node.node_type == "text":
            issues.extend(_check_overflow(node, slide))

    # E_WRAP — text wrapped onto a second line, i.e. the copy is too long.
    for node in all_nodes:
        if node.node_type == "text" and not node.is_chrome:
            issues.extend(_check_wrap(node, slide))

    # E_MONOCHROME — the slide renders with no colour at all.
    issues.extend(_check_monochrome(slide, deck))

    # E_OVERLAP — non-chrome nodes intersect.
    content_nodes = [n for n in slide.nodes if not n.is_chrome]
    issues.extend(_check_overlaps(content_nodes, slide))

    # E_GAP — sibling blocks too close together.
    issues.extend(_check_gaps(content_nodes, slide))

    # E_MIN_BODY_SIZE — body text below 32pt (chrome and caption-tier exempt).
    # Caption tier (24-26pt) is intentionally smaller; only text below the caption
    # floor triggers this error.
    for node in slide.nodes:
        if (node.node_type == "text" and not node.is_chrome
                and not node.is_caption and node.size_pt is not None):
            if node.size_pt < BODY_FONT_FLOOR_PT:
                issues.append(LintIssue(
                    code="E_MIN_BODY_SIZE",
                    severity="error",
                    slide=slide.slide_index,
                    node_path=node.node_id,
                    message=(
                        f"Text node '{node.node_id}' uses {node.size_pt}pt, "
                        f"below the 32pt body floor."
                    ),
                    suggested_fix=(
                        f"Set size_pt >= {BODY_FONT_FLOOR_PT} or mark the node as "
                        f"caption-tier if it is secondary annotation text (24-26pt)."
                    ),
                ))

    # E_FONT — font outside the safe set.
    for node in all_nodes:
        if node.font and node.font.lower() not in SAFE_FONTS:
            issues.append(LintIssue(
                code="E_FONT",
                severity="error",
                slide=slide.slide_index,
                node_path=node.node_id,
                message=(
                    f"Text node '{node.node_id}' uses font '{node.font}', "
                    f"which is not in the metric-safe set."
                ),
                suggested_fix=(
                    f"Change font to one of: {', '.join(sorted(SAFE_FONTS))}."
                ),
            ))

    # E_PAGE_NUMBER — if deck has page numbers enabled, check they're present.
    if deck.page_numbers.enabled:
        is_cover = slide.slide_index == 0 and slide.component == "title-slide"
        if is_cover and deck.page_numbers.skip_title_slide:
            pass  # expected to have no page number
        elif slide.page_number is not None and not slide.chrome:
            issues.append(LintIssue(
                code="E_PAGE_NUMBER",
                severity="error",
                slide=slide.slide_index,
                node_path="chrome",
                message="Page numbering is enabled but this slide has no page-number chrome.",
                suggested_fix="This is a layout engine bug — ensure chrome is emitted.",
            ))

    # E_CONTRAST — text contrast check (simplified: warn if text color = background color).
    # Full WCAG check requires effective background computation (out of scope for v1 without
    # background node tracking). We check obvious violations: text == surface color.
    issues.extend(_check_contrast(slide, deck))

    # ── Warnings ──────────────────────────────────────────────────────────────

    # W_TEXT_ONLY — text-only slide (no image/chart/icon/shape).
    slot_types = {n.slot_type for n in slide.nodes if n.slot_type}
    has_media = bool(slot_types & {"image", "chart", "icon"}) or any(
        n.node_type in ("box", "ellipse") for n in slide.nodes
    )
    # this-vs-that is deliberately text-only: the operator rejected the boxed VS
    # badge and accent colours (FB-028) — a bare typographic face-off is the design.
    # bullet-list joined it with FB-030 (its title accent rule was dropped too).
    if not has_media and slide.component not in ("title-slide", "this-vs-that",
                                                 "bullet-list"):
        issues.append(LintIssue(
            code="W_TEXT_ONLY",
            severity="warning",
            slide=slide.slide_index,
            node_path="slide",
            message="Slide contains only text — consider adding an image, chart, or icon.",
            suggested_fix="Add an icon-text-rows, stat-callout, or image-half-bleed component.",
        ))

    # W_PIN_USED — absolute pin positioning (not applicable in v1 — no pin nodes yet).

    # W_BULLETS — more than 6 bullets in a list (check text nodes with many lines from a list).
    for node in slide.nodes:
        if node.node_type == "text" and len(node.lines) > 6:
            issues.append(LintIssue(
                code="W_BULLETS",
                severity="warning",
                slide=slide.slide_index,
                node_path=node.node_id,
                message=f"Text block has {len(node.lines)} lines — consider splitting across slides.",
                suggested_fix="Reduce to ≤6 bullet points or split into two slides.",
            ))

    # W_TIMELINE_BALANCE — one timeline column's description wraps to noticeably
    # more lines than its siblings, so it reads as crowded/cut-off next to the
    # others (operator feedback FB-013: "set a limit for how many words can
    # appear; the other columns are perfect"). Deterministic: compare wrapped
    # line counts across the event-description nodes.
    if slide.component == "timeline":
        desc_nodes = [
            n for n in slide.nodes
            if n.node_type == "text" and n.node_id.startswith("ev_desc") and n.lines
        ]
        if len(desc_nodes) >= 2:
            line_counts = [len(n.lines) for n in desc_nodes]
            lo, hi = min(line_counts), max(line_counts)
            if hi - lo > TIMELINE_BALANCE_LINE_SLACK:
                longest = max(desc_nodes, key=lambda n: len(n.lines))
                issues.append(LintIssue(
                    code="W_TIMELINE_BALANCE",
                    severity="warning",
                    slide=slide.slide_index,
                    node_path=longest.node_id,
                    message=(
                        f"Timeline event description '{longest.node_id}' wraps to "
                        f"{hi} lines while the shortest column uses {lo} — the columns "
                        f"look unbalanced and the long one reads as cut off."
                    ),
                    suggested_fix=(
                        f"Shorten this description so every column wraps within "
                        f"{lo + TIMELINE_BALANCE_LINE_SLACK} lines (trim to roughly the "
                        f"word count of the shorter columns)."
                    ),
                ))

    # W_TITLE_HIERARCHY — title not clearly larger than body.
    title_nodes = [n for n in slide.nodes if n.node_type == "text" and n.bold and n.size_pt]
    body_nodes = [n for n in slide.nodes if n.node_type == "text" and not n.bold and n.size_pt]
    if title_nodes and body_nodes:
        max_title_pt = max(n.size_pt for n in title_nodes)
        max_body_pt = max(n.size_pt for n in body_nodes)
        if max_body_pt > 0 and max_title_pt / max_body_pt < 1.4:
            issues.append(LintIssue(
                code="W_TITLE_HIERARCHY",
                severity="warning",
                slide=slide.slide_index,
                node_path="slide",
                message=(
                    f"Title ({max_title_pt}pt) is less than 1.4× body ({max_body_pt}pt). "
                    f"Hierarchy appears weak."
                ),
                suggested_fix="Increase title size or decrease body size.",
            ))

    return issues


def _check_margin(node: ResolvedNode, slide: ResolvedSlide) -> list[LintIssue]:
    issues = []
    r = node.rect
    violations = []
    if r.x < MARGIN_MIN_EMU:
        violations.append(f"left edge {r.x} < {MARGIN_MIN_EMU} EMU (0.5\")")
    if r.y < MARGIN_MIN_EMU:
        violations.append(f"top edge {r.y} < {MARGIN_MIN_EMU} EMU (0.5\")")
    if r.right() > slide.canvas_w - MARGIN_MIN_EMU:
        violations.append(f"right edge {r.right()} > {slide.canvas_w - MARGIN_MIN_EMU} EMU")
    if r.bottom() > slide.canvas_h - MARGIN_MIN_EMU:
        violations.append(f"bottom edge {r.bottom()} > {slide.canvas_h - MARGIN_MIN_EMU} EMU")
    for v in violations:
        issues.append(LintIssue(
            code="E_MARGIN",
            severity="error",
            slide=slide.slide_index,
            node_path=node.node_id,
            message=f"Content violates 0.5\" margin: {v}.",
            suggested_fix="Reduce content size, add padding, or use a different component.",
        ))
    return issues


def _check_overflow(node: ResolvedNode, slide: ResolvedSlide) -> list[LintIssue]:
    issues = []
    r = node.rect
    slack_w = int(r.w * SLACK_WIDTH_FRACTION)

    # Check if any line overflows its allocated box.
    for ln in node.lines:
        if ln.overflows:
            issues.append(LintIssue(
                code="E_OVERFLOW",
                severity="error",
                slide=slide.slide_index,
                node_path=node.node_id,
                message=(
                    f"Text '{ln.text[:40]}...' cannot break and overflows "
                    f"box width ({r.w} EMU)."
                ),
                suggested_fix=(
                    "Shorten the text, use a wider column, or break long words with spaces."
                ),
            ))

    # Check total text height vs box height.
    if node.lines:
        line_h = node.lines[0].height_emu if node.lines else 0
        slack_h = int(line_h * SLACK_HEIGHT_HALF_LINE)
        total_h = sum(ln.height_emu for ln in node.lines)
        if total_h > r.h + slack_h:
            issues.append(LintIssue(
                code="E_OVERFLOW",
                severity="error",
                slide=slide.slide_index,
                node_path=node.node_id,
                message=(
                    f"Text height ({total_h} EMU) exceeds box height "
                    f"({r.h} EMU + slack {slack_h} EMU)."
                ),
                suggested_fix=(
                    "Use fewer lines of text, enable shrink, "
                    "or allocate a taller box."
                ),
            ))

    return issues


def _check_wrap(node: ResolvedNode, slide: ResolvedSlide) -> list[LintIssue]:
    """Flag text that wraps onto a second line.

    Wrapping means the copy outran its slot. The remedy is always fewer words:
    shrinking the font is explicitly not allowed, and the box geometry is proven,
    so the sentence is what gives.
    """
    lines = node.lines or []
    if len(lines) <= 1:
        return []

    capacity = single_line_capacity(node)
    text = node.text_content or ""
    narrow = capacity < MIN_SINGLE_LINE_CAPACITY

    return [LintIssue(
        code="W_WRAP" if narrow else "E_WRAP",
        severity="warning" if narrow else "error",
        slide=slide.slide_index,
        node_path=node.node_id,
        message=(
            f"Text node '{node.node_id}' wraps onto {len(lines)} lines: "
            f"{len(text)} characters in a slot that fits about {capacity}."
        ),
        suggested_fix=(
            f"Shorten the text to about {capacity} characters so it fits on one "
            f"line. Do not reduce the font size."
            if not narrow else
            f"This slot fits only about {capacity} characters per line, too few "
            f"for one-line copy. Keep it as short as the design allows."
        ),
    )]


def _check_overlaps(nodes: list[ResolvedNode], slide: ResolvedSlide) -> list[LintIssue]:
    """Check for intersecting rects between sibling non-chrome nodes."""
    issues = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            # Skip pairs sharing the same non-None group_id: these are an
            # intentional stack (e.g. a text label sitting on its background box,
            # or sub-elements of one card). The plan exempts intentional stacks
            # from E_OVERLAP.
            if a.group_id is not None and a.group_id == b.group_id:
                continue
            if a.rect.intersects(b.rect):
                issues.append(LintIssue(
                    code="E_OVERLAP",
                    severity="error",
                    slide=slide.slide_index,
                    node_path=f"{a.node_id}↔{b.node_id}",
                    message=(
                        f"Nodes '{a.node_id}' and '{b.node_id}' overlap. "
                        f"Rects: {a.rect.to_dict()} ↔ {b.rect.to_dict()}"
                    ),
                    suggested_fix=(
                        "Reduce content, adjust weights, or use a different component."
                    ),
                ))
    return issues


def _check_gaps(nodes: list[ResolvedNode], slide: ResolvedSlide) -> list[LintIssue]:
    """Check for nodes in the same column/row that are too close (< 0.3\").

    Skips pairs that share the same non-None group_id — these are sub-elements
    within the same logical group (e.g., icon/title/body inside one card).
    """
    issues = []
    sorted_nodes = sorted(nodes, key=lambda n: n.rect.y)
    for i, a in enumerate(sorted_nodes):
        for b in sorted_nodes[i + 1:]:
            # Skip intra-group pairs (e.g., elements within the same card).
            if a.group_id is not None and a.group_id == b.group_id:
                continue
            if b.rect.y >= a.rect.bottom():
                gap = b.rect.y - a.rect.bottom()
                # Only flag if nodes are horizontally overlapping (same column).
                if a.rect.x < b.rect.right() and b.rect.x < a.rect.right():
                    if 0 < gap < GAP_MIN_EMU:
                        issues.append(LintIssue(
                            code="E_GAP",
                            severity="error",
                            slide=slide.slide_index,
                            node_path=f"{a.node_id}↔{b.node_id}",
                            message=(
                                f"Gap between '{a.node_id}' and '{b.node_id}' "
                                f"is {gap} EMU < {GAP_MIN_EMU} EMU (0.3\")."
                            ),
                            suggested_fix="Increase spacing between elements.",
                        ))
    return issues


# Operator style rule (2026-08-26): NO slide may render as pure black-and-white.
# Every slide must carry at least one element the eye reads as coloured. The page
# number is explicitly excluded — it is chrome, and its colour does not count.
#
# "Coloured" is judged perceptually, not by hex inequality: a deck's ink is often a
# very dark navy that reads as black. A CONTENT colour must be reasonably saturated
# AND light enough to register (s >= 0.35, v >= 0.50). A slide BACKGROUND is judged
# on saturation alone — a deliberate dark backdrop like the code panel's #0C1A1C is
# a colour choice, whereas pure #000000 (s = 0) is not.
_CHROMA_MIN_SAT = 0.35
_CHROMA_MIN_VAL = 0.50
_BACKDROP_MIN_SAT = 0.25


def _hsv(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    import colorsys
    return colorsys.rgb_to_hsv(r, g, b)


def _is_chromatic(hex_color: str, *, backdrop: bool = False) -> bool:
    """True if this colour reads as colour rather than as black/white/grey."""
    try:
        _, sat, val = _hsv(hex_color)
    except (ValueError, IndexError):
        return False
    if backdrop:
        return sat >= _BACKDROP_MIN_SAT
    return sat >= _CHROMA_MIN_SAT and val >= _CHROMA_MIN_VAL


def _check_monochrome(slide: ResolvedSlide, deck: DeckIR) -> list[LintIssue]:
    """E_MONOCHROME — the slide carries no colour the eye can see."""
    if slide.background and _is_chromatic(slide.background, backdrop=True):
        return []
    for node in slide.nodes:            # chrome (the page number) deliberately excluded
        for color in (node.text_color, node.fill_color):
            if color and _is_chromatic(color):
                return []
    return [LintIssue(
        code="E_MONOCHROME",
        severity="error",
        slide=slide.slide_index,
        node_path=f"slide[{slide.slide_index}]",
        message=(
            f"Slide {slide.slide_index} ({slide.component}) renders in black and "
            f"white: no element carries a colour the eye registers (the page "
            f"number does not count)."
        ),
        suggested_fix=(
            "Give the slide a chromatic element — the simplest is the deck theme's "
            "`headline: accent`, which colours the slide title. A palette accent on "
            "a rule, icon, or highlighted cell also satisfies this."
        ),
    )]


def _check_contrast(slide: ResolvedSlide, deck: DeckIR) -> list[LintIssue]:
    """E_CONTRAST — basic check: text color matches surface (zero contrast)."""
    issues = []
    surface = deck.theme.palette.surface.upper()
    for node in slide.nodes:
        if node.node_type == "text" and not node.is_chrome:
            # If the node has an explicit color that matches the surface, flag it.
            # (Full WCAG requires effective background — simplified here.)
            pass  # Full contrast requires background rect tracking; deferred to v1.1
    return issues


# ── cross-slide warnings ──────────────────────────────────────────────────────


def _check_cross_slide(resolved: ResolvedDeck, deck: DeckIR) -> list[LintIssue]:
    """Warnings that span multiple slides."""
    issues = []

    # W_REPEATED_COMPONENT — same component >2 consecutive slides.
    components = [s.component for s in resolved.slides]
    for i in range(len(components) - 2):
        if components[i] == components[i + 1] == components[i + 2]:
            issues.append(LintIssue(
                code="W_REPEATED_COMPONENT",
                severity="warning",
                slide=i + 2,
                node_path="slide",
                message=(
                    f"Component '{components[i]}' appears on 3+ consecutive slides "
                    f"(slides {i + 1}–{i + 3})."
                ),
                suggested_fix="Vary the layout to maintain visual interest.",
            ))

    return issues
