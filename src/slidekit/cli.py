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
    build_p = sub.add_parser("build", help="Build a deck YAML → .pptx (or .pdf)")
    build_p.add_argument("deck", help="Path to deck.yaml")
    build_p.add_argument("-o", "--output", default=None, help="Output path (.pptx or .pdf)")
    build_p.add_argument(
        "--pdf",
        action="store_true",
        help="Output PDF (rendered via LibreOffice) instead of .pptx",
    )

    # slidekit layout
    layout_p = sub.add_parser("layout", help="Resolve layout geometry")
    layout_p.add_argument("deck", help="Path to deck.yaml")
    layout_p.add_argument("--json", action="store_true", help="Print resolved JSON")

    # slidekit schema
    schema_p = sub.add_parser("schema", help="Export JSON Schema for the IR")
    schema_p.add_argument("-o", "--output", default="slidekit-schema.json")

    # slidekit new
    from slidekit.scaffold import DEFAULT_TEMPLATE, list_templates

    new_p = sub.add_parser("new", help="Scaffold a themed starter deck from a template")
    new_p.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE,
        help=f"Component mix: {', '.join(list_templates())} (default: {DEFAULT_TEMPLATE})",
    )
    new_p.add_argument("-o", "--output", default="deck.yaml")
    new_p.add_argument(
        "--list", action="store_true", help="List available templates and exit"
    )

    # slidekit verify (Phase 6 CI-only render drift harness — NOT part of generation)
    verify_p = sub.add_parser(
        "verify",
        help="CI-only: render decks via LibreOffice and check pixels vs computed geometry",
    )
    verify_p.add_argument("decks", nargs="+", help="Deck YAML path(s) to verify")
    verify_p.add_argument("--dpi", type=int, default=None, help="Render DPI (default 150)")

    args = parser.parse_args()

    if args.command == "build":
        _cmd_build(args)
    elif args.command == "layout":
        _cmd_layout(args)
    elif args.command == "schema":
        _cmd_schema(args)
    elif args.command == "new":
        _cmd_new(args)
    elif args.command == "verify":
        _cmd_verify(args)


def _cmd_build(args: argparse.Namespace) -> None:
    from slidekit.ir import load
    from slidekit.layout import resolve
    from slidekit.lint import lint
    from slidekit.emit.pptx_emitter import emit_pptx

    try:
        deck = load(args.deck)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    rd = resolve(deck)

    issues = lint(deck, rd)
    errors = [i for i in issues if i.code.startswith("E_")]
    if errors:
        for issue in errors:
            print(json.dumps({
                "code": issue.code,
                "slide": issue.slide,
                "node_path": issue.node_path,
                "message": issue.message,
                "suggested_fix": issue.suggested_fix,
            }))
        sys.exit(1)

    if args.output:
        out = Path(args.output)
    elif args.pdf:
        out = Path(args.deck).with_suffix(".pdf")
    else:
        out = Path(args.deck).with_suffix(".pptx")

    if args.pdf or out.suffix.lower() == ".pdf":
        out = out.with_suffix(".pdf")
        _emit_pdf(deck, rd, out)
        print(f"[slidekit] built {out} ({len(deck.slides)} slides, lint-clean, PDF)")
    else:
        emit_pptx(deck, rd, out)
        print(f"[slidekit] built {out} ({len(deck.slides)} slides, lint-clean)")
    sys.exit(0)


def _emit_pdf(deck, rd, out_pdf: Path) -> None:
    """Emit a PDF natively from the resolved geometry (reportlab, no LibreOffice)."""
    from slidekit.emit.pdf_emitter import emit_pdf

    emit_pdf(deck, rd, out_pdf)


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


def _cmd_verify(args: argparse.Namespace) -> None:
    """Render decks and run pixel heuristics against computed geometry.

    CI-only drift detector — explicitly NOT part of deck generation. Prints a JSON
    report per deck and exits non-zero if any deck fails or the render tools are
    missing.
    """
    from slidekit.verify import VerifyConfig, tools_available, verify_deck_yaml

    ok, reason = tools_available()
    if not ok:
        print(json.dumps({"error": reason}), file=sys.stderr)
        sys.exit(2)

    cfg = VerifyConfig()
    if args.dpi:
        cfg.dpi = args.dpi

    all_passed = True
    for deck_path in args.decks:
        result = verify_deck_yaml(Path(deck_path), cfg=cfg)
        print(json.dumps(result.to_dict()))
        if not result.passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)


def _cmd_new(args: argparse.Namespace) -> None:
    """Scaffold a themed, lint-clean starter deck the agent edits in place."""
    from slidekit.scaffold import list_templates, render_template

    if getattr(args, "list", False):
        for name in list_templates():
            print(name)
        sys.exit(0)

    try:
        yaml_text = render_template(args.template)
    except KeyError:
        print(
            f"Unknown template '{args.template}'. Available: {', '.join(list_templates())}",
            file=sys.stderr,
        )
        sys.exit(1)

    out = Path(args.output)
    out.write_text(yaml_text)
    print(f"Starter deck ({args.template}) written to {out}")
    print("Edit the placeholder text, then: slidekit build " + str(out))
