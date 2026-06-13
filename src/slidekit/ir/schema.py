"""JSON Schema export for the DeckIR model."""

from __future__ import annotations

import json
from pathlib import Path

from slidekit.ir.models import DeckIR


def get_schema() -> dict:
    """Return the JSON Schema dict for DeckIR."""
    return DeckIR.model_json_schema()


def write_schema(path: str | Path = "slidekit-schema.json") -> Path:
    """Write the JSON Schema to a file and return its path."""
    p = Path(path)
    p.write_text(json.dumps(get_schema(), indent=2))
    return p
