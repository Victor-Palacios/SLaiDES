"""Heading underlines span exactly the text they underline (operator 2026-10-21:
"the underline doesn't match up with the text it underlines").

Every emitter draws glyphs at rect.x with no left inset, so a rule under a heading
must start at the heading's rect.x and be the heading's measured bold width."""
from __future__ import annotations

import textwrap

import pytest

from slidekit.ir.parse import loads
from slidekit.layout import resolve
from slidekit.metrics.measure import measure_text

CASES = {
    "two-panel-list": """\
      - component: two-panel-list
        title: "What MCP Is"
        left: {title: "It is", items: ["A protocol"]}
        right: {title: "It is not", items: ["A model"]}
    """,
    "swot": """\
      - component: swot
        title: "SWOT"
        strengths: ["Fast"]
        weaknesses: ["Small"]
        opportunities: ["Growth"]
        threats: ["Rivals"]
    """,
}


def _pairs(slide, head_tag, rule_tag):
    heads = [n for n in slide.nodes if head_tag in n.node_id]
    rules = [n for n in slide.nodes if rule_tag in n.node_id]
    assert heads and len(heads) == len(rules)
    return zip(heads, rules)


@pytest.mark.parametrize("component", sorted(CASES))
def test_rule_starts_at_first_glyph_and_spans_the_heading(component):
    deck = loads("version: 1\nslides:\n" + textwrap.dedent(CASES[component]))
    slide = resolve(deck).slides[0]
    tag = "swot" if component == "swot" else ""
    for head, rule in _pairs(slide, f"{tag}_head", f"{tag}_rule"):
        width = measure_text(head.text_content, head.font, head.size_pt, bold=True)
        assert rule.rect.x == head.rect.x, (component, head.text_content)
        assert rule.rect.w == min(width, head.rect.w), (component, head.text_content)


def test_process_step_rule_spans_its_numeral():
    deck = loads("version: 1\nslides:\n" + textwrap.dedent("""\
      - component: process-steps
        title: "Steps"
        steps: [{label: "Map", body: "Draw it"}, {label: "Tool", body: "Name one"}]
    """))
    slide = resolve(deck).slides[0]
    for num, rule in _pairs(slide, "ps_num", "ps_rule"):
        width = measure_text(num.text_content, num.font, num.size_pt, bold=True)
        assert rule.rect.x == num.rect.x
        assert rule.rect.w == min(width, num.rect.w)
