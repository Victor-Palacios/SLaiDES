"""Component-metadata registry — the single source of truth for layout taxonomy + selection.

Each of the 40 IR components is grouped into a *layout family* (a distinct geometric
skeleton). Several components are honest **styled variants** of a family anchor — same
skeleton, differing only by marker/colour/orientation/field-set — so the true count of
distinct layouts (~25) is smaller than the component count (40). This module records that
mapping plus the human/LLM selection metadata (purpose, when-to-use, capacity,
content-shape), and derives each component's required/optional fields straight from the
pydantic models in `slidekit.ir.models` so field facts never drift from the schema.

Consumed by:
  - scripts/build_layout_taxonomy.py   -> docs/LAYOUT_TAXONOMY.md   (honest skeleton map)
  - `slidekit catalog [--json]` + scripts/build_selection_guide.py -> selection guide
  - slidekit.select.recommend          (content-shape -> component)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, get_args

from slidekit.ir.models import Slide


# ── curated metadata ────────────────────────────────────────────────────────────
# Per component: family (skeleton id), role ('anchor' = the canonical distinct skeleton,
# 'variant' = a styling of its family's anchor), variant_of, differs_by, purpose,
# use_when (selection cue), capacity (min,max repeatable items or None), content_shape
# (the structural fingerprint the recommender matches against).
#
# A family contributes ONE distinct skeleton (its anchor). Honest distinct count =
# number of families. Variant clustering follows the engine.py handler audit.

_META: dict[str, dict] = {
    # title
    "title-slide": dict(family="title", role="anchor", purpose="Deck/section cover.",
        use_when="Opening or closing a deck or a major section.",
        content_shape="a title (+ optional subtitle/logo), no body content"),

    # emphasis-stack family — one centered text stack; variants differ by roles/colour
    "statement": dict(family="emphasis-stack", role="anchor",
        purpose="A single bold centered line — a manifesto/claim.",
        use_when="One short, high-impact sentence should fill the slide.",
        content_shape="one short line of text"),
    "section-divider": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="section number + title (two roles)",
        purpose="Section break with number + title.", use_when="Marking a new section.",
        content_shape="a section number + a section title"),
    "quote-opener": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="italic quote + attribution",
        purpose="Open with a quote.", use_when="Leading a section with a quotation.",
        content_shape="a quote + an attribution"),
    "big-number": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="oversized accent value + label (+ context)",
        purpose="One hero metric.", use_when="A single number is the whole point.",
        content_shape="one dominant value + a label (+ optional context)"),
    "pull-quote": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="bold quote + attribution",
        purpose="Emphasised inline quote.", use_when="Highlighting a testimonial-style line.",
        content_shape="a quote + an attribution"),
    "definition": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="accent term + definition body",
        purpose="Define a term.", use_when="Introducing/anchoring one key term.",
        content_shape="a term + its definition"),
    "question": dict(family="emphasis-stack", role="variant", variant_of="statement",
        differs_by="single question line",
        purpose="Pose a question.", use_when="Framing a rhetorical/discussion prompt.",
        content_shape="one question"),

    # agenda
    "agenda": dict(family="agenda", role="anchor",
        purpose="Numbered agenda / table of contents.", use_when="Listing what the deck covers.",
        capacity=(2, 8), content_shape="an ordered list of section titles"),

    # two-column family
    "two-column": dict(family="two-column", role="anchor",
        purpose="Two weighted columns of free content.",
        use_when="Two parallel content groups (text/images) side by side.",
        content_shape="two groups of content slots"),
    "comparison-columns": dict(family="two-column", role="variant", variant_of="two-column",
        differs_by="fixed 50/50, titled, bulleted",
        purpose="Two titled bulleted columns.", use_when="Comparing two labelled options.",
        content_shape="two titled groups of bullets"),
    "image-half-bleed": dict(family="two-column", role="variant", variant_of="two-column",
        differs_by="one column is a half-bleed image",
        purpose="Image on one half, content on the other.",
        use_when="A supporting image should share the slide with text.",
        content_shape="one image + a group of content slots"),
    "chart-with-insight": dict(family="two-column", role="variant", variant_of="two-column",
        differs_by="chart (60%) + emphasis takeaway (40%)",
        purpose="A chart with a called-out takeaway.",
        use_when="A chart needs a one-line 'so what'.",
        content_shape="one chart + a short insight"),

    # icon-text-rows family
    "icon-text-rows": dict(family="icon-text-rows", role="anchor",
        purpose="Rows of icon + text.", use_when="A few labelled points, each with an icon.",
        capacity=(2, 6), content_shape="rows of {icon, heading, body}"),
    "feature-list": dict(family="icon-text-rows", role="variant", variant_of="icon-text-rows",
        differs_by="icon + heading + body per feature",
        purpose="Feature highlights.", use_when="Listing product features with icons.",
        capacity=(2, 6), content_shape="rows of {icon, heading, body}"),

    # stat-callout family (horizontal numeric cells)
    "stat-callout": dict(family="stat-callout", role="anchor",
        purpose="A row of stat cards (value + label).", use_when="2–4 headline stats in a row.",
        capacity=(2, 4), content_shape="several {value, label} pairs"),
    "metric-comparison": dict(family="stat-callout", role="variant", variant_of="stat-callout",
        differs_by="adds a delta chip per metric",
        purpose="Metrics with change deltas.", use_when="Showing metrics plus up/down deltas.",
        capacity=(2, 3), content_shape="several {value, label, delta} metrics"),

    # timeline
    "timeline": dict(family="timeline", role="anchor",
        purpose="Horizontal dated events.", use_when="A sequence of dated milestones.",
        capacity=(2, 6), content_shape="ordered {date, title, description} events"),

    # card-grid
    "card-grid": dict(family="card-grid", role="anchor",
        purpose="A grid of content cards.", use_when="Several peer items as cards.",
        capacity=(2, 8), content_shape="a set of {title, body, icon?} cards"),

    # marker-list family
    "bullet-list": dict(family="marker-list", role="anchor",
        purpose="A simple bulleted list.", use_when="A plain vertical list of points.",
        capacity=(2, 8), content_shape="a list of short lines"),
    "code": dict(family="code-block", role="anchor",
        purpose="A dark terminal/IDE-style code block.",
        use_when="Showing source code, a CLI session, or a config snippet verbatim.",
        content_shape="a block of monospace code/terminal lines"),
    "numbered-steps": dict(family="marker-list", role="variant", variant_of="bullet-list",
        differs_by="numbered chips (vertical)",
        purpose="An ordered vertical list of steps.", use_when="Sequential steps, read top-down.",
        capacity=(2, 6), content_shape="ordered {title, body} steps"),

    # two-panel-list family
    "before-after": dict(family="two-panel-list", role="anchor",
        purpose="Two contrasting bulleted panels (before vs after).",
        use_when="Showing a transformation between two states.",
        content_shape="two titled groups of bullets (states)"),
    "pros-cons": dict(family="two-panel-list", role="variant", variant_of="before-after",
        differs_by="pros (accent) vs cons (muted) colour roles",
        purpose="Pros vs cons panels.", use_when="Weighing advantages against disadvantages.",
        content_shape="two titled groups of bullets (for/against)"),

    # vs-badge
    "this-vs-that": dict(family="vs-badge", role="anchor",
        purpose="Head-to-head with a central VS badge.", use_when="A direct A-vs-B face-off.",
        content_shape="two short values opposed by a VS"),

    # metric grid
    "kpi-grid": dict(family="kpi-grid", role="anchor",
        purpose="A grid of KPIs (value + rule + label).", use_when="A dashboard of 3–6 KPIs.",
        capacity=(3, 6), content_shape="several {value, label} KPIs in a grid"),

    # chart / table
    "chart-slide": dict(family="chart", role="anchor",
        purpose="A single chart.", use_when="One chart is the focus.",
        content_shape="one chart (+ optional caption)"),
    "table-slide": dict(family="table", role="anchor",
        purpose="A data table.", use_when="Tabular rows and columns of values.",
        content_shape="a header row + body rows"),

    # process flow (horizontal)
    "process-steps": dict(family="process-flow", role="anchor",
        purpose="Horizontal numbered process.", use_when="A left-to-right sequence of steps.",
        capacity=(2, 5), content_shape="ordered {label, body} steps (horizontal)"),

    # roadmap
    "roadmap": dict(family="roadmap", role="anchor",
        purpose="Phased lanes with header bands.", use_when="A roadmap of phases each with items.",
        capacity=(2, 5), content_shape="phases, each a titled list of items"),

    # funnel / pyramid
    "funnel": dict(family="funnel", role="anchor",
        purpose="Narrowing funnel tiers.", use_when="A converging/narrowing sequence (e.g. a funnel).",
        capacity=(3, 6), content_shape="ordered tiers that narrow"),
    "pyramid": dict(family="pyramid", role="anchor",
        purpose="Widening pyramid tiers.", use_when="A hierarchy built on a broad base.",
        capacity=(3, 6), content_shape="ordered tiers that widen"),

    # matrices
    "matrix-2x2": dict(family="matrix-2x2", role="anchor",
        purpose="A 2×2 axes matrix.", use_when="Plotting items against two axes / four quadrants.",
        content_shape="four quadrants (+ axis labels)"),
    "swot": dict(family="swot", role="anchor",
        purpose="A SWOT 2×2 of titled bulleted panels.", use_when="A SWOT analysis specifically.",
        content_shape="four titled groups of bullets"),
    "comparison-matrix": dict(family="comparison-matrix", role="anchor",
        purpose="An options × criteria grid.", use_when="Comparing many options across criteria.",
        content_shape="row headers × column headers + cells"),

    # labeled image grids
    "team-grid": dict(family="labeled-image-grid", role="anchor",
        purpose="A grid of people (portrait + name + role).", use_when="Introducing a team.",
        capacity=(2, 9), content_shape="members {portrait, name, role}"),
    "logo-wall": dict(family="labeled-image-grid", role="variant", variant_of="team-grid",
        differs_by="logo tiles (image/label) instead of portrait+name+role",
        purpose="A wall of logos.", use_when="Showing customer/partner logos.",
        capacity=(3, 12), content_shape="logo tiles {image|label}"),

    # images
    "image-full-bleed": dict(family="image-full-bleed", role="anchor",
        purpose="A full-bleed image (+ overlay title).", use_when="One image should fill the slide.",
        content_shape="one image (+ optional overlay title)"),
    "image-grid": dict(family="image-grid", role="anchor",
        purpose="A gallery grid of images.", use_when="Showing several images together.",
        capacity=(2, 4), content_shape="a set of images (+ captions)"),

    # testimonial
    "testimonial": dict(family="testimonial", role="anchor",
        purpose="A testimonial (portrait + quote + name/role).", use_when="One customer quote with a face.",
        content_shape="a quote + name + role (+ portrait)"),
}


@dataclass(frozen=True)
class Layout:
    component: str
    family: str
    role: str  # 'anchor' | 'variant'
    variant_of: Optional[str]
    differs_by: Optional[str]
    purpose: str
    use_when: str
    capacity: Optional[tuple]  # (min, max) repeatable items, or None
    content_shape: str
    required_fields: tuple  # derived from the pydantic model
    optional_fields: tuple

    @property
    def distinct(self) -> bool:
        return self.role == "anchor"


def _slide_models() -> dict[str, type]:
    """component-key -> pydantic model class, enumerated from the IR Slide union."""
    out: dict[str, type] = {}
    for model in get_args(get_args(Slide)[0]):  # Annotated[Union[...], Field]
        lit = model.model_fields["component"].annotation
        key = get_args(lit)[0]
        out[key] = model
    return out


def _fields(model: type) -> tuple[tuple, tuple]:
    """(required, optional) field names of a slide model, excluding the discriminator."""
    req, opt = [], []
    for name, f in model.model_fields.items():
        if name == "component":
            continue
        (req if f.is_required() else opt).append(name)
    return tuple(req), tuple(opt)


def repeatable_field(component: str) -> Optional[str]:
    """Name of the component's repeatable (list-typed) content field, if any.

    Used to capacity-check an authored slide against the registry's capacity hint.
    """
    model = _slide_models().get(component)
    if model is None:
        return None
    for name, f in model.model_fields.items():
        ann = getattr(f.annotation, "__origin__", None)
        if ann in (list, tuple) or str(f.annotation).startswith("list["):
            return name
    return None


def catalog() -> dict[str, Layout]:
    """All 40 components with merged curated + schema-derived metadata, keyed by component."""
    models = _slide_models()
    out: dict[str, Layout] = {}
    for key, model in models.items():
        m = _META.get(key)
        if m is None:
            raise KeyError(f"registry _META missing metadata for component '{key}'")
        req, opt = _fields(model)
        out[key] = Layout(
            component=key,
            family=m["family"],
            role=m["role"],
            variant_of=m.get("variant_of"),
            differs_by=m.get("differs_by"),
            purpose=m["purpose"],
            use_when=m["use_when"],
            capacity=m.get("capacity"),
            content_shape=m["content_shape"],
            required_fields=req,
            optional_fields=opt,
        )
    return out


def distinct_families() -> list[str]:
    """Sorted list of distinct layout-family ids (one per distinct geometric skeleton)."""
    return sorted({l.family for l in catalog().values()})


def as_records() -> list[dict]:
    """The catalog as JSON-serialisable records, sorted by component — the machine-readable
    selection catalog an LLM consumes to pick layouts (no vision)."""
    out = []
    for key in sorted(catalog()):
        lo = catalog()[key]
        out.append({
            "component": lo.component,
            "family": lo.family,
            "distinct": lo.distinct,
            "variant_of": lo.variant_of,
            "differs_by": lo.differs_by,
            "purpose": lo.purpose,
            "use_when": lo.use_when,
            "capacity": list(lo.capacity) if lo.capacity else None,
            "content_shape": lo.content_shape,
            "required_fields": list(lo.required_fields),
            "optional_fields": list(lo.optional_fields),
        })
    return out
