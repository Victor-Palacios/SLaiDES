"""Phase 2 acceptance tests for the IR schema."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
import yaml

from slidekit.ir.models import (
    DeckIR,
    Palette,
    Theme,
    TypeScale,
    TitleSlide,
    TwoColumnSlide,
    StatCalloutSlide,
    TextSlot,
    ImageSlot,
)
from slidekit.ir.parse import load, loads
from slidekit.ir.schema import get_schema

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"

# ── minimal valid deck for building up from ───────────────────────────────────

MINIMAL_YAML = textwrap.dedent("""\
    version: 1
    slides:
      - component: title-slide
        title: "Hello World"
""")


# ── DeckIR round-trip parsing ─────────────────────────────────────────────────

class TestBasicParsing:
    def test_minimal_yaml_parses(self):
        deck = loads(MINIMAL_YAML)
        assert isinstance(deck, DeckIR)
        assert deck.version == 1
        assert len(deck.slides) == 1

    def test_defaults_applied(self):
        deck = loads(MINIMAL_YAML)
        assert deck.page_numbers.enabled is True
        assert deck.theme.font == "arial"
        assert deck.theme.type_scale.body >= 32.0

    def test_slide_is_title_slide(self):
        deck = loads(MINIMAL_YAML)
        slide = deck.slides[0]
        assert isinstance(slide, TitleSlide)
        assert slide.title == "Hello World"
        assert slide.subtitle is None

    def test_parse_json(self):
        data = {
            "version": 1,
            "slides": [{"component": "title-slide", "title": "Test"}],
        }
        deck = loads(json.dumps(data), fmt="json")
        assert deck.version == 1

    def test_all_example_decks_parse(self):
        """Every file in examples/ must parse without error."""
        yaml_files = list(EXAMPLES_DIR.glob("*.yaml")) + list(EXAMPLES_DIR.glob("*.yml"))
        assert len(yaml_files) >= 10, "Expected at least 10 example decks"
        for path in sorted(yaml_files):
            deck = load(path)
            assert isinstance(deck, DeckIR), f"Failed to parse {path.name}"
            assert len(deck.slides) >= 1, f"No slides in {path.name}"


# ── theme validation ──────────────────────────────────────────────────────────

class TestThemeValidation:
    def test_default_palette_valid(self):
        p = Palette()
        assert p.primary.startswith("#")

    def test_invalid_hex_rejected(self):
        with pytest.raises(Exception, match="invalid hex color"):
            Palette(primary="blue")

    def test_short_hex_expanded(self):
        p = Palette(primary="#FFF", surface="#000", accent="#F00", text="#111", muted="#888")
        assert len(p.primary) == 7

    def test_unsafe_font_rejected(self):
        with pytest.raises(Exception, match="metric-safe"):
            Theme(font="helvetica")

    def test_safe_fonts_accepted(self):
        for font in ("arial", "calibri", "cambria", "times new roman",
                     "courier new", "bookman old style", "century schoolbook"):
            t = Theme(font=font)
            assert t.font == font

    def test_body_size_floor_enforced(self):
        with pytest.raises(Exception):
            TypeScale(body=31.0)

    def test_title_size_ceiling_enforced(self):
        with pytest.raises(Exception):
            TypeScale(title=70.0)

    def test_type_scale_defaults_in_range(self):
        ts = TypeScale()
        assert 54 <= ts.title <= 66
        assert 40 <= ts.header <= 44
        assert 32 <= ts.body <= 36
        assert 24 <= ts.caption <= 26


# ── component coverage ────────────────────────────────────────────────────────

class TestComponents:
    def _deck_with_slide(self, slide_yaml: str) -> DeckIR:
        yaml_text = f"version: 1\nslides:\n" + textwrap.indent(
            "- " + slide_yaml.strip(), "  "
        )
        return loads(yaml_text)

    def test_title_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: title-slide
                title: "Hello"
                subtitle: "World"
        """))
        s = deck.slides[0]
        assert isinstance(s, TitleSlide)
        assert s.subtitle == "World"

    def test_two_column_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: two-column
                title: "Test"
                left:
                  - type: text
                    content: "Left"
                right:
                  - type: text
                    content: "Right"
        """))
        s = deck.slides[0]
        assert isinstance(s, TwoColumnSlide)

    def test_stat_callout_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: stat-callout
                title: "Stats"
                stats:
                  - value: "42%"
                    label: "Growth"
        """))
        s = deck.slides[0]
        assert isinstance(s, StatCalloutSlide)

    def test_icon_text_rows_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: icon-text-rows
                title: "Values"
                rows:
                  - icon: star
                    heading: "Excellence"
                    body: "We strive for the best."
        """))
        assert deck.slides[0].component == "icon-text-rows"

    def test_comparison_columns_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: comparison-columns
                left_title: "Before"
                right_title: "After"
                left_items:
                  - text: "Slow"
                right_items:
                  - text: "Fast"
        """))
        assert deck.slides[0].component == "comparison-columns"

    def test_timeline_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: timeline
                title: "Roadmap"
                events:
                  - date: "Q1"
                    title: "Launch"
        """))
        assert deck.slides[0].component == "timeline"

    def test_image_half_bleed_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: image-half-bleed
                image_side: left
                image:
                  type: image
                  path: "assets/photo.jpg"
                  fit: cover
                content:
                  - type: text
                    content: "Caption text"
        """))
        assert deck.slides[0].component == "image-half-bleed"

    def test_card_grid_slide(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: card-grid
                title: "Products"
                cards:
                  - icon: star
                    title: "Product A"
                    body: "Description"
        """))
        assert deck.slides[0].component == "card-grid"

    def test_all_eight_components_represented(self):
        components = {s.component for deck in
                      [load(p) for p in sorted(EXAMPLES_DIR.glob("*.yaml"))]
                      for s in deck.slides}
        expected = {
            "title-slide", "two-column", "icon-text-rows", "stat-callout",
            "comparison-columns", "timeline", "image-half-bleed", "card-grid",
        }
        assert expected.issubset(components), f"Missing: {expected - components}"


# ── content slot types ────────────────────────────────────────────────────────

class TestContentSlots:
    def _two_col(self, left_slot: str, right_slot: str) -> DeckIR:
        return loads(textwrap.dedent(f"""\
            version: 1
            slides:
              - component: two-column
                left:
                  - {left_slot}
                right:
                  - type: text
                    content: "placeholder"
        """))

    def test_text_slot(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: two-column
                left:
                  - type: text
                    content: "hello"
                right:
                  - type: text
                    content: "right"
        """))
        slot = deck.slides[0].left[0]
        assert isinstance(slot, TextSlot)

    def test_image_slot(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: image-half-bleed
                image:
                  type: image
                  path: "x.jpg"
                content:
                  - type: text
                    content: "text"
        """))
        assert isinstance(deck.slides[0].image, ImageSlot)

    def test_icon_slot(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: two-column
                left:
                  - type: icon
                    name: star
                right:
                  - type: text
                    content: "right"
        """))
        assert deck.slides[0].left[0].type == "icon"

    def test_spacer_slot(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: two-column
                left:
                  - type: spacer
                    size: 2
                right:
                  - type: text
                    content: "right"
        """))
        assert deck.slides[0].left[0].type == "spacer"

    def test_chart_slot(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: two-column
                left:
                  - type: chart
                    chart_type: bar
                    labels: [Jan, Feb]
                    series:
                      - name: Revenue
                        values: [100, 120]
                right:
                  - type: text
                    content: "right"
        """))
        assert deck.slides[0].left[0].type == "chart"


