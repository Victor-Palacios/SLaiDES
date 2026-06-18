"""Deterministic aesthetic sub-scores + composite over a ResolvedDeck.

Every metric is a closed-form function of the resolved geometry (node rects) and
the theme colours — reproducible, no rendering. Each sub-score is in [0, 1]; the
composite is reported 0–100. ADVISORY only: this never blocks a build.

Sub-scores (per slide unless noted):
  balance, whitespace, alignment, non_overlap, hierarchy, contrast,
  richness (visual engagement), color_harmony (theme-level).
Deck score = mean(slide scores) · cross_slide_consistency  (docs/AESTHETICS.md).

Calibration against human ratings is DEFERRED (needs a labelled slide-pair set);
do not claim human correlation. Default weights are documented below.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slidekit.ir.models import DeckIR
    from slidekit.layout.models import ResolvedDeck, ResolvedSlide, Rect

from slidekit.metrics.constants import EMU_PER_INCH

# Default sub-score weights. Overlap and contrast weigh more — a deck that overlaps
# or is unreadable is "ugly" in a way balance can't compensate for. Richness weighs
# as much as contrast: a deliberately-designed slide (accent emphasis, structural
# elements, restrained colour) must out-score a bare, text-only one — otherwise the
# geometric metrics reward minimalism for its own sake (see docs/AESTHETICS.md).
# These weights are HEURISTIC; calibration is DEFERRED (needs a labelled slide-pair
# dataset, cf. ref #2 EvoPresent). Per-decision lineage: docs/RESEARCH_TRACE.md.
DEFAULT_WEIGHTS: dict[str, float] = {
    "balance": 1.0,
    "whitespace": 1.0,
    "alignment": 1.0,
    "non_overlap": 1.5,
    "hierarchy": 1.0,
    "contrast": 1.5,
    "richness": 1.5,
    "color_harmony": 1.0,
}

_ALIGN_TOL = int(0.06 * EMU_PER_INCH)  # ~0.06" edge-clustering tolerance

# Advisory thresholds for the W_AESTH_* warnings. A sub-score below its threshold
# emits an advisory warning — NEVER a build-blocking error (the linter stays the
# gate, per docs/AESTHETICS.md "Relationship to the linter"). Tuned from the
# observed per-slide distribution across the 40-design example library so a warning
# flags a genuine outlier, not ordinary variation (e.g. the structurally-low
# alignment score of legitimate multi-column grids). HEURISTIC — documented in
# docs/AESTHETICS.md; calibration is DEFERRED.
ADVISORY_THRESHOLDS: dict[str, float] = {
    "balance": 0.50,
    "whitespace": 0.50,
    "alignment": 0.25,
    "non_overlap": 0.80,
    "hierarchy": 0.50,
    "contrast": 0.50,
    "richness": 0.40,
    "color_harmony": 0.40,
}

# Sub-metric → (warning code, human label, concrete fix). Codes mirror the linter's
# W_* namespace but live under W_AESTH_ so they are unmistakably advisory.
_WARN_META: dict[str, tuple[str, str, str]] = {
    "balance": (
        "W_AESTH_BALANCE",
        "visual mass is lopsided",
        "redistribute elements so the content centroid sits nearer the slide centre,"
        " or balance a heavy side with a counter-weight element.",
    ),
    "whitespace": (
        "W_AESTH_WHITESPACE",
        "slide is crowded or nearly empty",
        "aim for ~12–55% content coverage: add breathing room if crowded, or promote"
        " content / enlarge type if sparse.",
    ),
    "alignment": (
        "W_AESTH_ALIGNMENT",
        "element left edges do not share alignment lines",
        "snap related elements to shared left edges / a common grid column.",
    ),
    "non_overlap": (
        "W_AESTH_OVERLAP",
        "elements visually overlap",
        "separate the overlapping rects (the linter's E_OVERLAP is the hard gate; this"
        " advises on near-touching mass).",
    ),
    "hierarchy": (
        "W_AESTH_HIERARCHY",
        "title/body type contrast is weak",
        "increase the theme title size relative to body (aim for ≥1.5× the body size).",
    ),
    "contrast": (
        "W_AESTH_CONTRAST",
        "text/background contrast is low for its size",
        "darken/lighten the text colour against the surface (≥3:1 for large text,"
        " ≥4.5:1 for body).",
    ),
    "richness": (
        "W_AESTH_RICHNESS",
        "slide reads as bare / under-designed",
        "add deliberate accent-colour emphasis on a key element or a structural"
        " (non-text) element — within restraint.",
    ),
    "color_harmony": (
        "W_AESTH_HARMONY",
        "theme primary/accent hues are not in a recognised relationship",
        "choose accent vs primary hues that are analogous, complementary, or triadic.",
    ),
}

# Sub-metrics that are theme/deck-level (identical on every slide); warn ONCE at the
# deck level rather than repeating per slide.
_DECK_LEVEL = {"hierarchy", "color_harmony"}

# Cross-slide consistency advisory threshold (deck-level; metric is bounded [0.9, 1]).
_CONSISTENCY_THRESHOLD = 0.93

# WCAG contrast targets. Body floor is 32pt so essentially all slidekit content text
# is "large" by WCAG (≥18pt regular); large text needs only 3:1, which is why an
# accent emphasis figure (e.g. a coloured big-number) is NOT a contrast failure. The
# 4.5:1 body target is retained for any text below the large-text boundary.
_LARGE_TEXT_PT = 24.0  # WCAG / PLAN.md Phase-4 large-text threshold
_TARGET_LARGE = 3.0
_TARGET_BODY = 4.5


# ── colour helpers ──────────────────────────────────────────────────────────────


def _rel_lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    chans = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in chans]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = _rel_lum(c1), _rel_lum(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _hue_sat(hex_color: str) -> tuple[float, float]:
    """Return (hue 0–360, saturation 0–1) for a hex colour (HSV-style)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        hue = 0.0
    elif mx == r:
        hue = ((g - b) / d) % 6
    elif mx == g:
        hue = (b - r) / d + 2
    else:
        hue = (r - g) / d + 4
    sat = 0.0 if mx == 0 else d / mx
    return hue * 60.0, sat


