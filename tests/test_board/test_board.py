"""Guards for the file-based task board (board.yaml -> BOARD.md).

Mirrors the layout golden-file pattern: BOARD.md is generated and committed, and a
test asserts it stays in sync with board.yaml so the board can never silently drift.
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "render_board", ROOT / "scripts" / "render_board.py"
)
rb = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rb)


def test_board_yaml_validates():
    board = rb.load_board()
    assert board.version == 1
    assert board.tasks, "board should have tasks"


def test_render_is_deterministic():
    board = rb.load_board()
    assert rb.render(board) == rb.render(board)


def test_board_md_in_sync():
    """The committed BOARD.md must equal a fresh render of board.yaml."""
    board = rb.load_board()
    committed = (ROOT / "ops" / "BOARD.md").read_text(encoding="utf-8")
    assert committed == rb.render(board), (
        "BOARD.md is stale — run `python scripts/render_board.py` and commit it"
    )


def test_unknown_column_rejected():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo", "done"],
                "epics": [],
                "tasks": [{"id": "T-1", "title": "x", "column": "nope"}],
            }
        )


def test_duplicate_id_rejected():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo"],
                "epics": [],
                "tasks": [
                    {"id": "T-1", "title": "a", "column": "todo"},
                    {"id": "T-1", "title": "b", "column": "todo"},
                ],
            }
        )


def test_unknown_epic_rejected():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo"],
                "epics": [{"id": "e1", "title": "E1"}],
                "tasks": [{"id": "T-1", "title": "a", "column": "todo", "epic": "ghost"}],
            }
        )
