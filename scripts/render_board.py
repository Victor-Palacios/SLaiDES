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
BOARD_YAML = ROOT / "ops" / "board.yaml"
BOARD_MD = ROOT / "ops" / "BOARD.md"

_PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}
_MOSCOW_RANK = {"must": 0, "should": 1, "could": 2, "wont": 3}

# Column -> the glyph used for a task's completion status in the sprint listings.
_STATUS_GLYPH = {
    "done": "✅",
    "blocked": "⛔",
    "in_progress": "◐",
    "todo": "☐",
    "backlog": "·",
}


class Epic(BaseModel):
    id: str
    title: str
    tag: Optional[str] = None  # short badge shown on cards; derived from id if absent

    @property
    def badge(self) -> str:
        return self.tag or self.id.upper()


class Sprint(BaseModel):
    """A delivery window. Sprints are closed in id order; S1 is the earliest."""

    id: str
    title: str
    goal: str
    starts: Optional[str] = None
    ends: Optional[str] = None
    status: str = "complete"

    @field_validator("starts", "ends", mode="before")
    @classmethod
    def _date_to_str(cls, v):
        return v.isoformat() if hasattr(v, "isoformat") else v


class Story(BaseModel):
    """A user story from docs/USER_STORIES.md, scheduled into a sprint.

    `status` is asserted here and cross-checked against the story's tasks by
    Board._check_refs, so a story cannot claim to be done while work under it is
    still open.
    """

    id: str
    title: str
    epic: Optional[str] = None
    priority: str = "should"  # MoSCoW
    sprint: Optional[str] = None
    status: str = "todo"  # done | partial | todo
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_enums(self) -> "Story":
        if self.priority not in _MOSCOW_RANK:
            raise ValueError(
                f"story {self.id}: priority '{self.priority}' must be one of "
                f"{sorted(_MOSCOW_RANK)}"
            )
        if self.status not in {"done", "partial", "todo"}:
            raise ValueError(
                f"story {self.id}: status '{self.status}' must be done|partial|todo"
            )
        return self


class Task(BaseModel):
    id: str
    title: str
    column: str
    epic: Optional[str] = None
    story: Optional[str] = None
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
    sprints: list[Sprint] = Field(default_factory=list)
    epics: list[Epic] = Field(default_factory=list)
    stories: list[Story] = Field(default_factory=list)
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
            if t.story is not None and t.story not in {s.id for s in self.stories}:
                raise ValueError(f"task {t.id}: story '{t.story}' is not defined")
            if t.sprint is not None and t.sprint not in {s.id for s in self.sprints}:
                raise ValueError(f"task {t.id}: sprint '{t.sprint}' is not defined")
        epic_ids = [e.id for e in self.epics]
        if len(epic_ids) != len(set(epic_ids)):
            raise ValueError("duplicate epic id")

        story_ids = [s.id for s in self.stories]
        if len(story_ids) != len(set(story_ids)):
            raise ValueError("duplicate story id")
        sprint_ids = [s.id for s in self.sprints]
        if len(sprint_ids) != len(set(sprint_ids)):
            raise ValueError("duplicate sprint id")

        for st in self.stories:
            if st.epic is not None and st.epic not in {e.id for e in self.epics}:
                raise ValueError(f"story {st.id}: epic '{st.epic}' is not defined")
            if st.sprint is not None and st.sprint not in {s.id for s in self.sprints}:
                raise ValueError(f"story {st.id}: sprint '{st.sprint}' is not defined")
            # A story's claimed status must match the state of its own tasks — the
            # board cannot report a story delivered while its work is still open.
            own = [t for t in self.tasks if t.story == st.id]
            if own:
                n_done = sum(1 for t in own if t.column == "done")
                if st.status == "done" and n_done != len(own):
                    raise ValueError(
                        f"story {st.id}: status 'done' but {len(own) - n_done} of "
                        f"{len(own)} tasks are not done"
                    )
                if st.status == "todo" and n_done:
                    raise ValueError(
                        f"story {st.id}: status 'todo' but {n_done} tasks are done"
                    )
                if st.status == "partial" and (n_done == 0 or n_done == len(own)):
                    raise ValueError(
                        f"story {st.id}: status 'partial' needs a mix of done and "
                        f"not-done tasks (has {n_done}/{len(own)} done)"
                    )
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
        "`board.yaml`, then re-render; do not hand-edit. Sprints, the user "
        "stories from `docs/USER_STORIES.md` scheduled into them, and the cards "
        "that delivered each; `PROGRESS.md` stays the acceptance ledger._"
    )
    lines.append("")
    counts = " · ".join(f"**{c}** {len(by_col[c])}" for c in board.columns)
    lines.append(f"{counts} · _last change {last_change}_")
    lines.append("")

    # Kanban: lanes as columns, cards stacked down each lane. Once every card is
    # done the grid is one very long column of finished work and says nothing the
    # counts above do not — so it is only drawn while something is still in flight.
    in_flight = [t for t in board.tasks if t.column != "done"]
    if not in_flight:
        lines.append(
            "_All cards are done — the kanban lanes are omitted. The sprint "
            "sections below are the record of the work._"
        )
        lines.append("")
        lines.extend(_render_epics(board))
        lines.extend(_render_backlog(board))
        lines.extend(_render_sprints(board))
        return "\n".join(lines) + "\n"

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

    lines.extend(_render_epics(board))
    lines.extend(_render_backlog(board))
    lines.extend(_render_sprints(board))

    return "\n".join(lines) + "\n"


