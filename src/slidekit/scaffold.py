"""Starter-deck templates for ``slidekit new`` (Phase 7).

Each template is a complete, lint-clean deck the agent edits rather than authoring
from a blank file. Content is placeholder copy sized to fit its slots, so the
scaffold builds green out of the box — the agent swaps the text and rebuilds.

Templates are kept as literal YAML strings (not constructed from the IR models) so
the agent sees exactly the surface syntax it must edit, comments and all.
"""

from __future__ import annotations

_THEME_BLOCK = """version: 1
theme:
  palette:
    primary: "#1B4F8A"   # headings / strong accents
    surface: "#FFFFFF"   # slide background
    accent: "#E84545"    # icons / highlights
    text: "#1A1A2E"      # body copy
    muted: "#8A8A9A"     # page numbers / captions
  type_scale:
    title: 60            # 54-66pt
    header: 42           # 40-44pt
    body: 34             # 32-36pt (hard floor 32pt)
    caption: 25          # 24-26pt
  font: arial            # metric-safe set only
  motif: minimal
page_numbers:
  enabled: true
  start_at: 1
  skip_title_slide: true
slides:
"""

_TITLE_SLIDE = """  - component: title-slide
    title: "Your Deck Title"
    subtitle: "A one-line subtitle goes here"
"""

_TWO_COLUMN = """  - component: two-column
    title: "Section Heading"
    left:
      - type: text
        content: "First point on the left"
      - type: text
        content: "Second point on the left"
      - type: text
        content: "Third point on the left"
    right:
      - type: text
        content: "First point on the right"
      - type: text
        content: "Second point on the right"
      - type: text
        content: "Third point on the right"
"""

_STAT_CALLOUT = """  - component: stat-callout
    title: "Key Numbers"
    stats:
      - value: "42%"
        label: "Metric One"
        subtext: "short context"
      - value: "3x"
        label: "Metric Two"
        subtext: "short context"
      - value: "120"
        label: "Metric Three"
        subtext: "short context"
"""

_ICON_TEXT_ROWS = """  - component: icon-text-rows
    title: "Three Principles"
    rows:
      - icon: check
        heading: "First Principle"
        body: "One sentence explaining the first principle."
      - icon: lock
        heading: "Second Principle"
        body: "One sentence explaining the second principle."
      - icon: bolt
        heading: "Third Principle"
        body: "One sentence explaining the third principle."
"""

_COMPARISON = """  - component: comparison-columns
    title: "Before and After"
    left_title: "Before"
    right_title: "After"
    left_items:
      - text: "Old way, point one"
      - text: "Old way, point two"
      - text: "Old way, point three"
    right_items:
      - text: "New way, point one"
      - text: "New way, point two"
      - text: "New way, point three"
"""

# Named templates → ordered list of slide blocks. Keep every template lint-clean.
TEMPLATES: dict[str, list[str]] = {
    "title-slide": [_TITLE_SLIDE],
    "standard": [_TITLE_SLIDE, _TWO_COLUMN, _STAT_CALLOUT, _ICON_TEXT_ROWS],
    "comparison": [_TITLE_SLIDE, _COMPARISON],
    "pitch": [_TITLE_SLIDE, _TWO_COLUMN, _STAT_CALLOUT, _ICON_TEXT_ROWS, _COMPARISON],
}

DEFAULT_TEMPLATE = "standard"


def list_templates() -> list[str]:
    return sorted(TEMPLATES)


def render_template(name: str) -> str:
    """Return the full YAML for a named template. Raises KeyError if unknown."""
    if name not in TEMPLATES:
        raise KeyError(name)
    return _THEME_BLOCK + "\n".join(TEMPLATES[name])
