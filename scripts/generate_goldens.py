#!/usr/bin/env python3
"""Regenerate golden layout JSON for every example deck.

Dev tooling — NOT part of the build loop. Run after an intentional layout change:

    python scripts/generate_goldens.py            # regenerate all
    python scripts/generate_goldens.py 11_bullet_list   # regenerate one (by stem)

Each example deck under examples/*.yaml is resolved and its ResolvedDeck JSON is
written to tests/test_layout/golden/<stem>.json. Node IDs depend on a global
counter and are stripped from golden comparisons, so byte-for-byte stability of
the id field is not required.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from slidekit.ir.parse import load  # noqa: E402
from slidekit.layout import resolve  # noqa: E402

EXAMPLES_DIR = ROOT / "examples"
GOLDEN_DIR = ROOT / "tests" / "test_layout" / "golden"


def main(argv: list[str]) -> int:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set(argv)
    written = 0
    for yaml_path in sorted(EXAMPLES_DIR.glob("*.yaml")):
        stem = yaml_path.stem
        if wanted and stem not in wanted:
            continue
        deck = load(yaml_path)
        rd = resolve(deck)
        out = GOLDEN_DIR / f"{stem}.json"
        out.write_text(rd.to_json() + "\n")
        print(f"wrote {out.relative_to(ROOT)}")
        written += 1
    if wanted and written == 0:
        print(f"no examples matched {wanted}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
