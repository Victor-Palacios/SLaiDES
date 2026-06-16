#!/usr/bin/env python3
"""Render the agile task board: board.yaml (source of truth) -> BOARD.md (kanban).

The board is the active/sprint kanban view of the work; PROGRESS.md stays the
canonical phase/acceptance ledger. board.yaml is hand/agent-edited; BOARD.md is
generated and committed so GitHub renders a readable board.

Usage:
  python scripts/render_board.py            # validate + (re)write BOARD.md
  python scripts/render_board.py --check     # validate only; non-zero exit on problems

Deterministic by construction: cards are sorted (column order, priority, id) and the
"last change" line uses max(task.updated) from the data — never a wall-clock time —
so re-rendering an unchanged board.yaml yields a byte-identical BOARD.md. A test
(tests/test_board) asserts BOARD.md stays in sync, the same spirit as the layout
golden files.
"""
import sys
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

ROOT = Path(__file__).resolve().parent.parent
BOARD_YAML = ROOT / "board.yaml"
BOARD_MD = ROOT / "BOARD.md"

_PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}


class Epic(BaseModel):
    id: str
    title: str
    tag: Optional[str] = None  # short badge shown on cards; derived from id if absent

    @property
    def badge(self) -> str:
        return self.tag or self.id.upper()


class Task(BaseModel):
    id: str
    title: str
    column: str
    epic: Optional[str] = None
    priority: str = "med"
    sprint: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("created", "updated", mode="before")
    @classmethod
    def _date_to_str(cls, v):
        # PyYAML parses a bare `2026-06-16` as a datetime.date; accept either form.
        return v.isoformat() if hasattr(v, "isoformat") else v

    @model_validator(mode="after")
    def _check_priority(self) -> "Task":
        if self.priority not in _PRIORITY_RANK:
            raise ValueError(
                f"task {self.id}: priority '{self.priority}' must be one of "
                f"{sorted(_PRIORITY_RANK)}"
            )
        return self


class Board(BaseModel):
    version: int
    columns: list[str] = Field(min_length=1)
    epics: list[Epic] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_refs(self) -> "Board":
        seen: set[str] = set()
        for t in self.tasks:
            if t.id in seen:
                raise ValueError(f"duplicate task id '{t.id}'")
            seen.add(t.id)
            if t.column not in self.columns:
                raise ValueError(
                    f"task {t.id}: column '{t.column}' is not one of {self.columns}"
                )
            if t.epic is not None and t.epic not in {e.id for e in self.epics}:
                raise ValueError(f"task {t.id}: epic '{t.epic}' is not defined")
        epic_ids = [e.id for e in self.epics]
        if len(epic_ids) != len(set(epic_ids)):
            raise ValueError("duplicate epic id")
        return self


def load_board(path: Path = BOARD_YAML) -> Board:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Board.model_validate(data)


def _cell(task: Task, epics: dict[str, Epic]) -> str:
    """One card as a single table-cell string (no pipes/newlines)."""
    bits = [f"**{task.id}** {task.title}"]
    if task.epic and task.epic in epics:
        bits.append(f"_{epics[task.epic].badge}_")
    if task.priority == "high":
        bits.append("`high`")
    if task.column == "blocked" and task.notes:
        bits.append(f"⚠ {task.notes}")
    return " · ".join(bits).replace("|", "/").replace("\n", " ")


def _sort_key(t: Task) -> tuple:
    return (_PRIORITY_RANK[t.priority], t.id)


def render(board: Board) -> str:
    epics = {e.id: e for e in board.epics}
    by_col: dict[str, list[Task]] = {c: [] for c in board.columns}
    for t in board.tasks:
        by_col[t.column].append(t)
    for c in by_col:
        by_col[c].sort(key=_sort_key)

    updates = [t.updated for t in board.tasks if t.updated]
    last_change = max(updates) if updates else "—"

    lines: list[str] = []
    lines.append("# Board — slidekit")
    lines.append("")
    lines.append(
        "_Generated from `board.yaml` by `scripts/render_board.py` — edit "
        "`board.yaml`, then re-render; do not hand-edit. The kanban view of the "
        "work; `PROGRESS.md` stays the acceptance ledger._"
    )
    lines.append("")
    counts = " · ".join(f"**{c}** {len(by_col[c])}" for c in board.columns)
    lines.append(f"{counts} · _last change {last_change}_")
    lines.append("")

    # Kanban: lanes as columns, cards stacked down each lane.
    headers = [f"{c.replace('_', ' ').title()} ({len(by_col[c])})" for c in board.columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(board.columns)) + "|")
    depth = max((len(by_col[c]) for c in board.columns), default=0)
    for i in range(depth):
        row = []
        for c in board.columns:
            tasks = by_col[c]
            row.append(_cell(tasks[i], epics) if i < len(tasks) else "")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Per-epic progress (done / total).
    if board.epics:
        lines.append("## Epics")
        lines.append("")
        lines.append("| Epic | Done | Total |")
        lines.append("|---|---|---|")
        for e in board.epics:
            et = [t for t in board.tasks if t.epic == e.id]
            done = sum(1 for t in et if t.column == "done")
            lines.append(f"| {e.title} | {done} | {len(et)} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    try:
        board = load_board()
    except Exception as exc:  # noqa: BLE001 — surface a clean message to the operator
        print(f"board.yaml invalid: {exc}", file=sys.stderr)
        return 1
    out = render(board)
    if check_only:
        current = BOARD_MD.read_text(encoding="utf-8") if BOARD_MD.exists() else ""
        if current != out:
            print(
                "BOARD.md is out of sync with board.yaml — run "
                "`python scripts/render_board.py`",
                file=sys.stderr,
            )
            return 1
        print("board.yaml valid and BOARD.md in sync.")
        return 0
    BOARD_MD.write_text(out, encoding="utf-8")
    print(f"wrote {BOARD_MD.relative_to(ROOT)} ({len(board.tasks)} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
