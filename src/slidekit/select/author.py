"""Assemble a validated DeckIR from a lean authoring outline.

An outline is a mapping with a `slides:` list (and optional `theme`/`page_numbers`); each
slide is either a chosen `component` + its fields, or a `recommend:` content-shape block
that the deterministic recommender resolves to a component. Theme/version default if absent.
The result is validated against the IR schema (friendly errors reused from slidekit.ir),
so an LLM can author with the lean format and slidekit renders deterministically — no vision.
"""
from __future__ import annotations

import yaml

from slidekit.catalog.registry import catalog, repeatable_field
from slidekit.ir import loads
from slidekit.ir.models import DeckIR
from slidekit.select.recommend import ContentFeatures, recommend


def build_deck(raw: dict) -> tuple[DeckIR, list[str]]:
    """(DeckIR, notes) from an outline mapping. Raises ValueError with a clear message."""
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        raise ValueError("outline must be a mapping with a 'slides:' list")

    cat = catalog()
    deck: dict = {"version": 1, "slides": []}
    for key in ("theme", "page_numbers"):
        if key in raw:
            deck[key] = raw[key]

    notes: list[str] = []
    for idx, sl in enumerate(raw["slides"], 1):
        if not isinstance(sl, dict):
            raise ValueError(f"slide {idx}: must be a mapping")
        slide = dict(sl)
        rec = slide.pop("recommend", None)
        if "component" not in slide:
            if not isinstance(rec, dict):
                raise ValueError(f"slide {idx}: needs a 'component' or a 'recommend:' block")
            try:
                sugg = recommend(ContentFeatures(**rec))[0]
            except TypeError as exc:
                raise ValueError(f"slide {idx}: bad recommend features: {exc}") from exc
            slide["component"] = sugg.component
            notes.append(f"slide {idx}: recommended '{sugg.component}' ({sugg.rationale})")
        comp = slide.get("component")
        if comp not in cat:
            raise ValueError(f"slide {idx}: unknown component '{comp}'")
        rf, cap = repeatable_field(comp), cat[comp].capacity
        if rf and cap and isinstance(slide.get(rf), list) and len(slide[rf]) > cap[1]:
            notes.append(
                f"slide {idx}: {comp} has {len(slide[rf])} {rf} (suggested max {cap[1]}) — "
                "lint will flag it if it overflows")
        deck["slides"].append(slide)

    return loads(yaml.safe_dump(deck)), notes
