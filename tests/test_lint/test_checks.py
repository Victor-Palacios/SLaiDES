"""Phase 4 acceptance tests for the linter.

Two acceptance criteria:
1. A fixture deck with one instance of every defect — linter catches all.
2. A clean deck produces zero errors.

The fixture is constructed directly as ResolvedDeck objects (bypassing
IR → layout) to inject specific defects with precision.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

import pytest

from slidekit.ir.parse import loads, load
from slidekit.layout import resolve
from slidekit.layout.models import Rect, ResolvedDeck, ResolvedNode, ResolvedSlide
from slidekit.lint import lint, has_errors, LintIssue
from slidekit.metrics.constants import (
    BODY_FONT_FLOOR_PT,
    EMU_PER_INCH,
    GAP_MIN_EMU,
    MARGIN_MIN_EMU,
    SLIDE_16_9_H,
    SLIDE_16_9_W,
)
from slidekit.metrics.measure import Line

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


# ── helpers ───────────────────────────────────────────────────────────────────

def _deck_with_one_slide(deck_yaml: str) -> "ResolvedDeck":
    deck = loads(deck_yaml)
    return deck, resolve(deck)


def _make_slide(
    index: int = 0,
    component: str = "title-slide",
    nodes: Optional[list[ResolvedNode]] = None,
    chrome: Optional[list[ResolvedNode]] = None,
    canvas_w: int = SLIDE_16_9_W,
    canvas_h: int = SLIDE_16_9_H,
    page_number: Optional[int] = 1,
) -> ResolvedSlide:
    return ResolvedSlide(
        slide_index=index,
        page_number=page_number,
        component=component,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        nodes=nodes or [],
        chrome=chrome or [],
    )


def _text_node(
    node_id: str,
    rect: Rect,
    text: str = "Sample text",
    font: str = "arial",
    size_pt: float = 34.0,
    bold: bool = False,
    italic: bool = False,
    lines: Optional[list[Line]] = None,
    is_chrome: bool = False,
) -> ResolvedNode:
    if lines is None:
        lh = int(size_pt * 1.2 * 12700)
        lines = [Line(text=text, width_emu=int(rect.w * 0.8), height_emu=lh)]
    return ResolvedNode(
        node_id=node_id,
        node_type="text",
        rect=rect,
        lines=lines,
        font=font,
        size_pt=size_pt,
        bold=bold,
        italic=italic,
        text_content=text,
        is_chrome=is_chrome,
    )


def _minimal_ir():
    return loads(textwrap.dedent("""\
        version: 1
        slides:
          - component: title-slide
            title: "Hello"
    """))


# ── DEFECT FIXTURE ────────────────────────────────────────────────────────────
# One instance of each error/warning; the linter must catch them all.

class TestDefectFixture:
    """Each test injects one defect and asserts the linter finds it."""

    def _lint_slide(self, slide: ResolvedSlide) -> list[LintIssue]:
        ir = _minimal_ir()
        rd = ResolvedDeck(slides=[slide])
        return lint(ir, rd)

    def _has_code(self, issues: list[LintIssue], code: str) -> bool:
        return any(i.code == code for i in issues)

    # E_OVERFLOW: text height exceeds box height.
    def test_e_overflow_height(self):
        line_h = int(34 * 1.2 * 12700)
        node = _text_node(
            "overflow_node",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, line_h),  # box fits only 1 line
            lines=[
                Line("Line one", 4_000_000, line_h),
                Line("Line two", 4_000_000, line_h),
                Line("Line three", 4_000_000, line_h),
            ],
            size_pt=34.0,
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_OVERFLOW"), (
            f"Expected E_OVERFLOW, got: {[i.code for i in issues]}"
        )

    # E_OVERFLOW: unbreakable token wider than box.
    def test_e_overflow_line(self):
        box_w = int(2 * EMU_PER_INCH)
        line_h = int(34 * 1.2 * 12700)
        node = _text_node(
            "overflow_line_node",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, box_w, line_h * 3),
            lines=[Line("LONGTOKEN", width_emu=box_w + 100_000, height_emu=line_h, overflows=True)],
            size_pt=34.0,
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_OVERFLOW")

    # E_OVERLAP: two nodes with overlapping rects.
    def test_e_overlap(self):
        n1 = _text_node("n1", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 3_000_000, 500_000))
        n2 = _text_node("n2", Rect(MARGIN_MIN_EMU + 100_000, MARGIN_MIN_EMU + 100_000, 3_000_000, 500_000))
        slide = _make_slide(nodes=[n1, n2])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_OVERLAP"), (
            f"Expected E_OVERLAP, got: {[i.code for i in issues]}"
        )

    # E_MARGIN: node right edge beyond canvas margin.
    def test_e_margin_right(self):
        # Place a node that extends past the right margin.
        node = _text_node(
            "margin_node",
            rect=Rect(
                SLIDE_16_9_W - MARGIN_MIN_EMU - 10_000,  # starts near right edge
                MARGIN_MIN_EMU,
                2_000_000,  # extends way past canvas
                500_000,
            ),
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_MARGIN"), (
            f"Expected E_MARGIN, got: {[i.code for i in issues]}"
        )

    # E_MARGIN: node too close to top edge.
    def test_e_margin_top(self):
        node = _text_node(
            "top_margin_node",
            rect=Rect(MARGIN_MIN_EMU, 0, 2_000_000, 500_000),  # y=0, within top margin
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_MARGIN")

    # E_GAP: two vertically adjacent overlapping-column nodes too close.
    def test_e_gap(self):
        small_gap = GAP_MIN_EMU // 2  # smaller than 0.3"
        n1 = _text_node("gap_n1", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 3_000_000, 500_000))
        n2 = _text_node(
            "gap_n2",
            Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU + 500_000 + small_gap, 3_000_000, 500_000),
        )
        slide = _make_slide(nodes=[n1, n2])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_GAP"), (
            f"Expected E_GAP (gap={small_gap} EMU < {GAP_MIN_EMU}), got: {[i.code for i in issues]}"
        )

    # E_MIN_BODY_SIZE: text node with size below 32pt.
    def test_e_min_body_size(self):
        node = _text_node(
            "small_text",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000),
            size_pt=24.0,  # below 32pt floor
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_MIN_BODY_SIZE"), (
            f"Expected E_MIN_BODY_SIZE, got: {[i.code for i in issues]}"
        )

    # E_FONT: text node with unsafe font.
    def test_e_font(self):
        node = _text_node(
            "bad_font",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000),
            font="wingdings",
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "E_FONT"), (
            f"Expected E_FONT, got: {[i.code for i in issues]}"
        )

    # E_PAGE_NUMBER: page numbers enabled but no chrome on slide.
    def test_e_page_number_missing(self):
        ir = loads(textwrap.dedent("""\
            version: 1
            page_numbers:
              enabled: true
            slides:
              - component: title-slide
                title: "Hello"
        """))
        node = _text_node("n", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000))
        # Slide with page_number=1 but no chrome.
        slide = _make_slide(nodes=[node], chrome=[], page_number=1)
        rd = ResolvedDeck(slides=[slide])
        issues = lint(ir, rd)
        assert self._has_code(issues, "E_PAGE_NUMBER"), (
            f"Expected E_PAGE_NUMBER, got: {[i.code for i in issues]}"
        )

    # W_TEXT_ONLY: slide with only text (no media). Uses feature-list — bullet-list
    # is exempt now that its accent rule is gone (FB-030) and the layout is
    # deliberately pure typography.
    def test_w_text_only(self):
        node = _text_node("n", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000))
        slide = _make_slide(component="feature-list", nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "W_TEXT_ONLY"), (
            f"Expected W_TEXT_ONLY, got: {[i.code for i in issues]}"
        )

    # W_REPEATED_COMPONENT: 3+ consecutive same component.
    def test_w_repeated_component(self):
        ir = _minimal_ir()
        node = _text_node("n", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000))
        slides = [
            _make_slide(index=i, component="bullet-list", nodes=[node], page_number=i + 1)
            for i in range(3)
        ]
        rd = ResolvedDeck(slides=slides)
        issues = lint(ir, rd)
        assert self._has_code(issues, "W_REPEATED_COMPONENT"), (
            f"Expected W_REPEATED_COMPONENT, got: {[i.code for i in issues]}"
        )

    # W_BULLETS: text node with more than 6 lines.
    def test_w_bullets(self):
        line_h = int(34 * 1.2 * 12700)
        many_lines = [Line(f"Bullet {i}", 3_000_000, line_h) for i in range(7)]
        node = _text_node(
            "many_bullets",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, line_h * 8),
            lines=many_lines,
        )
        slide = _make_slide(nodes=[node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "W_BULLETS"), (
            f"Expected W_BULLETS, got: {[i.code for i in issues]}"
        )

    # W_TITLE_HIERARCHY: title not 1.4× larger than body.
    def test_w_title_hierarchy(self):
        lh_title = int(34 * 1.2 * 12700)
        lh_body = int(32 * 1.2 * 12700)
        title_node = _text_node(
            "title",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, lh_title),
            size_pt=34.0,  # only slightly larger than body
            bold=True,
        )
        body_node = _text_node(
            "body",
            rect=Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU + lh_title + GAP_MIN_EMU, 5_000_000, lh_body),
            size_pt=32.0,
            bold=False,
        )
        slide = _make_slide(nodes=[title_node, body_node])
        issues = self._lint_slide(slide)
        assert self._has_code(issues, "W_TITLE_HIERARCHY"), (
            f"Expected W_TITLE_HIERARCHY (34pt / 32pt = {34/32:.2f} < 1.4), "
            f"got: {[i.code for i in issues]}"
        )


# ── CLEAN DECK produces zero errors ──────────────────────────────────────────

class TestCleanDeck:
    def test_example_decks_produce_no_errors(self):
        """All example decks in examples/ must produce zero lint errors."""
        yaml_files = sorted(EXAMPLES_DIR.glob("*.yaml"))
        for path in yaml_files:
            deck = load(path)
            rd = resolve(deck)
            issues = lint(deck, rd)
            errors = [i for i in issues if i.severity == "error"]
            assert errors == [], (
                f"{path.name} produced lint errors:\n"
                + "\n".join(f"  {e.code}: {e.message}" for e in errors)
            )

    def test_minimal_deck_zero_errors(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: title-slide
                title: "Clean Deck"
                subtitle: "No defects"
        """))
        rd = resolve(deck)
        issues = lint(deck, rd)
        errors = [i for i in issues if i.severity == "error"]
        assert errors == []


