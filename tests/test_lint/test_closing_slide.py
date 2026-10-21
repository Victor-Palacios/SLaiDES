"""E_CLOSING_QUESTION — a deck never ends on a bare question slide (operator
2026-10-21: "don't end on these kinds of useless slides")."""
from __future__ import annotations

import textwrap

from slidekit.ir.parse import loads
from slidekit.layout import resolve
from slidekit.lint.checks import lint


def _codes(text: str) -> list[str]:
    deck = loads(textwrap.dedent(text))
    return [e.code for e in lint(deck, resolve(deck)) if e.severity == "error"]


def test_a_closing_question_is_an_error():
    assert "E_CLOSING_QUESTION" in _codes("""\
        version: 1
        slides:
          - component: bullet-list
            title: "Good Habits"
            items: ["Draw to explain", "One question per diagram"]
          - component: question
            question: "What would you draw first?"
        """)


def test_an_opening_question_is_fine():
    assert "E_CLOSING_QUESTION" not in _codes("""\
        version: 1
        slides:
          - component: question
            question: "Where does your data live?"
          - component: bullet-list
            title: "Good Habits"
            items: ["Draw to explain", "One question per diagram"]
        """)


def test_a_one_slide_component_specimen_is_exempt():
    # A specimen deck shows one component; it has no ending to judge.
    assert "E_CLOSING_QUESTION" not in _codes("""\
        version: 1
        slides:
          - component: question
            question: "What are you building?"
        """)
