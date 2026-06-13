"""slidekit CLI — build, lint, and inspect slide decks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="slidekit",
        description="Agent-first slide builder with deterministic layout verification",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # slidekit build
    build_p = sub.add_parser("build", help="Build a deck YAML → .pptx")
    build_p.add_argument("deck", help="Path to deck.yaml")
    build_p.add_argument("-o", "--output", default=None, help="Output .pptx path")

    # slidekit layout
    layout_p = sub.add_parser("layout", help="Resolve layout geometry")
    layout_p.add_argument("deck", help="Path to deck.yaml")
    layout_p.add_argument("--json", action="store_true", help="Print resolved JSON")

    # slidekit schema
    schema_p = sub.add_parser("schema", help="Export JSON Schema for the IR")
    schema_p.add_argument("-o", "--output", default="slidekit-schema.json")

    # slidekit new
    new_p = sub.add_parser("new", help="Scaffold a new deck from a template")
    new_p.add_argument("--template", default="title-slide", help="Component mix template")
    new_p.add_argument("-o", "--output", default="deck.yaml")

    args = parser.parse_args()

    if args.command == "build":
        _cmd_build(args)
    elif args.command == "layout":
        _cmd_layout(args)
    elif args.command == "schema":
        _cmd_schema(args)
    elif args.command == "new":
        _cmd_new(args)


def _cmd_build(args: argparse.Namespace) -> None:
    from slidekit.ir import load

    try:
        deck = load(args.deck)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    out = args.output or Path(args.deck).with_suffix(".pptx")
    # Phase 3 + 5 required — emit not yet implemented.
    print(f"[slidekit] build: IR validated ({len(deck.slides)} slides). Emitter not yet implemented.")
    sys.exit(0)


def _cmd_layout(args: argparse.Namespace) -> None:
    from slidekit.ir import load
    from slidekit.layout import resolve

    try:
        deck = load(args.deck)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    rd = resolve(deck)
    if args.json:
        print(rd.to_json())
    else:
        for slide in rd.slides:
            node_count = len(slide.nodes) + len(slide.chrome)
            print(f"  slide {slide.slide_index + 1}: {slide.component} — {node_count} nodes, "
                  f"page={slide.page_number}")
    sys.exit(0)


def _cmd_schema(args: argparse.Namespace) -> None:
    from slidekit.ir import write_schema

    path = write_schema(args.output)
    print(f"Schema written to {path}")


def _cmd_new(args: argparse.Namespace) -> None:
    # Phase 7 — scaffold not yet implemented; emit a minimal starter.
    template = f"""version: 1
theme:
  palette:
    primary: "#1B4F8A"
    surface: "#FFFFFF"
    accent: "#E84545"
    text: "#1A1A2E"
    muted: "#8A8A9A"
page_numbers:
  enabled: true
slides:
  - component: title-slide
    title: "Your Title Here"
    subtitle: "Your subtitle"
"""
    out = Path(args.output)
    out.write_text(template)
    print(f"Starter deck written to {out}")
