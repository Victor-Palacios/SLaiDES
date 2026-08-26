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

    primary: HexColor = "#123A6B"
    surface: HexColor = "#FFFFFF"
    accent: HexColor = "#0072CE"
    text: HexColor = "#0A2240"
    muted: HexColor = "#5B6B82"


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
    # Optional: the palette ROLE used to colour slide titles/headlines (e.g. "accent"
    # to make every headline the deck accent). None keeps each layout's existing title
    # colour, so decks that don't set it are unaffected.
    headline: Optional[str] = None

    @field_validator("headline")
    @classmethod
    def _headline_is_role(cls, v: Optional[str]) -> Optional[str]:
        roles = {"primary", "surface", "accent", "text", "muted"}
        if v is not None and v not in roles:
            raise ValueError(
                f"headline '{v}' must be a palette role name ({', '.join(sorted(roles))})"
            )
        return v

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


class _SlideBase(BaseModel):
    """Shared base for every slide component.

    Carries fields common to all slides. `source` is an optional http(s) URL
    rendered as a clickable "Source" citation in the bottom-right chrome (next
    to the page number) — for attributing a slide's content to its origin.
    """

    source: Optional[str] = None
    # Speaker notes for the presenter. Never rendered on the slide itself — the
    # pptx emitter writes them to the slide's notes page (PowerPoint's and Google
    # Slides' speaker-notes pane), so they carry no geometry and cannot affect
    # layout or lint.
    notes: Optional[str] = None

    @field_validator("source", check_fields=False)
    @classmethod
    def _source_is_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError(
                f"source '{v}' must be an http:// or https:// URL"
            )
        return v


class TitleSlide(_SlideBase):
    component: Literal["title-slide"]
    title: str
    subtitle: Optional[str] = None
    logo: Optional[ImageSlot] = None


class IconTextRow(BaseModel):
    icon: str
    heading: str
    body: str


class IconTextRowsSlide(_SlideBase):
    component: Literal["icon-text-rows"]
    title: Optional[str] = None
    rows: list[IconTextRow] = Field(min_length=1)


class Stat(BaseModel):
    value: str
    label: str
    subtext: Optional[str] = None


class StatCalloutSlide(_SlideBase):
    component: Literal["stat-callout"]
    title: Optional[str] = None
    stats: list[Stat] = Field(min_length=1)


class ComparisonItem(BaseModel):
    text: str
    icon: Optional[str] = None


class ComparisonColumnsSlide(_SlideBase):
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


class TimelineSlide(_SlideBase):
    component: Literal["timeline"]
    title: Optional[str] = None
    events: list[TimelineEvent] = Field(min_length=1)


class ImageHalfBleedSlide(_SlideBase):
    component: Literal["image-half-bleed"]
    title: Optional[str] = None
    image_side: Literal["left", "right"] = "left"
    image: ImageSlot
    content: list[ContentSlot] = Field(min_length=1)


class Card(BaseModel):
    icon: Optional[str] = None
    title: str
    body: str


class CardGridSlide(_SlideBase):
    component: Literal["card-grid"]
    title: Optional[str] = None
    cards: list[Card] = Field(min_length=1)


# ── Phase 9: openers & emphasis (catalog #2–9) ────────────────────────────────


class SectionDividerSlide(_SlideBase):
    component: Literal["section-divider"]
    number: str
    title: str


class AgendaSlide(_SlideBase):
    component: Literal["agenda"]
    title: str = "Agenda"
    items: list[str] = Field(min_length=1)


# QuoteOpenerSlide was retired 2026-07-05 per operator request (FB-048);
# PullQuoteSlide is the surviving quote layout.


class BigNumberSlide(_SlideBase):
    component: Literal["big-number"]
    value: str
    label: str
    context: Optional[str] = None


class PullQuoteSlide(_SlideBase):
    component: Literal["pull-quote"]
    quote: str
    attribution: str


# StatementSlide was retired 2026-07-05 per operator request (FB-047).


class DefinitionSlide(_SlideBase):
    component: Literal["definition"]
    term: str
    definition: str


class QuestionSlide(_SlideBase):
    component: Literal["question"]
    question: str


# ── Phase 9: lists & text (catalog #11, #13–15) ───────────────────────────────


class BulletListSlide(_SlideBase):
    component: Literal["bullet-list"]
    title: str
    items: list[str] = Field(min_length=1)


# Feature/FeatureListSlide were retired 2026-07-05 per operator request (FB-049);
# IconTextRowsSlide covers icon + heading + body rows.


