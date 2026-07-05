"""Deterministic component recommender: a content *shape* -> ranked layout components.

The no-LLM half of the selection pipeline. Given structural facts about a slide's content
(`ContentFeatures` — how many groups/items, is it ordered, a quote, a chart, etc.), score
each component by a fixed rule ladder and return the best matches with a rationale. Pure
and deterministic: same features in -> same ranking out, no rendering, no model call.

This complements the LLM-facing selection guide (docs/LAYOUT_SELECTION_GUIDE.md /
`slidekit catalog`): an LLM picks with judgement; this picks by rule when no choice is given.
"""
from __future__ import annotations

from dataclasses import dataclass

from slidekit.catalog.registry import catalog


@dataclass(frozen=True)
class ContentFeatures:
    """Structural facts about one slide's content — what it IS, not how it looks."""
    groups: int = 0          # parallel content groups (columns / panels / quadrants)
    items: int = 0           # list items / cards / steps / tiers
    ordered: bool = False    # a sequence (steps, stages)
    horizontal: bool = False # the sequence reads left-to-right rather than top-down
    trend: str | None = None # 'narrowing' | 'widening' (for funnel / pyramid)
    metrics: int = 0         # value+label pairs
    deltas: bool = False     # metrics carry up/down deltas
    grid: bool = False       # arranged as a 2-D grid rather than a row
    single_value: bool = False  # one hero number
    quote: bool = False
    portrait: bool = False   # a person's photo accompanies the quote
    people: int = 0          # team members (photo + name + role)
    logos: int = 0
    images: int = 0
    chart: bool = False
    insight: bool = False    # a chart plus a one-line takeaway
    table: bool = False      # generic rows x columns
    options_criteria: bool = False  # options scored across criteria
    axes: bool = False       # two-axis 2x2 plane
    swot: bool = False       # explicitly a SWOT
    vs: bool = False         # head-to-head A vs B
    code: bool = False       # source code / a terminal session
    icons: bool = False      # rows carry icons
    agenda: bool = False     # a table of contents
    cover: bool = False      # a deck / section cover
    section: bool = False    # a section divider specifically


@dataclass(frozen=True)
class Suggestion:
    component: str
    score: float
    rationale: str


def _rules(f: ContentFeatures) -> list[Suggestion]:
    """Emit (component, score, rationale) candidates that match the features."""
    s: list[Suggestion] = []
    add = lambda c, sc, why: s.append(Suggestion(c, sc, why))

    # covers / dividers
    if f.cover:
        add("title-slide", 0.95, "a cover")
    if f.section:
        add("section-divider", 0.95, "a section break")
    if f.agenda:
        add("agenda", 0.95, "a table of contents")

    # quotes
    # (testimonial was retired 2026-07-03 per FB-029 — pull-quote covers quotes,
    # with or without a portrait)
    if f.quote:
        # (quote-opener retired 2026-07-05, FB-048 — pull-quote is THE quote layout)
        add("pull-quote", 0.8, "a quote with attribution")

    # single hero number
    if f.single_value:
        add("big-number", 0.95, "one hero metric")

    # metrics
    if f.metrics >= 2 and not f.single_value:
        if f.grid:
            add("kpi-grid", 0.9, "a grid of KPIs")
        elif f.deltas:
            add("metric-comparison", 0.9, "metrics with change deltas")
        else:
            add("stat-callout", 0.85, "a row of headline stats")

    # charts
    if f.chart and f.insight:
        add("chart-with-insight", 0.95, "a chart with a takeaway")
    elif f.chart:
        # The bare chart-slide was retired (FB-025): every chart ships with a takeaway.
        add("chart-with-insight", 0.85, "a chart (state its takeaway as the insight)")

    # tables / matrices
    if f.options_criteria:
        add("comparison-matrix", 0.95, "options scored across criteria")
    elif f.table:
        add("table-slide", 0.9, "tabular rows and columns")
    if f.swot:
        add("swot", 0.95, "a SWOT analysis")
    elif f.axes:
        # matrix-2x2 retired (FB-044): quadrant labels fall back to peer cards.
        add("card-grid", 0.6, "quadrant labels as peer cards (matrix-2x2 retired)")

    # ordered sequences
    if f.ordered and f.trend == "narrowing":
        add("funnel", 0.95, "tiers that narrow")
    elif f.ordered and f.trend == "widening":
        add("pyramid", 0.95, "tiers that widen")
    elif f.ordered:
        if f.horizontal:
            add("process-steps", 0.85, "a left-to-right sequence of steps")
        else:
            add("numbered-steps", 0.85, "an ordered top-down list of steps")

    # two-group comparisons
    if f.groups == 2 and f.vs:
        add("this-vs-that", 0.9, "a head-to-head A vs B")
    elif f.groups == 2 and f.items:
        add("comparison-columns", 0.8, "two titled bulleted columns")
        add("two-panel-list", 0.6, "two contrasting panels (before/after, pros/cons)")
    elif f.groups == 2:
        add("comparison-columns", 0.7, "two parallel content groups")

    # image-led (team-grid, image-full-bleed and image-grid were retired 2026-07-04
    # per FB-040..FB-042, logo-wall 2026-07-05 per FB-046 — image-half-bleed is the
    # surviving image layout; people/logo content falls back to card-grid cards)
    if f.people >= 1:
        add("card-grid", 0.7, "people as name+role cards (team-grid retired)")
    if f.logos >= 1:
        add("card-grid", 0.65, "logos as label cards (logo-wall retired)")
    if f.images >= 1 and not f.quote:
        add("image-half-bleed", 0.8, "an image beside supporting text")

    # rows with icons
    if f.icons and f.items:
        # (feature-list retired 2026-07-05, FB-049 — icon-text-rows covers it)
        add("icon-text-rows", 0.75, "labelled points each with an icon")

    # code / terminal
    if f.code:
        add("code", 0.9, "source code or a terminal session")
    # plain lists
    if f.items and f.groups <= 1 and not (f.ordered or f.icons or f.code or f.metrics):
        add("bullet-list", 0.6, "a plain vertical list")

    return s


def recommend(f: ContentFeatures, top: int = 3) -> list[Suggestion]:
    """Ranked component suggestions for a content shape (highest score first).

    Deterministic: stable sort by (-score, component). Always returns at least one
    suggestion (bullet-list as the catch-all). Only returns real components.
    """
    valid = set(catalog())
    cands = [c for c in _rules(f) if c.component in valid]
    if not cands:
        cands = [Suggestion("bullet-list", 0.3, "default: a plain list")]
    # de-dupe keeping the highest score per component
    best: dict[str, Suggestion] = {}
    for c in cands:
        if c.component not in best or c.score > best[c.component].score:
            best[c.component] = c
    ranked = sorted(best.values(), key=lambda c: (-c.score, c.component))
    return ranked[:top]
