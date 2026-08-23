"""E_WRAP — text must fit on one line.

Wrapped copy means the sentence outran its slot. The only sanctioned fix is fewer
words: the 32pt body floor makes shrinking the font off-limits, and the box
geometry is proven, so the copy is what gives.

Every assertion here is character- or metric-based. Nothing renders an image, so
the rule is enforceable in CI without LibreOffice.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from slidekit.ir.parse import load, loads
from slidekit.layout import resolve
from slidekit.lint import lint
from slidekit.lint.checks import MIN_SINGLE_LINE_CAPACITY, single_line_capacity

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def _swot(item: str) -> str:
    """A SWOT deck whose first strength is `item` — a ~28 character slot."""
    return textwrap.dedent(f"""\
        version: 1
        slides:
          - component: swot
            title: "Review"
            strengths:
              - "{item}"
            weaknesses:
              - "Thin margins"
            opportunities:
              - "New markets"
            threats:
              - "New entrants"
        """)


def _codes(deck_yaml: str) -> list[str]:
    deck = loads(deck_yaml)
    return [i.code for i in lint(deck, resolve(deck))]


class TestSingleLineCapacity:
    """The budget is derived from font metrics and counted in characters."""

    def test_capacity_is_deterministic(self):
        deck = loads(_swot("Strong brand"))
        nodes = [
            n
            for s in resolve(deck).slides
            for n in s.all_nodes()
            if n.node_type == "text"
        ]
        assert [single_line_capacity(n) for n in nodes] == [
            single_line_capacity(n) for n in nodes
        ]

    def test_capacity_scales_with_box_width(self):
        deck = loads(_swot("Strong brand"))
        nodes = [
            n
            for s in resolve(deck).slides
            for n in s.all_nodes()
            if n.node_type == "text"
        ]
        wide = max(nodes, key=lambda n: n.rect.w)
        narrow = min(nodes, key=lambda n: n.rect.w)
        assert single_line_capacity(wide) > single_line_capacity(narrow)

    def test_text_within_capacity_does_not_wrap(self):
        """The budget the message quotes has to actually hold."""
        deck = loads(_swot("Strong brand"))
        for slide in resolve(deck).slides:
            for node in slide.all_nodes():
                if node.node_type == "text" and node.text_content:
                    if len(node.text_content) <= single_line_capacity(node):
                        assert len(node.lines) == 1, (
                            f"{node.text_content!r} fits the budget but wrapped"
                        )


class TestWrapRule:
    def test_long_copy_is_an_error(self):
        assert "E_WRAP" in _codes(_swot("Designs are selectable, not just baked in"))

    def test_short_copy_is_clean(self):
        assert "E_WRAP" not in _codes(_swot("All designs are selectable"))

    def test_error_names_the_character_budget(self):
        deck = loads(_swot("Designs are selectable, not just baked in"))
        issue = next(i for i in lint(deck, resolve(deck)) if i.code == "E_WRAP")
        assert "41 characters" in issue.message
        assert "characters" in issue.suggested_fix

    def test_fix_is_never_a_smaller_font(self):
        """The 32pt floor is not negotiable, so the advice must not suggest it."""
        deck = loads(_swot("Designs are selectable, not just baked in"))
        issue = next(i for i in lint(deck, resolve(deck)) if i.code == "E_WRAP")
        assert "Do not reduce the font size" in issue.suggested_fix

    def test_wrapping_is_what_triggers_it(self):
        """One line is the criterion — not a raw character count in isolation."""
        deck = loads(_swot("All designs are selectable"))
        for slide in resolve(deck).slides:
            for node in slide.all_nodes():
                if node.node_type == "text":
                    assert len(node.lines) <= 1


class TestNarrowSlotsWarnInstead:
    """A slot under ~15 characters a line cannot hold readable one-line copy, and
    widening it is not allowed — so it warns rather than blocking the build."""

    def test_narrow_column_warns_not_errors(self):
        codes = _codes(textwrap.dedent("""\
            version: 1
            slides:
              - component: timeline
                title: "Milestones"
                events:
                  - date: "Q1"
                    title: "Foundation"
                    description: "Cloud platform migration done."
                  - date: "Q2"
                    title: "API Launch"
                    description: "REST API live with a strong SLA."
                  - date: "Q3"
                    title: "AI Beta"
                    description: "AI features shipped to partners."
                  - date: "Q4"
                    title: "Scale Out"
                    description: "APAC regions live; global cover."
            """))
        assert "W_WRAP" in codes
        assert "E_WRAP" not in codes

    def test_threshold_is_a_character_count(self):
        assert isinstance(MIN_SINGLE_LINE_CAPACITY, int)
        assert MIN_SINGLE_LINE_CAPACITY > 0


class TestExampleDecksHoldTheLine:
    def test_no_example_deck_wraps(self):
        """The rule is enforced, not merely available."""
        offenders = []
        for path in sorted(EXAMPLES_DIR.glob("*.yaml")):
            deck = load(path)
            for issue in lint(deck, resolve(deck)):
                if issue.code == "E_WRAP":
                    offenders.append(f"{path.name}: {issue.message}")
        assert offenders == [], "wrapping copy:\n" + "\n".join(offenders)

    def test_demo_deck_does_not_wrap(self):
        path = EXAMPLES_DIR / "theme-layouts-demo" / "deck.yaml"
        deck = load(path)
        codes = [i.code for i in lint(deck, resolve(deck))]
        assert "E_WRAP" not in codes