# ── Output format ─────────────────────────────────────────────────────────────

class TestOutputFormat:
    def test_issue_has_required_fields(self):
        ir = _minimal_ir()
        node = _text_node(
            "n", Rect(0, 0, 5_000_000, 500_000)  # margin violation (y=0)
        )
        slide = _make_slide(nodes=[node])
        rd = ResolvedDeck(slides=[slide])
        issues = lint(ir, rd)
        for issue in issues:
            d = issue.to_dict()
            assert "code" in d
            assert "severity" in d
            assert "slide" in d
            assert "node_path" in d
            assert "message" in d
            assert "suggested_fix" in d

    def test_timeline_balance_warns_on_uneven_columns(self):
        """FB-013: a timeline column that wraps to more lines than its siblings
        reads as cut off — W_TIMELINE_BALANCE flags it (deterministic, no render)."""
        deck, rd = _deck_with_one_slide(textwrap.dedent("""\
            version: 1
            slides:
              - component: timeline
                title: "Roadmap"
                events:
                  - date: "Q1"
                    title: "Foundation"
                    description: "Cloud migration and core setup complete."
                  - date: "Q2"
                    title: "API Launch"
                    description: "REST API live with 99.99% SLA."
                  - date: "Q3"
                    title: "AI Beta"
                    description: "AI features shipped to 500 partners."
                  - date: "Q4"
                    title: "Scale Out"
                    description: "APAC regions live; global coverage."
        """))
        codes = {i.code for i in lint(deck, rd)}
        assert "W_TIMELINE_BALANCE" in codes

    def test_timeline_balance_clean_when_columns_even(self):
        """Balanced timeline columns (all wrap to the same line count) do not warn."""
        deck, rd = _deck_with_one_slide(textwrap.dedent("""\
            version: 1
            slides:
              - component: timeline
                title: "Roadmap"
                events:
                  - date: "Q1"
                    title: "Foundation"
                    description: "Cloud platform migration done."
                  - date: "Q2"
                    title: "API Launch"
                    description: "REST API live with 99.99% SLA."
                  - date: "Q3"
                    title: "AI Beta"
                    description: "AI features shipped to 500 partners."
                  - date: "Q4"
                    title: "Scale Out"
                    description: "APAC regions live; global coverage."
        """))
        codes = {i.code for i in lint(deck, rd)}
        assert "W_TIMELINE_BALANCE" not in codes

    def test_has_errors_returns_true_on_error(self):
        node = _text_node("n", Rect(0, 0, 5_000_000, 500_000))
        slide = _make_slide(nodes=[node])
        ir = _minimal_ir()
        rd = ResolvedDeck(slides=[slide])
        issues = lint(ir, rd)
        assert has_errors(issues)

    def test_has_errors_returns_false_on_clean(self):
        deck = loads(textwrap.dedent("""\
            version: 1
            slides:
              - component: title-slide
                title: "OK"
        """))
        rd = resolve(deck)
        issues = lint(deck, rd)
        assert not has_errors(issues)

    def test_errors_before_warnings_convention(self):
        """Errors should have severity='error', warnings should have severity='warning'."""
        ir = _minimal_ir()
        # Node with bad size (error) and a text-only slide (warning).
        node = _text_node("n", Rect(MARGIN_MIN_EMU, MARGIN_MIN_EMU, 5_000_000, 500_000),
                          size_pt=20.0)
        # feature-list, not bullet-list: the latter is W_TEXT_ONLY-exempt (FB-030).
        slide = _make_slide(component="feature-list", nodes=[node])
        rd = ResolvedDeck(slides=[slide])
        issues = lint(ir, rd)
        error_codes = {i.code for i in issues if i.severity == "error"}
        warning_codes = {i.code for i in issues if i.severity == "warning"}
        assert "E_MIN_BODY_SIZE" in error_codes
        assert "W_TEXT_ONLY" in warning_codes
