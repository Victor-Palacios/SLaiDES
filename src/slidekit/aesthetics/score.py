"""Deterministic aesthetic sub-scores + composite over a ResolvedDeck.

Every metric is a closed-form function of the resolved geometry (node rects) and
the theme colours — reproducible, no rendering. Each sub-score is in [0, 1]; the
composite is reported 0–100. ADVISORY only: this never blocks a build.

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
# or is unreadable is "ugly" in a way balance can't compensate for.
DEFAULT_WEIGHTS: dict[str, float] = {
    "balance": 1.0,
    "whitespace": 1.0,
    "alignment": 1.0,
    "non_overlap": 1.5,
    "hierarchy": 1.0,
    "contrast": 1.5,
}

_ALIGN_TOL = int(0.06 * EMU_PER_INCH)  # ~0.06" edge-clustering tolerance


# ── helpers ───────────────────────────────────────────────────────────────────


def _rel_lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    chans = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in chans]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = _rel_lum(c1), _rel_lum(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


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
    if not nodes:
        return 0.0
    tot = sum(n.rect.w * n.rect.h for n in nodes) or 1
    cx = sum((n.rect.x + n.rect.w / 2) * n.rect.w * n.rect.h for n in nodes) / tot
    cy = sum((n.rect.y + n.rect.h / 2) * n.rect.w * n.rect.h for n in nodes) / tot
    dist = math.hypot(cx - cw / 2, cy - ch / 2)
    half = math.hypot(cw / 2, ch / 2)
    return max(0.0, 1 - dist / half)


def _whitespace(nodes, cw: int, ch: int) -> float:
    cover = min(1.0, sum(n.rect.w * n.rect.h for n in nodes) / (cw * ch))
    lo, hi = 0.12, 0.55  # comfortable coverage band; outside = bare or crowded
    if lo <= cover <= hi:
        return 1.0
    if cover < lo:
        return max(0.0, cover / lo)
    return max(0.0, 1 - (cover - hi) / (1 - hi))


def _alignment(nodes) -> float:
    if len(nodes) < 2:
        return 1.0
    lines: list[int] = []
    for n in nodes:
        x = n.rect.x
        if not any(abs(x - l) <= _ALIGN_TOL for l in lines):
            lines.append(x)
    return max(0.0, 1 - len(lines) / len(nodes))


def _non_overlap(nodes) -> float:
    if len(nodes) < 2:
        return 1.0
    tot = sum(n.rect.w * n.rect.h for n in nodes) or 1
    inter = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            inter += _intersect_area(nodes[i].rect, nodes[j].rect)
    return max(0.0, 1 - inter / tot)


def _hierarchy(deck: "DeckIR") -> float:
    ts = deck.theme.type_scale
    ratio = ts.title / ts.body if ts.body else 1.0
    # Reward a clear title→body step: full credit at ≥1.5×, none at ≤1.0×.
    return min(1.0, max(0.0, (ratio - 1.0) / 0.5))


def _contrast(rs: "ResolvedSlide", deck: "DeckIR") -> float:
    pal = deck.theme.palette
    ratios = []
    for n in rs.nodes:
        if n.node_type == "text" and not n.is_chrome:
            color = n.text_color or (pal.muted if n.is_caption else pal.text)
            ratios.append(_contrast_ratio(color, pal.surface))
    if not ratios:
        return 1.0
    worst = min(ratios)
    return min(1.0, max(0.0, (worst - 1.0) / (4.5 - 1.0)))  # WCAG body target 4.5:1


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
class AestheticReport:
    deck_score: float
    slides: list[SlideScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "deck_score": round(self.deck_score, 1),
            "slides": [s.to_dict() for s in self.slides],
        }

    def to_json(self, indent: int = 2) -> str:
        import json

        return json.dumps(self.to_dict(), indent=indent)


# ── public API ────────────────────────────────────────────────────────────────


def score_deck(
    deck: "DeckIR", resolved: "ResolvedDeck", weights: Optional[dict] = None
) -> AestheticReport:
    """Return a deterministic aesthetic report (0–100) for a resolved deck."""
    w = weights or DEFAULT_WEIGHTS
    wsum = sum(w.values()) or 1.0

    slide_scores: list[SlideScore] = []
    for rs in resolved.slides:
        nodes = _content_nodes(rs)
        sub = {
            "balance": _balance(nodes, rs.canvas_w, rs.canvas_h),
            "whitespace": _whitespace(nodes, rs.canvas_w, rs.canvas_h),
            "alignment": _alignment(nodes),
            "non_overlap": _non_overlap(nodes),
            "hierarchy": _hierarchy(deck),
            "contrast": _contrast(rs, deck),
        }
        composite = 100.0 * sum(sub[k] * w.get(k, 0.0) for k in sub) / wsum
        weakest = min(sub, key=lambda k: sub[k])
        slide_scores.append(
            SlideScore(rs.slide_index, rs.component, sub, composite, weakest)
        )

    deck_score = (
        sum(s.score for s in slide_scores) / len(slide_scores) if slide_scores else 0.0
    )
    return AestheticReport(deck_score=deck_score, slides=slide_scores)
