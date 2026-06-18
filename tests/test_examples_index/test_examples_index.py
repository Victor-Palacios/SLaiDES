"""Guard for the generated example inventory (docs/EXAMPLES_INDEX.md).

Same golden/sync spirit as the board and combined-PDF tests: the index is committed
and a test asserts it stays in sync with examples/, so it can never silently drift.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "build_examples_index", ROOT / "scripts" / "build_examples_index.py"
)
bei = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bei)


def test_render_is_deterministic():
    assert bei.render() == bei.render()


def test_index_in_sync_with_examples():
    committed = bei.OUT.read_text(encoding="utf-8")
    assert committed == bei.render(), (
        "docs/EXAMPLES_INDEX.md is stale — run `python scripts/build_examples_index.py`"
    )


def test_every_example_listed():
    listed = bei.render()
    for path in ROOT.glob("examples/*.yaml"):
        assert f"`{path.stem}.yaml`" in listed, f"{path.stem} missing from the index"
