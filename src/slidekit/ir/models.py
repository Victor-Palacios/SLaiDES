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


class TwoColumnSlide(BaseModel):
    component: Literal["two-column"]
    title: Optional[str] = None
    left: list[ContentSlot] = Field(min_length=1)
    right: list[ContentSlot] = Field(min_length=1)
    left_weight: float = Field(default=1.0, gt=0.0)
    right_weight: float = Field(default=1.0, gt=0.0)


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


class QuoteOpenerSlide(BaseModel):
    component: Literal["quote-opener"]
    quote: str
    attribution: str


class BigNumberSlide(BaseModel):
    component: Literal["big-number"]
    value: str
    label: str
    context: Optional[str] = None


class PullQuoteSlide(BaseModel):
    component: Literal["pull-quote"]
    quote: str
    attribution: str


class StatementSlide(BaseModel):
    component: Literal["statement"]
    text: str


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


class Feature(BaseModel):
    icon: str
    heading: str
    body: str


class FeatureListSlide(BaseModel):
    component: Literal["feature-list"]
    title: Optional[str] = None
    features: list[Feature] = Field(min_length=1)


class ChecklistItem(BaseModel):
    text: str
    checked: bool = False


class ChecklistSlide(BaseModel):
    component: Literal["checklist"]
    title: str
    items: list[ChecklistItem] = Field(min_length=1)


class Step(BaseModel):
    title: str
    body: str


class NumberedStepsSlide(BaseModel):
    component: Literal["numbered-steps"]
    title: Optional[str] = None
    steps: list[Step] = Field(min_length=1)


# ── Phase 9: comparison (catalog #17–19) ──────────────────────────────────────


class BeforeAfterState(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


class BeforeAfterSlide(BaseModel):
    component: Literal["before-after"]
    title: Optional[str] = None
    before: BeforeAfterState
    after: BeforeAfterState


class ProsConsSlide(BaseModel):
    component: Literal["pros-cons"]
    title: Optional[str] = None
    pros_title: str = "Pros"
    cons_title: str = "Cons"
    pros: list[str] = Field(min_length=1)
    cons: list[str] = Field(min_length=1)


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


class ChartSlide(BaseModel):
    component: Literal["chart-slide"]
    title: Optional[str] = None
    chart: ChartSlot
    caption: Optional[str] = None


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


Slide = Annotated[
    Union[
        TitleSlide,
        TwoColumnSlide,
        IconTextRowsSlide,
        StatCalloutSlide,
        ComparisonColumnsSlide,
        TimelineSlide,
        ImageHalfBleedSlide,
        CardGridSlide,
        SectionDividerSlide,
        AgendaSlide,
        QuoteOpenerSlide,
        BigNumberSlide,
        PullQuoteSlide,
        StatementSlide,
        DefinitionSlide,
        QuestionSlide,
        BulletListSlide,
        FeatureListSlide,
        ChecklistSlide,
        NumberedStepsSlide,
        BeforeAfterSlide,
        ProsConsSlide,
        ThisVsThatSlide,
        KpiGridSlide,
        ChartSlide,
        ChartWithInsightSlide,
        TableSlide,
        MetricComparisonSlide,
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
