#!/usr/bin/env python3
"""Generate the honest layout taxonomy: registry -> docs/LAYOUT_TAXONOMY.md.

Records the truth the component count obscures: the 40 IR components implement ~25
distinct geometric *skeletons* (families); the rest are styled variants of a family
anchor. Deterministic (families/components sorted), with a --check mode and a sync test
(mirrors scripts/render_board.py / scripts/build_examples_index.py).

Usage:
  python scripts/build_layout_taxonomy.py            # (re)write docs/LAYOUT_TAXONOMY.md
  python scripts/build_layout_taxonomy.py --check     # verify in sync; non-zero if stale
"""
import sys
from pathlib import Path

from slidekit.catalog.registry import catalog, distinct_families

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "LAYOUT_TAXONOMY.md"


def render() -> str:
    cat = catalog()
    fams = distinct_families()
    anchors = {l.family: l for l in cat.values() if l.role == "anchor"}
    n_variants = sum(1 for l in cat.values() if l.role == "variant")

    lines = [
        "# Layout taxonomy",
        "",
        "_Generated from `src/slidekit/catalog/registry.py` by "
        "`scripts/build_layout_taxonomy.py` — do not hand-edit. A test "
        "(`tests/test_catalog`) fails if it drifts._",
        "",
        f"**{len(cat)} components** implement **{len(fams)} distinct layout skeletons** "
        f"(families); **{n_variants}** are styled variants of a family anchor — same "
        "geometry, differing only by marker / colour / orientation / field-set. "
        "\"40 distinct layouts\" would overstate it; the honest figure is "
        f"**{len(fams)} distinct layouts**.",
        "",
        f"## Distinct layout families ({len(fams)})",
        "",
        "| Family | Anchor component | What the skeleton is |",
        "|---|---|---|",
    ]
    for fam in fams:
        a = anchors[fam]
        lines.append(f"| `{fam}` | `{a.component}` | {a.purpose} |")
    lines += [
        "",
        "## All components mapped to their skeleton",
        "",
        "| Component | Family | Role | Differs from anchor by |",
        "|---|---|---|---|",
    ]
    for key in sorted(cat):
        lo = cat[key]
        role = "**anchor**" if lo.role == "anchor" else "variant"
        differs = lo.differs_by or "—"
        lines.append(f"| `{key}` | `{lo.family}` | {role} | {differs} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list) -> int:
    out = render()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != out:
            print("docs/LAYOUT_TAXONOMY.md is out of sync — run "
                  "`python scripts/build_layout_taxonomy.py`", file=sys.stderr)
            return 1
        print("docs/LAYOUT_TAXONOMY.md in sync.")
        return 0
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(distinct_families())} families)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