def _render_epics(board: Board) -> list[str]:
    """Per-epic progress. A task's epic comes from its story when it has none."""
    if not board.epics:
        return []
    stories = {st.id: st for st in board.stories}

    def task_epic(t: Task) -> Optional[str]:
        if t.epic:
            return t.epic
        st = stories.get(t.story or "")
        return st.epic if st else None

    lines = ["## Epics", "", "| Epic | Done | Total |", "|---|---|---|"]
    for e in board.epics:
        et = [t for t in board.tasks if task_epic(t) == e.id]
        done = sum(1 for t in et if t.column == "done")
        lines.append(f"| {e.title} | {done} | {len(et)} |")
    lines.append("")
    return lines


def _story_progress(board: Board, story_id: str) -> tuple[int, int]:
    own = [t for t in board.tasks if t.story == story_id]
    return sum(1 for t in own if t.column == "done"), len(own)


_STORY_STATUS_LABEL = {"done": "✅ done", "partial": "◐ partial", "todo": "☐ todo"}


def _render_backlog(board: Board) -> list[str]:
    """The product backlog: every story, ordered by MoSCoW then id."""
    if not board.stories:
        return []
    epics = {e.id: e for e in board.epics}
    lines = ["## Product backlog", ""]
    lines.append(
        "_Every user story from `docs/USER_STORIES.md`, ordered by MoSCoW "
        "priority. `Tasks` counts delivered / total cards under the story._"
    )
    lines.append("")
    lines.append("| Story | Epic | Priority | Sprint | Status | Tasks |")
    lines.append("|---|---|---|---|---|---|")
    for st in sorted(board.stories, key=lambda s: (_MOSCOW_RANK[s.priority], s.id)):
        done, total = _story_progress(board, st.id)
        epic = epics[st.epic].badge if st.epic in epics else "—"
        lines.append(
            f"| **{st.id}** {st.title} | {epic} | {st.priority.title()} | "
            f"{st.sprint or '—'} | {_STORY_STATUS_LABEL[st.status]} | {done}/{total} |"
        )
    lines.append("")
    return lines


def _task_sprint(board: Board, t: Task) -> Optional[str]:
    """A card's sprint: its own if set, else the sprint of the story it delivers.

    Keeping the story as the single owner of scheduling means a card can never
    disagree with its story about which sprint delivered it.
    """
    if t.sprint:
        return t.sprint
    st = {x.id: x for x in board.stories}.get(t.story or "")
    return st.sprint if st else None


def _render_sprints(board: Board) -> list[str]:
    """One section per sprint: its stories, and the tasks that delivered each."""
    if not board.sprints:
        return []
    lines = ["## Sprints", ""]
    lines.append("| Sprint | Window | Stories | Tasks done |")
    lines.append("|---|---|---|---|")
    for sp in board.sprints:
        sts = [st for st in board.stories if st.sprint == sp.id]
        tks = [t for t in board.tasks if _task_sprint(board, t) == sp.id]
        done = sum(1 for t in tks if t.column == "done")
        window = f"{sp.starts or '—'} → {sp.ends or '—'}"
        lines.append(f"| **{sp.id}** {sp.title} | {window} | {len(sts)} | {done}/{len(tks)} |")
    lines.append("")

    for sp in board.sprints:
        sts = sorted(
            (st for st in board.stories if st.sprint == sp.id),
            key=lambda s: (_MOSCOW_RANK[s.priority], s.id),
        )
        tks = [t for t in board.tasks if _task_sprint(board, t) == sp.id]
        done = sum(1 for t in tks if t.column == "done")
        lines.append(f"### {sp.id} — {sp.title}")
        lines.append("")
        lines.append(f"_{sp.goal}_")
        lines.append("")
        lines.append(
            f"**{sp.starts or '—'} → {sp.ends or '—'}** · {len(sts)} stories · "
            f"{done}/{len(tks)} tasks done · _{sp.status}_"
        )
        lines.append("")
        for st in sts:
            s_done, s_total = _story_progress(board, st.id)
            lines.append(
                f"**{st.id} · {st.title}** — {_STORY_STATUS_LABEL[st.status]} "
                f"({s_done}/{s_total} tasks)"
            )
            lines.append("")
            own = sorted(
                (t for t in board.tasks if t.story == st.id), key=lambda t: t.id
            )
            for t in own:
                glyph = _STATUS_GLYPH.get(t.column, "·")
                note = f" — {t.notes}" if t.column != "done" and t.notes else ""
                title = t.title.replace("|", "/")
                lines.append(f"- {glyph} `{t.id}` {title}{note}")
            if not own:
                lines.append("- _(no cards recorded)_")
            lines.append("")
    return lines


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
