"""Golden-file tests for the layout engine.

Each example deck's resolved layout is committed as a JSON reference.
Any change to the layout engine will show up as a reviewable diff here.

Node IDs are stripped from comparisons because they depend on the
global counter which varies across test runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from slidekit.ir.parse import load
from slidekit.layout import resolve

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
GOLDEN_DIR = Path(__file__).parent / "golden"

_NODE_ID_RE = re.compile(r'"node_id": "[^"]*"')


def _strip_node_ids(text: str) -> str:
    return _NODE_ID_RE.sub('"node_id": ""', text)


def _get_example_names() -> list[str]:
    return [p.stem for p in sorted(EXAMPLES_DIR.glob("*.yaml"))]


@pytest.mark.parametrize("name", _get_example_names())
def test_golden_layout(name: str):
    """Resolved layout must match the committed golden file."""
    yaml_path = EXAMPLES_DIR / f"{name}.yaml"
    golden_path = GOLDEN_DIR / f"{name}.json"

    if not golden_path.exists():
        pytest.skip(f"No golden file for {name} — run generate_goldens.py to create")

    deck = load(yaml_path)
    rd = resolve(deck)

    actual = _strip_node_ids(rd.to_json())
    expected = _strip_node_ids(golden_path.read_text())

    actual_data = json.loads(actual)
    expected_data = json.loads(expected)

    assert actual_data == expected_data, (
        f"Layout changed for {name}. "
        f"Update golden files by re-running the golden generator if this is intentional."
    )
