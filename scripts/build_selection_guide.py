#!/usr/bin/env python3
"""Generate the layout selection guide: registry -> docs/LAYOUT_SELECTION_GUIDE.md.

The human/LLM-readable "which layout do I use" guide — grouped by distinct family, each
component with its purpose, when-to-use, capacity, content shape, and required fields. An
LLM reads this (no vision) to pick a component per slide; `slidekit catalog --json` is the
machine form of the same data. Deterministic, with --check + a sync test.

Usage:
  python scripts/build_selection_guide.py            # (re)write the guide
  python scripts/build_selection_guide.py --check     # verify in sync; non-zero if stale
"""
import sys
from pathlib import Path

from slidekit.catalog.registry import catalog, distinct_families

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "LAYOUT_SELECTION_GUIDE.md"


def render() -> str:
    cat = catalog()
    fams = distinct_families()
    anchors = {l.family: l for l in cat.values() if l.role == "anchor"}

    lines = [
        "# Layout selection guide",
        "",
        "_Generated from `src/slidekit/catalog/registry.py` by "
        "`scripts/build_selection_guide.py` — do not hand-edit. The machine-readable form is "
        "`slidekit catalog --json`. A test (`tests/test_catalog`) fails if it drifts._",
        "",
        "Pick a component per slide from its **content shape** — no rendering or vision needed. "
        f"There are **{len(cat)} components** across **{len(fams)} distinct layouts**; variants "
        "share an anchor's geometry and differ only by marker / colour / orientation / fields.",
        "",
    ]
    for fam in fams:
        a = anchors[fam]
        members = sorted(
            [l for l in cat.values() if l.family == fam],
            key=lambda l: (l.role != "anchor", l.component),
        )
        lines.append(f"## {fam} — {a.purpose}")
        lines.append("")
        for lo in members:
            cap = f" · capacity {lo.capacity[0]}–{lo.capacity[1]}" if lo.capacity else ""
            anchor_tag = "" if lo.role == "anchor" else f" · variant of `{lo.variant_of}` ({lo.differs_by})"
            req = ", ".join(f"`{f}`" for f in lo.required_fields) or "—"
            lines.append(f"- **`{lo.component}`**{anchor_tag}{cap}")
            lines.append(f"  - use when: {lo.use_when}")
            lines.append(f"  - content shape: {lo.content_shape}")
            lines.append(f"  - required fields: {req}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list) -> int:
    out = render()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != out:
            print("docs/LAYOUT_SELECTION_GUIDE.md is out of sync — run "
                  "`python scripts/build_selection_guide.py`", file=sys.stderr)
            return 1
        print("docs/LAYOUT_SELECTION_GUIDE.md in sync.")
        return 0
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(catalog())} components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
