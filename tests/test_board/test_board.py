"""Guards for the file-based task board (board.yaml -> BOARD.md).

Mirrors the layout golden-file pattern: BOARD.md is generated and committed, and a
test asserts it stays in sync with board.yaml so the board can never silently drift.
"""

import importlib.util
import re
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


# ── sprints, stories and their cross-checks ──────────────────────────────────

USER_STORIES_MD = ROOT / "docs" / "USER_STORIES.md"


def test_board_has_three_closed_sprints():
    board = rb.load_board()
    assert len(board.sprints) == 3
    assert all(s.status == "complete" for s in board.sprints)


def test_every_story_is_scheduled_and_has_cards():
    board = rb.load_board()
    assert board.stories
    for story in board.stories:
        assert story.sprint, f"{story.id} is not scheduled into a sprint"
        assert story.epic, f"{story.id} has no epic"
        own = [t for t in board.tasks if t.story == story.id]
        assert own, f"{story.id} has no constituent tasks"


def test_every_task_belongs_to_a_story():
    board = rb.load_board()
    for task in board.tasks:
        assert task.story, f"{task.id} is not attached to a user story"


def test_board_covers_every_documented_user_story():
    """The board and docs/USER_STORIES.md must not drift apart."""
    documented = set(re.findall(r"^### (US-\d+)", USER_STORIES_MD.read_text(), re.M))
    on_board = {s.id for s in rb.load_board().stories}
    assert documented == on_board, (
        f"only in docs: {sorted(documented - on_board)}; "
        f"only on board: {sorted(on_board - documented)}"
    )


def test_work_is_spread_across_the_sprints():
    """No sprint may carry the bulk of the work — the split should be even."""
    board = rb.load_board()
    per = {
        s.id: len([t for t in board.tasks if rb._task_sprint(board, t) == s.id])
        for s in board.sprints
    }
    assert all(per.values()), f"a sprint has no cards: {per}"
    assert max(per.values()) <= 2 * min(per.values()), f"sprints are lopsided: {per}"


def test_story_cannot_claim_done_while_a_card_is_open():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo", "done"],
                "sprints": [{"id": "S1", "title": "s", "goal": "g"}],
                "epics": [{"id": "e1", "title": "E1"}],
                "stories": [
                    {"id": "US-01", "title": "x", "epic": "e1",
                     "priority": "must", "sprint": "S1", "status": "done"}
                ],
                "tasks": [
                    {"id": "T-1", "title": "a", "column": "done", "story": "US-01"},
                    {"id": "T-2", "title": "b", "column": "todo", "story": "US-01"},
                ],
            }
        )


def test_unknown_story_reference_rejected():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo"],
                "epics": [],
                "stories": [],
                "tasks": [{"id": "T-1", "title": "a", "column": "todo",
                           "story": "US-99"}],
            }
        )


def test_unknown_sprint_reference_rejected():
    with pytest.raises(Exception):
        rb.Board.model_validate(
            {
                "version": 1,
                "columns": ["todo"],
                "epics": [{"id": "e1", "title": "E1"}],
                "sprints": [],
                "stories": [{"id": "US-01", "title": "x", "epic": "e1",
                             "sprint": "S9", "status": "todo"}],
                "tasks": [],
            }
        )
