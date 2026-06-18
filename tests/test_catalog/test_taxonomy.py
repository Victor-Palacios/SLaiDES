"""docs/LAYOUT_TAXONOMY.md must stay in sync with the registry."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "build_layout_taxonomy", ROOT / "scripts" / "build_layout_taxonomy.py"
)
blt = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(blt)


def test_render_is_deterministic():
    assert blt.render() == blt.render()


def test_taxonomy_in_sync():
    committed = blt.OUT.read_text(encoding="utf-8")
    assert committed == blt.render(), (
        "docs/LAYOUT_TAXONOMY.md is stale — run `python scripts/build_layout_taxonomy.py`"
    )
