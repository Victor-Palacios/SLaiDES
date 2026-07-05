"""Declarative IR schema for slidekit decks.

Version 1 — validated by pydantic with precise error paths.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic.functional_validators import AfterValidator

from slidekit.metrics.constants import SAFE_FONTS

# ── color validation ──────────────────────────────────────────────────────────

_HEX_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def _validate_hex(v: str) -> str:
    if not _HEX_RE.match(v):
        raise ValueError(
            f"invalid hex color '{v}': expected #RGB or #RRGGBB format"
        )
    # Expand #RGB → #RRGGBB for uniformity.
    if len(v) == 4:
        return "#" + "".join(c * 2 for c in v[1:])
    return v.upper()


HexColor = Annotated[str, AfterValidator(_validate_hex)]

# ── theme ─────────────────────────────────────────────────────────────────────


class Palette(BaseModel):
    """Theme color roles. Slides reference these roles, not raw hex."""

    primary: HexColor = "#1B4F8A"
    surface: HexColor = "#FFFFFF"
    accent: HexColor = "#E84545"
    text: HexColor = "#1A1A2E"
    muted: HexColor = "#8A8A9A"


class TypeScale(BaseModel):
    """Font size ranges (points) per tier. Body floor is 32pt — hard rule."""

    title: float = Field(default=60.0, ge=54.0, le=66.0)
    header: float = Field(default=42.0, ge=40.0, le=44.0)
    body: float = Field(default=34.0, ge=32.0, le=36.0)
    caption: float = Field(default=25.0, ge=24.0, le=26.0)


class Theme(BaseModel):
    """Design system: palette roles, type scale, spacing unit, motif, font."""

    palette: Palette = Field(default_factory=Palette)
    type_scale: TypeScale = Field(default_factory=TypeScale)
    spacing_unit: float = Field(default=12.0, gt=0.0)
    motif: str = "minimal"
    font: str = Field(default="arial")

    @field_validator("font")
    @classmethod
    def _font_must_be_safe(cls, v: str) -> str:
        low = v.lower()
        if low not in SAFE_FONTS:
            allowed = ", ".join(sorted(SAFE_FONTS))
            raise ValueError(
                f"font '{v}' is not in the metric-safe set. "
                f"Allowed fonts: {allowed}."
            )
        return low


# ── page numbers ──────────────────────────────────────────────────────────────


class PageNumbers(BaseModel):
    """Built-in chrome: page numbers rendered bottom-right at 16pt muted."""

    enabled: bool = True
    start_at: int = Field(default=1, ge=1)
    skip_title_slide: bool = False


# ── content slots ─────────────────────────────────────────────────────────────


class TextSlot(BaseModel):
    type: Literal["text"]
    content: str
    bold: bool = False
    italic: bool = False
    max_lines: Optional[int] = Field(default=None, gt=0)
    size_pt: Optional[float] = Field(default=None, ge=32.0)
    color: Optional[HexColor] = None


class ImageSlot(BaseModel):
    type: Literal["image"]
    path: str
    fit: Literal["cover", "contain"] = "contain"
    alt: str = ""


class ChartSeries(BaseModel):
    name: str
    values: list[float]


class ChartSlot(BaseModel):
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "pie", "scatter"] = "bar"
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    labels: list[str] = Field(default_factory=list)
    series: list[ChartSeries] = Field(default_factory=list)


class IconSlot(BaseModel):
    type: Literal["icon"]
    name: str
    color: Optional[HexColor] = None


class SpacerSlot(BaseModel):
    type: Literal["spacer"]
    size: Optional[float] = Field(default=None, gt=0.0)


ContentSlot = Annotated[
    Union[TextSlot, ImageSlot, ChartSlot, IconSlot, SpacerSlot],
    Field(discriminator="type"),
]

# ── slide components ──────────────────────────────────────────────────────────


class TitleSlide(BaseModel):
    component: Literal["title-slide"]
    title: str
    subtitle: Optional[str] = None
    logo: Optional[ImageSlot] = None


class IconTextRow(BaseModel):
    icon: str
    heading: str
    body: str


class IconTextRowsSlide(BaseModel):
    component: Literal["icon-text-rows"]
    title: Optional[str] = None
    rows: list[IconTextRow] = Field(min_length=1)


class Stat(BaseModel):
    value: str
    label: str
    subtext: Optional[str] = None


class StatCalloutSlide(BaseModel):
    component: Literal["stat-callout"]
    title: Optional[str] = None
    stats: list[Stat] = Field(min_length=1)


class ComparisonItem(BaseModel):
    text: str
    icon: Optional[str] = None


class ComparisonColumnsSlide(BaseModel):
    component: Literal["comparison-columns"]
    title: Optional[str] = None
    left_title: str
    right_title: str
    left_items: list[ComparisonItem] = Field(min_length=1)
    right_items: list[ComparisonItem] = Field(min_length=1)


class TimelineEvent(BaseModel):
    date: str
    title: str
    description: Optional[str] = None


class TimelineSlide(BaseModel):
    component: Literal["timeline"]
    title: Optional[str] = None
    events: list[TimelineEvent] = Field(min_length=1)


class ImageHalfBleedSlide(BaseModel):
    component: Literal["image-half-bleed"]
    title: Optional[str] = None
    image_side: Literal["left", "right"] = "left"
    image: ImageSlot
    content: list[ContentSlot] = Field(min_length=1)


class Card(BaseModel):
    icon: Optional[str] = None
    title: str
    body: str


class CardGridSlide(BaseModel):
    component: Literal["card-grid"]
    title: Optional[str] = None
    cards: list[Card] = Field(min_length=1)


# ── Phase 9: openers & emphasis (catalog #2–9) ────────────────────────────────


class SectionDividerSlide(BaseModel):
    component: Literal["section-divider"]
    number: str
    title: str


class AgendaSlide(BaseModel):
    component: Literal["agenda"]
    title: str = "Agenda"
    items: list[str] = Field(min_length=1)


# QuoteOpenerSlide was retired 2026-07-05 per operator request (FB-048);
# PullQuoteSlide is the surviving quote layout.


class BigNumberSlide(BaseModel):
    component: Literal["big-number"]
    value: str
    label: str
    context: Optional[str] = None


class PullQuoteSlide(BaseModel):
    component: Literal["pull-quote"]
    quote: str
    attribution: str


# StatementSlide was retired 2026-07-05 per operator request (FB-047).


class DefinitionSlide(BaseModel):
    component: Literal["definition"]
    term: str
    definition: str


class QuestionSlide(BaseModel):
    component: Literal["question"]
    question: str


# ── Phase 9: lists & text (catalog #11, #13–15) ───────────────────────────────


class BulletListSlide(BaseModel):
    component: Literal["bullet-list"]
    title: str
    items: list[str] = Field(min_length=1)


# Feature/FeatureListSlide were retired 2026-07-05 per operator request (FB-049);
# IconTextRowsSlide covers icon + heading + body rows.


class CodeSlide(BaseModel):
    component: Literal["code"]
    title: Optional[str] = None  # optional filename / caption shown above the block
    code: str  # the code or terminal block; newlines are hard line breaks (no wrapping)
    chrome: bool = True  # show the window traffic-light dots


class Step(BaseModel):
    title: str
    body: str


class NumberedStepsSlide(BaseModel):
    component: Literal["numbered-steps"]
    title: Optional[str] = None
    steps: list[Step] = Field(min_length=1)


# ── Phase 9: comparison (catalog #17–19) ──────────────────────────────────────


class ListPanel(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


class TwoPanelListSlide(BaseModel):
    """Two contrasting titled bullet panels. The generalised successor of the old
    before-after / pros-cons pair (operator FB-022): one layout, any two-state
    contrast — before/after, pros/cons, old/new, problem/solution. The right panel
    carries the accent (the "preferred"/later state); the left is muted."""

    component: Literal["two-panel-list"]
    title: Optional[str] = None
    left: ListPanel
    right: ListPanel


class VersusSide(BaseModel):
    value: str
    label: str


class ThisVsThatSlide(BaseModel):
    component: Literal["this-vs-that"]
    title: Optional[str] = None
    left: VersusSide
    right: VersusSide


# ── Phase 9: data & stats (catalog #21–25) ────────────────────────────────────


class Kpi(BaseModel):
    value: str
    label: str


class KpiGridSlide(BaseModel):
    component: Literal["kpi-grid"]
    title: Optional[str] = None
    kpis: list[Kpi] = Field(min_length=1)


class ChartWithInsightSlide(BaseModel):
    component: Literal["chart-with-insight"]
    title: Optional[str] = None
    chart: ChartSlot
    insight: str


class TableSlide(BaseModel):
    component: Literal["table-slide"]
    title: Optional[str] = None
    headers: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)


class Metric(BaseModel):
    value: str
    label: str
    delta: Optional[str] = None


class MetricComparisonSlide(BaseModel):
    component: Literal["metric-comparison"]
    title: Optional[str] = None
    metrics: list[Metric] = Field(min_length=1)


# ── Phase 9: process & shape (catalog #26, 28–32) ─────────────────────────────


class ProcessStep(BaseModel):
    label: str
    body: str


class ProcessStepsSlide(BaseModel):
    component: Literal["process-steps"]
    title: Optional[str] = None
    steps: list[ProcessStep] = Field(min_length=1)


class RoadmapPhase(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


class RoadmapSlide(BaseModel):
    component: Literal["roadmap"]
    title: Optional[str] = None
    phases: list[RoadmapPhase] = Field(min_length=1)


class FunnelStage(BaseModel):
    label: str
    value: Optional[str] = None


class FunnelSlide(BaseModel):
    component: Literal["funnel"]
    title: Optional[str] = None
    stages: list[FunnelStage] = Field(min_length=1)


class PyramidLayer(BaseModel):
    label: str


class PyramidSlide(BaseModel):
    component: Literal["pyramid"]
    title: Optional[str] = None
    layers: list[PyramidLayer] = Field(min_length=1)


# Matrix2x2Slide was retired 2026-07-05 per operator feedback FB-044.


class SwotSlide(BaseModel):
    component: Literal["swot"]
    title: Optional[str] = None
    # Exactly one statement per category (operator feedback FB-038): a SWOT slide
    # states the single defining point in each quadrant, not a packed list.
    strengths: list[str] = Field(min_length=1, max_length=1)
    weaknesses: list[str] = Field(min_length=1, max_length=1)
    opportunities: list[str] = Field(min_length=1, max_length=1)
    threats: list[str] = Field(min_length=1, max_length=1)


# ── Phase 9: structured relationships & visual (catalog #33, #35, #37–40) ────
# (team-grid, image-full-bleed and image-grid were retired 2026-07-04 per operator
# feedback FB-040..FB-042; logo-wall followed 2026-07-05 per FB-046.)


class ComparisonMatrixSlide(BaseModel):
    component: Literal["comparison-matrix"]
    title: Optional[str] = None
    options: list[str] = Field(min_length=1)
    criteria: list[str] = Field(min_length=1)
    cells: list[list[str]] = Field(min_length=1)
    # Up to two [row, col] cells rendered as accent chips — the ONLY colour in the
    # matrix body (FB-039: highlight one or two items, never the categories).
    highlights: list[tuple[int, int]] = Field(default_factory=list, max_length=2)


Slide = Annotated[
    Union[
        TitleSlide,
        IconTextRowsSlide,
        StatCalloutSlide,
        ComparisonColumnsSlide,
        TimelineSlide,
        ImageHalfBleedSlide,
        CardGridSlide,
        SectionDividerSlide,
        AgendaSlide,
        BigNumberSlide,
        PullQuoteSlide,
        DefinitionSlide,
        QuestionSlide,
        BulletListSlide,
        CodeSlide,
        NumberedStepsSlide,
        TwoPanelListSlide,
        ThisVsThatSlide,
        KpiGridSlide,
        ChartWithInsightSlide,
        TableSlide,
        MetricComparisonSlide,
        ProcessStepsSlide,
        RoadmapSlide,
        FunnelSlide,
        PyramidSlide,
        SwotSlide,
        ComparisonMatrixSlide,
    ],
    Field(discriminator="component"),
]

# ── top-level deck ────────────────────────────────────────────────────────────


class DeckIR(BaseModel):
    """Top-level deck IR. version must be 1."""

    version: Literal[1]
    theme: Theme = Field(default_factory=Theme)
    page_numbers: PageNumbers = Field(default_factory=PageNumbers)
    slides: list[Slide] = Field(min_length=1)