# ── error message quality ─────────────────────────────────────────────────────

class TestErrorMessages:
    def test_missing_version_names_field(self):
        with pytest.raises(ValueError) as exc:
            loads("slides:\n  - component: title-slide\n    title: X")
        assert "version" in str(exc.value)

    def test_wrong_version_value(self):
        with pytest.raises(ValueError) as exc:
            loads("version: 2\nslides:\n  - component: title-slide\n    title: X")
        assert "version" in str(exc.value).lower() or "2" in str(exc.value)

    def test_invalid_component_names_error(self):
        with pytest.raises(ValueError) as exc:
            loads("version: 1\nslides:\n  - component: unknown-thing\n    title: X")
        msg = str(exc.value).lower()
        assert "component" in msg or "unknown" in msg

    def test_bad_hex_color_error_message(self):
        with pytest.raises(ValueError) as exc:
            loads(textwrap.dedent("""\
                version: 1
                theme:
                  palette:
                    primary: "notacolor"
                    surface: "#FFF"
                    accent: "#F00"
                    text: "#111"
                    muted: "#888"
                slides:
                  - component: title-slide
                    title: X
            """))
        assert "invalid hex color" in str(exc.value).lower() or "hex" in str(exc.value).lower()

    def test_missing_required_field_names_it(self):
        with pytest.raises(ValueError) as exc:
            loads("version: 1\nslides:\n  - component: stat-callout\n")
        assert "stats" in str(exc.value)

    def test_empty_slides_list_rejected(self):
        with pytest.raises(ValueError):
            loads("version: 1\nslides: []\n")

    def test_error_includes_yaml_path(self):
        with pytest.raises(ValueError) as exc:
            loads(textwrap.dedent("""\
                version: 1
                theme:
                  font: wingdings
                slides:
                  - component: title-slide
                    title: X
            """))
        msg = str(exc.value)
        assert "font" in msg

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            load(tmp_path / "nonexistent.yaml")

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text("version: 1")
        with pytest.raises(ValueError, match="extension"):
            load(p)


# ── JSON Schema export ────────────────────────────────────────────────────────

class TestJsonSchema:
    def test_schema_is_dict(self):
        schema = get_schema()
        assert isinstance(schema, dict)

    def test_schema_has_title(self):
        schema = get_schema()
        assert "title" in schema or "$defs" in schema or "properties" in schema

    def test_schema_references_version(self):
        schema = get_schema()
        schema_str = json.dumps(schema)
        assert "version" in schema_str

    def test_schema_references_slides(self):
        schema = get_schema()
        schema_str = json.dumps(schema)
        assert "slides" in schema_str

    def test_write_schema(self, tmp_path):
        from slidekit.ir.schema import write_schema
        out = write_path = write_schema(tmp_path / "schema.json")
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)


# ── page numbers ──────────────────────────────────────────────────────────────

class TestPageNumbers:
    def test_default_enabled(self):
        deck = loads(MINIMAL_YAML)
        assert deck.page_numbers.enabled is True

    def test_start_at_default_one(self):
        deck = loads(MINIMAL_YAML)
        assert deck.page_numbers.start_at == 1

    def test_page_numbers_configurable(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            page_numbers:
              enabled: false
              start_at: 5
              skip_title_slide: true
            slides:
              - component: title-slide
                title: X
        """))
        pn = deck.page_numbers
        assert pn.enabled is False
        assert pn.start_at == 5
        assert pn.skip_title_slide is True
