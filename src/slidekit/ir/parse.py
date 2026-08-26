"""YAML/JSON deck parsing with actionable error messages."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from slidekit.ir.models import DeckIR


def load(path: str | Path) -> DeckIR:
    """Parse a deck YAML or JSON file into a DeckIR model.

    Raises ValueError with YAML-path-prefixed error messages on any failure
    so the agent can identify the exact field and fix it.
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"Deck file not found: {p}")

    text = p.read_text()

    suffix = p.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            raw = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML parse error in {p}:\n  {exc}") from exc
    elif suffix == ".json":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON parse error in {p}:\n  {exc}") from exc
    else:
        raise ValueError(
            f"Unsupported file extension '{p.suffix}': use .yaml, .yml, or .json"
        )

    if not isinstance(raw, dict):
        raise ValueError(
            f"Deck file must be a YAML/JSON mapping (object), got {type(raw).__name__}"
        )

    try:
        return DeckIR.model_validate(raw)
    except ValidationError as exc:
        lines = [f"Validation failed for {p}:"]
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            msg = err["msg"].removeprefix("Value error, ")
            fix = _suggest_fix(err)
            lines.append(f"  {loc}: {msg}{fix}")
        raise ValueError("\n".join(lines)) from exc


def loads(text: str, *, fmt: str = "yaml") -> DeckIR:
    """Parse a deck from a string. fmt is 'yaml' or 'json'."""
    if fmt == "yaml":
        try:
            raw = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML parse error:\n  {exc}") from exc
    elif fmt == "json":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON parse error:\n  {exc}") from exc
    else:
        raise ValueError(f"Unknown format '{fmt}': use 'yaml' or 'json'")

    try:
        return DeckIR.model_validate(raw)
    except ValidationError as exc:
        lines = ["Validation failed:"]
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            msg = err["msg"].removeprefix("Value error, ")
            fix = _suggest_fix(err)
            lines.append(f"  {loc}: {msg}{fix}")
        raise ValueError("\n".join(lines)) from exc


def _suggest_fix(err: dict) -> str:
    """Return a short suggested-fix suffix for a pydantic error dict."""
    etype = err.get("type", "")
    loc = err.get("loc", ())

    if etype == "literal_error":
        return " — check spelling and refer to the component list in SKILL.md"
    if etype == "missing":
        field = loc[-1] if loc else "?"
        return f" — add the required field '{field}'"
    if "greater_than" in etype or "less_than" in etype or "ge" in etype or "le" in etype:
        return " — adjust the value to be within the allowed range"
    if "min_length" in etype:
        return " — provide at least one item in the list"
    if "hex" in str(err.get("msg", "")).lower() or "color" in str(err.get("msg", "")).lower():
        return " — use #RRGGBB hex format (e.g. #123A6B)"
    if "metric-safe" in str(err.get("msg", "")):
        return " — choose from: arial, calibri, cambria, times new roman, courier new, bookman old style, century schoolbook"
    return ""
