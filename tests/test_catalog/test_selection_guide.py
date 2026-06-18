"""docs/LAYOUT_SELECTION_GUIDE.md must stay in sync with the registry."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "build_selection_guide", ROOT / "scripts" / "build_selection_guide.py"
)
bsg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bsg)


def test_render_is_deterministic():
    assert bsg.render() == bsg.render()


def test_guide_in_sync():
    committed = bsg.OUT.read_text(encoding="utf-8")
    assert committed == bsg.render(), (
        "docs/LAYOUT_SELECTION_GUIDE.md is stale — run `python scripts/build_selection_guide.py`"
    )
