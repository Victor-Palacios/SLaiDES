"""`slidekit author`: a lean outline (chosen or recommended components) -> valid, lint-clean,
deterministically-rendered deck — the topic→LLM-selection→render pipeline's render bridge."""

import re

import pytest
import yaml

from slidekit.layout import resolve
from slidekit.lint import lint
from slidekit.select.author import build_deck

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
DEMO = ROOT / "examples" / "author-demo" / "outline.yaml"


def _outline(text):
    return yaml.safe_load(text)


def test_demo_outline_builds_lint_clean():
    deck, notes = build_deck(_outline(DEMO.read_text()))
    assert len(deck.slides) == 4
    rd = resolve(deck)
    assert [i for i in lint(deck, rd) if i.code.startswith("E_")] == []
    # the component-less slide got recommended
    assert any("recommended 'big-number'" in n for n in notes)


def test_defaults_applied_without_theme_or_version():
    deck, _ = build_deck({"slides": [{"component": "question", "question": "Hello?"}]})
    assert deck.version == 1
    assert deck.theme is not None  # default theme applied


def test_recommend_block_picks_component():
    deck, notes = build_deck({"slides": [
        {"recommend": {"single_value": True}, "value": "9", "label": "wins"},
    ]})
    assert deck.slides[0].component == "big-number"
    assert notes


def test_render_is_deterministic():
    def resolved():
        deck, _ = build_deck(_outline(DEMO.read_text()))
        return re.sub(r'"node_id": "[^"]*"', '"node_id": ""', resolve(deck).to_json())
    assert resolved() == resolved()


def test_unknown_component_is_a_clear_error():
    with pytest.raises(ValueError, match="unknown component"):
        build_deck({"slides": [{"component": "nope"}]})


def test_missing_slides_is_a_clear_error():
    with pytest.raises(ValueError, match="slides:"):
        build_deck({"theme": {}})


def test_missing_required_field_surfaces_schema_error():
    # big-number requires value+label; omitting them yields the friendly IR error
    with pytest.raises(ValueError, match="value"):
        build_deck({"slides": [{"component": "big-number"}]})