def _hue_diff(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360.0
    return min(d, 360.0 - d)


def _norm(s: str) -> str:
    return s.lstrip("#").upper()


# ── geometry helpers ────────────────────────────────────────────────────────────


def _intersect_area(a: "Rect", b: "Rect") -> int:
    dx = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
    dy = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
    return dx * dy if dx > 0 and dy > 0 else 0


def _content_nodes(rs: "ResolvedSlide") -> list:
    return [
        n
        for n in rs.nodes
        if not n.is_chrome and n.node_type in ("text", "box", "icon", "image")
    ]


# ── per-metric sub-scores (each in [0, 1]) ──────────────────────────────────────


def _balance(nodes, cw: int, ch: int) -> float:
    # ref #4 (Ngo/Teo/Byrne, Info. Sci. 2003) balance/equilibrium — docs/RESEARCH_TRACE.md
    if not nodes:
        return 0.0
    tot = sum(n.rect.w * n.rect.h for n in nodes) or 1
    cx = sum((n.rect.x + n.rect.w / 2) * n.rect.w * n.rect.h for n in nodes) / tot
    cy = sum((n.rect.y + n.rect.h / 2) * n.rect.w * n.rect.h for n in nodes) / tot
    dist = math.hypot(cx - cw / 2, cy - ch / 2)
    half = math.hypot(cw / 2, ch / 2)
    return max(0.0, 1 - dist / half)


def _whitespace(nodes, cw: int, ch: int) -> float:
    # ref #1 (AeSlides) excessive-whitespace; band is HEURISTIC — docs/RESEARCH_TRACE.md
    cover = min(1.0, sum(n.rect.w * n.rect.h for n in nodes) / (cw * ch))
    lo, hi = 0.12, 0.55  # comfortable coverage band; outside = bare or crowded
    if lo <= cover <= hi:
        return 1.0
    if cover < lo:
        return max(0.0, cover / lo)
    return max(0.0, 1 - (cover - hi) / (1 - hi))


def _alignment(nodes) -> float:
    # ref #3 (GRIDS, CHI 2020) alignment objective — docs/RESEARCH_TRACE.md
    if len(nodes) < 2:
        return 1.0
    lines: list[int] = []
    for n in nodes:
        x = n.rect.x
        if not any(abs(x - l) <= _ALIGN_TOL for l in lines):
            lines.append(x)
    return max(0.0, 1 - len(lines) / len(nodes))


def _non_overlap(nodes) -> float:
    # ref #1 (AeSlides) element-collision — docs/RESEARCH_TRACE.md
    if len(nodes) < 2:
        return 1.0
    tot = sum(n.rect.w * n.rect.h for n in nodes) or 1
    inter = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            inter += _intersect_area(nodes[i].rect, nodes[j].rect)
    return max(0.0, 1 - inter / tot)


def _hierarchy(deck: "DeckIR") -> float:
    # HEURISTIC — no primary source for the exact ratio band; docs/RESEARCH_TRACE.md
    ts = deck.theme.type_scale
    ratio = ts.title / ts.body if ts.body else 1.0
    # Reward a clear title→body step: full credit at ≥1.5×, none at ≤1.0×.
    return min(1.0, max(0.0, (ratio - 1.0) / 0.5))


def _contrast(rs: "ResolvedSlide", deck: "DeckIR") -> float:
    """Worst per-node contrast, each node judged against its size-appropriate WCAG
    target (3:1 large text, 4.5:1 body). An accent emphasis figure that clears the
    large-text bar therefore earns full credit instead of being penalised.

    Thresholds: WCAG 2.x standard + PLAN.md Phase 4; ref #11 (Rebelo et al., EvoMUSART
    2024) backs contrast-as-constraint. See docs/RESEARCH_TRACE.md."""
    pal = deck.theme.palette
    norm = []
    for n in rs.nodes:
        if n.node_type == "text" and not n.is_chrome:
            color = n.text_color or (pal.muted if n.is_caption else pal.text)
            ratio = _contrast_ratio(color, pal.surface)
            large = (n.size_pt or 0.0) >= _LARGE_TEXT_PT
            target = _TARGET_LARGE if large else _TARGET_BODY
            norm.append(min(1.0, max(0.0, (ratio - 1.0) / (target - 1.0))))
    if not norm:
        return 1.0
    return min(norm)


def _richness(nodes, deck: "DeckIR") -> float:
    """Visual engagement: reward deliberate accent-colour emphasis, structural
    (non-text) elements, and restrained colour variety. A bare, all-default,
    text-only slide scores low here so a designed slide out-scores it — without
    rewarding gratuitous decoration (variety peaks at a small palette, then falls).

    ref #12 (Reinecke et al., CHI 2013) colourfulness/complexity — palette colour
    variety is a no-render proxy; the 0.45/0.35/0.20 split is HEURISTIC. See
    docs/RESEARCH_TRACE.md."""
    if not nodes:
        return 0.0
    pal = deck.theme.palette
    emphasis_roles = {_norm(pal.primary), _norm(pal.accent)}

    deliberate_colors: set[str] = set()
    has_emphasis = False
    has_structure = False
    for n in nodes:
        if n.node_type in ("box", "icon", "image"):
            has_structure = True
        for c in (n.fill_color, n.text_color):
            if c:
                cn = _norm(c)
                deliberate_colors.add(cn)
                if cn in emphasis_roles:
                    has_emphasis = True

    emphasis = 1.0 if has_emphasis else 0.0
    structure = 1.0 if has_structure else 0.0
    k = len(deliberate_colors)
    if k == 0:
        variety = 0.0
    elif k <= 3:
        variety = 1.0
    else:  # restraint: too many distinct deliberate colours reads as noisy
        variety = max(0.0, 1.0 - (k - 3) * 0.34)

    return 0.45 * emphasis + 0.35 * structure + 0.20 * variety


def _color_harmony(deck: "DeckIR") -> float:
    """Theme-level: hue relationship between the chromatic palette roles. Rewards a
    recognised relationship (mono / analogous / triadic / split-comp / complementary).
    Near-grey roles are ignored; a single chromatic role is treated as inoffensive.

    HEURISTIC — classical colour theory, no primary source cited; docs/RESEARCH_TRACE.md."""
    pal = deck.theme.palette
    chromatic = []
    for c in (pal.primary, pal.accent):
        hue, sat = _hue_sat(c)
        if sat >= 0.15:
            chromatic.append(hue)
    if len(chromatic) < 2:
        return 1.0
    diff = _hue_diff(chromatic[0], chromatic[1])
    good = (0.0, 30.0, 120.0, 150.0, 180.0)
    return max(0.0, min(1.0, max(1.0 - abs(diff - g) / 30.0 for g in good)))


def _cross_slide_consistency(resolved: "ResolvedDeck") -> float:
    """Deck-level coherence: low variance in content margins across slides reads as a
    consistent system. Bounded to [0.9, 1.0] so it modulates the deck score gently
    rather than dominating it (docs/AESTHETICS.md: deck = mean(slides)·consistency).

    ref #7 (PPTEval) / #8 (DECKBench) coherence — both SECONDHAND (unverified); the
    bound is HEURISTIC. See docs/RESEARCH_TRACE.md."""
    lefts, tops = [], []
    for rs in resolved.slides:
        nodes = _content_nodes(rs)
        if not nodes:
            continue
        lefts.append(min(n.rect.x for n in nodes))
        tops.append(min(n.rect.y for n in nodes))
    if len(lefts) < 2:
        return 1.0

    def _cv(xs: list[int]) -> float:
        m = sum(xs) / len(xs)
        if m <= 0:
            return 0.0
        var = sum((x - m) ** 2 for x in xs) / len(xs)
        return min(1.0, math.sqrt(var) / m)

    raw = 1.0 - (_cv(lefts) + _cv(tops)) / 2.0
    return 0.9 + 0.1 * max(0.0, min(1.0, raw))


# ── report types ────────────────────────────────────────────────────────────────


@dataclass
class SlideScore:
    slide_index: int
    component: str
    subscores: dict[str, float]
    score: float  # 0–100 weighted composite
    weakest: str  # lowest sub-metric (the thing to fix first)

    def to_dict(self) -> dict:
        return {
            "slide_index": self.slide_index,
            "component": self.component,
            "subscores": {k: round(v, 3) for k, v in self.subscores.items()},
            "score": round(self.score, 1),
            "weakest": self.weakest,
        }


@dataclass
class AestheticWarning:
    """One advisory W_AESTH_* finding. Same shape as a linter issue for tooling
    parity, but ADVISORY — it never blocks a build."""

    code: str
    slide: Optional[int]  # 1-based slide number, or None for deck/theme-level
    metric: str
    value: float
    threshold: float
    message: str
    suggested_fix: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "slide": self.slide,
            "metric": self.metric,
            "value": round(self.value, 3),
            "threshold": self.threshold,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class AestheticReport:
    deck_score: float
    slides: list[SlideScore] = field(default_factory=list)
    consistency: float = 1.0
    warnings: list[AestheticWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "deck_score": round(self.deck_score, 1),
            "consistency": round(self.consistency, 3),
            "warnings": [w.to_dict() for w in self.warnings],
            "slides": [s.to_dict() for s in self.slides],
        }

    def to_json(self, indent: int = 2) -> str:
        import json

        return json.dumps(self.to_dict(), indent=indent)


# ── advisory warnings ───────────────────────────────────────────────────────────


def _build_warnings(
    slide_scores: list[SlideScore], consistency: float
) -> list[AestheticWarning]:
    """Derive advisory W_AESTH_* warnings from sub-scores below threshold.

    Deck/theme-level metrics (hierarchy, colour harmony) are emitted ONCE; per-slide
    metrics are emitted per offending slide. Order is deterministic: deck-level first,
    then by slide index then metric name. ADVISORY only — never a build gate."""
    warns: list[AestheticWarning] = []
    seen_deck: set[str] = set()

    for ss in slide_scores:
        for metric in ADVISORY_THRESHOLDS:
            val = ss.subscores.get(metric)
            if val is None:
                continue
            thr = ADVISORY_THRESHOLDS[metric]
            if val >= thr:
                continue
            code, label, fix = _WARN_META[metric]
            if metric in _DECK_LEVEL:
                if code in seen_deck:
                    continue
                seen_deck.add(code)
                warns.append(
                    AestheticWarning(
                        code, None, metric, val, thr,
                        f"deck: {label} ({val:.2f} < {thr:.2f}).", fix,
                    )
                )
            else:
                warns.append(
                    AestheticWarning(
                        code, ss.slide_index + 1, metric, val, thr,
                        f"slide {ss.slide_index + 1} ({ss.component}): {label} "
                        f"({val:.2f} < {thr:.2f}).",
                        fix,
                    )
                )

    if consistency < _CONSISTENCY_THRESHOLD:
        warns.append(
            AestheticWarning(
                "W_AESTH_CONSISTENCY", None, "consistency", consistency,
                _CONSISTENCY_THRESHOLD,
                f"deck: content margins vary across slides "
                f"({consistency:.3f} < {_CONSISTENCY_THRESHOLD:.2f}).",
                "align the content block to a shared left/top margin across slides.",
            )
        )

    # Deck-level warnings first, then per-slide ordered by (slide, code).
    warns.sort(key=lambda w: (w.slide if w.slide is not None else -1, w.code))
    return warns


# ── public API ────────────────────────────────────────────────────────────────


def score_deck(
    deck: "DeckIR", resolved: "ResolvedDeck", weights: Optional[dict] = None
) -> AestheticReport:
    """Return a deterministic aesthetic report (0–100) for a resolved deck."""
    w = weights or DEFAULT_WEIGHTS
    wsum = sum(w.values()) or 1.0
    harmony = _color_harmony(deck)
    hierarchy = _hierarchy(deck)

    slide_scores: list[SlideScore] = []
    for rs in resolved.slides:
        nodes = _content_nodes(rs)
        sub = {
            "balance": _balance(nodes, rs.canvas_w, rs.canvas_h),
            "whitespace": _whitespace(nodes, rs.canvas_w, rs.canvas_h),
            "alignment": _alignment(nodes),
            "non_overlap": _non_overlap(nodes),
            "hierarchy": hierarchy,
            "contrast": _contrast(rs, deck),
            "richness": _richness(nodes, deck),
            "color_harmony": harmony,
        }
        composite = 100.0 * sum(sub[k] * w.get(k, 0.0) for k in sub) / wsum
        weakest = min(sub, key=lambda k: sub[k])
        slide_scores.append(
            SlideScore(rs.slide_index, rs.component, sub, composite, weakest)
        )

    consistency = _cross_slide_consistency(resolved)
    mean_slide = (
        sum(s.score for s in slide_scores) / len(slide_scores) if slide_scores else 0.0
    )
    return AestheticReport(
        deck_score=mean_slide * consistency,
        slides=slide_scores,
        consistency=consistency,
        warnings=_build_warnings(slide_scores, consistency),
    )
