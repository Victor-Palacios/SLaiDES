#!/usr/bin/env python3
"""Generate the example-deck inventory: examples/*.yaml -> docs/EXAMPLES_INDEX.md.

A single, machine-generated source of truth for "what's in examples/" — each deck's
slide count and component sequence — so the inventory can never silently rot (the
failure mode a hand-typed list invites). Mirrors scripts/render_board.py and
scripts/build_combined_pdf.py: deterministic (decks in sorted filename order, no
timestamps), with a --check mode and a sync test (tests/test_examples_index).

Usage:
  python scripts/build_examples_index.py            # (re)write docs/EXAMPLES_INDEX.md
  python scripts/build_examples_index.py --check     # verify it is in sync; non-zero if stale
"""
import sys
from pathlib import Path

from slidekit.ir import load

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
OUT = ROOT / "docs" / "EXAMPLES_INDEX.md"


def _decks():
    """(stem, [component, ...]) for every example deck, in sorted filename order."""
    for path in sorted(EXAMPLES_DIR.glob("*.yaml")):
        deck = load(path)
        yield path.stem, [s.component for s in deck.slides]


def render() -> str:
    rows = list(_decks())
    specimens = [r for r in rows if len(r[1]) == 1]
    showcases = [r for r in rows if len(r[1]) > 1]
    total_slides = sum(len(c) for _, c in rows)

    lines = [
        "# Example deck index",
        "",
        "_Generated from `examples/*.yaml` by `scripts/build_examples_index.py` — do not "
        "hand-edit; run the script and commit. A single-component **specimen** is one slide "
        "of just its component; a **showcase** is a multi-slide composition. A test "
        "(`tests/test_examples_index`) fails if this file drifts from the decks._",
        "",
        f"**{len(rows)}** decks · **{len(specimens)}** specimens · **{len(showcases)}** "
        f"showcases · **{total_slides}** slides total",
        "",
        "| Example | Slides | Kind | Components |",
        "|---|--:|---|---|",
    ]
    for stem, comps in rows:
        kind = "specimen" if len(comps) == 1 else "showcase"
        lines.append(f"| `{stem}.yaml` | {len(comps)} | {kind} | {' → '.join(comps)} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list) -> int:
    out = render()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != out:
            print(
                "docs/EXAMPLES_INDEX.md is out of sync with examples/ — run "
                "`python scripts/build_examples_index.py`",
                file=sys.stderr,
            )
            return 1
        print("docs/EXAMPLES_INDEX.md in sync.")
        return 0
    OUT.write_text(out, encoding="utf-8")
    n = len(list(EXAMPLES_DIR.glob("*.yaml")))
    print(f"wrote {OUT.relative_to(ROOT)} ({n} decks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