class CodeSlide(_SlideBase):
    component: Literal["code"]
    title: Optional[str] = None  # optional filename / caption shown above the block
    code: str  # the code or terminal block; newlines are hard line breaks (no wrapping)
    chrome: bool = True  # show the window traffic-light dots


class FileTreeEntry(BaseModel):
    name: str  # e.g. "src/", "core.py" — a trailing "/" marks a directory
    depth: int = Field(default=0, ge=0)  # 0 = direct child of root; nesting level
    # None → inferred from the name (trailing "/" = dir, else file).
    kind: Optional[Literal["dir", "file"]] = None


class FileTreeSlide(_SlideBase):
    component: Literal["file-tree"]
    title: Optional[str] = None  # e.g. "Final folder shape" (on the light surface)
    root: str  # the top folder line, drawn with no connector, e.g. "simple-eda-project/"
    entries: list[FileTreeEntry] = Field(min_length=1)


class Step(BaseModel):
    title: str
    body: str


class NumberedStepsSlide(_SlideBase):
    component: Literal["numbered-steps"]
    title: Optional[str] = None
    steps: list[Step] = Field(min_length=1)


# ── Phase 9: comparison (catalog #17–19) ──────────────────────────────────────


class ListPanel(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


class TwoPanelListSlide(_SlideBase):
    """Two contrasting titled bullet panels. The generalised successor of the old
    before-after / pros-cons pair (operator FB-022): one layout, any two-state
    contrast — before/after, pros/cons, old/new, problem/solution. The right panel
    carries the accent (the "preferred"/later state); the left is muted."""

    component: Literal["two-panel-list"]
    title: Optional[str] = None
    left: ListPanel
    right: ListPanel
    # Optional per-slide emphasis: name the side to carry the accent colour (the other
    # goes muted). None keeps the default (left = primary, right = muted).
    accent_side: Optional[Literal["left", "right"]] = None


class VersusSide(BaseModel):
    value: str
    label: str


class ThisVsThatSlide(_SlideBase):
    component: Literal["this-vs-that"]
    title: Optional[str] = None
    left: VersusSide
    right: VersusSide


# ── Phase 9: data & stats (catalog #21–25) ────────────────────────────────────


class Kpi(BaseModel):
    value: str
    label: str


class KpiGridSlide(_SlideBase):
    component: Literal["kpi-grid"]
    title: Optional[str] = None
    kpis: list[Kpi] = Field(min_length=1)


class ChartWithInsightSlide(_SlideBase):
    component: Literal["chart-with-insight"]
    title: Optional[str] = None
    chart: ChartSlot
    insight: str


class TableSlide(_SlideBase):
    component: Literal["table-slide"]
    title: Optional[str] = None
    headers: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)


class Metric(BaseModel):
    value: str
    label: str
    delta: Optional[str] = None


class MetricComparisonSlide(_SlideBase):
    component: Literal["metric-comparison"]
    title: Optional[str] = None
    metrics: list[Metric] = Field(min_length=1)


# ── Phase 9: process & shape (catalog #26, 28–32) ─────────────────────────────


class ProcessStep(BaseModel):
    label: str
    body: str


class ProcessStepsSlide(_SlideBase):
    component: Literal["process-steps"]
    title: Optional[str] = None
    steps: list[ProcessStep] = Field(min_length=1)


class RoadmapPhase(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


class RoadmapSlide(_SlideBase):
    component: Literal["roadmap"]
    title: Optional[str] = None
    phases: list[RoadmapPhase] = Field(min_length=1)


class FunnelStage(BaseModel):
    label: str
    value: Optional[str] = None


class FunnelSlide(_SlideBase):
    component: Literal["funnel"]
    title: Optional[str] = None
    stages: list[FunnelStage] = Field(min_length=1)


class NestedStage(BaseModel):
    value: str
    label: str


class NestedCirclesSlide(_SlideBase):
    """Nested-circle funnel (operator-requested 2026-07-05): each stage is a circle
    INSIDE the previous, all tangent at the bottom — a subset-of-the-previous read
    (e.g. >700 applications ⊃ 6 interviews ⊃ 1.5 offers). Order stages large→small."""
    component: Literal["nested-circles"]
    title: Optional[str] = None
    stages: list[NestedStage] = Field(min_length=2, max_length=4)


class PyramidLayer(BaseModel):
    label: str


class PyramidSlide(_SlideBase):
    component: Literal["pyramid"]
    title: Optional[str] = None
    layers: list[PyramidLayer] = Field(min_length=1)


# Matrix2x2Slide was retired 2026-07-05 per operator feedback FB-044.


class SwotSlide(_SlideBase):
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


class ComparisonMatrixSlide(_SlideBase):
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
        FileTreeSlide,
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
        NestedCirclesSlide,
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
