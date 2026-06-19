"""FEEDBACK.yaml — schema, load/merge/save, and markdown render.

FEEDBACK.yaml is the single source of truth for operator layout feedback; FEEDBACK.md is
generated from it (and kept in sync by a test) so GitHub renders a readable view. Each
comment names a real `component` (validated against the catalog registry, so feedback can
never reference a non-existent layout) and carries a `status` the nightly drives:

    open    -> actionable; the nightly queues a board task and addresses it
    done    -> addressed (notes carry the commit ref)
    wontfix -> consciously declined (notes carry the reason)

The schema mirrors the board's: small, validated, deterministic to serialise so diffs stay
clean.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from slidekit.catalog.registry import catalog

ROOT = Path(__file__).resolve().parents[3]
FEEDBACK_YAML = ROOT / "FEEDBACK.yaml"
FEEDBACK_MD = ROOT / "FEEDBACK.md"

_STATUSES = ("open", "done", "wontfix")
_SEVERITIES = ("low", "med", "high")
_STATUS_RANK = {s: i for i, s in enumerate(_STATUSES)}


def known_components() -> set[str]:
    """The set of valid component keys feedback may reference (from the registry)."""
    return set(catalog())


class Comment(BaseModel):
    id: str
    component: str
    family: Optional[str] = None
    status: str = "open"
    severity: str = "med"
    comment: str
    created: Optional[str] = None
    updated: Optional[str] = None
    source: Optional[str] = None  # provenance, e.g. "issue #12"
    notes: Optional[str] = ""

    @field_validator("created", "updated", mode="before")
    @classmethod
    def _date_to_str(cls, v):
        # PyYAML parses a bare `2026-06-19` as a datetime.date; accept either form.
        return v.isoformat() if hasattr(v, "isoformat") else v

    @model_validator(mode="after")
    def _check(self) -> "Comment":
        if self.status not in _STATUSES:
            raise ValueError(
                f"comment {self.id}: status '{self.status}' must be one of {list(_STATUSES)}"
            )
        if self.severity not in _SEVERITIES:
            raise ValueError(
                f"comment {self.id}: severity '{self.severity}' must be one of {list(_SEVERITIES)}"
            )
        if self.component not in known_components():
            raise ValueError(
                f"comment {self.id}: component '{self.component}' is not a known layout"
            )
        return self


class Feedback(BaseModel):
    version: int = 1
    comments: list[Comment] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> "Feedback":
        seen: set[str] = set()
        for c in self.comments:
            if c.id in seen:
                raise ValueError(f"duplicate comment id '{c.id}'")
            seen.add(c.id)
        return self


# ── load / save ──────────────────────────────────────────────────────────────────

def load(path: Path = FEEDBACK_YAML) -> Feedback:
    if not path.exists():
        return Feedback()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Feedback.model_validate(data)


_FIELD_ORDER = (
    "id", "component", "family", "status", "severity",
    "comment", "created", "updated", "source", "notes",
)


def _ordered(c: Comment) -> dict:
    d = c.model_dump()
    return {k: d[k] for k in _FIELD_ORDER}


def dumps(fb: Feedback) -> str:
    """Deterministic YAML serialisation (stable field order, comments by id)."""
    body = {
        "version": fb.version,
        "comments": [_ordered(c) for c in sorted(fb.comments, key=lambda c: c.id)],
    }
    return yaml.safe_dump(body, sort_keys=False, allow_unicode=True, width=10_000)


def save(fb: Feedback, path: Path = FEEDBACK_YAML) -> None:
    path.write_text(dumps(fb), encoding="utf-8")


# ── merge new comments ─────────────────────────────────────────────────────────────

def next_id(fb: Feedback) -> str:
    nums = [int(c.id.split("-")[1]) for c in fb.comments if c.id.startswith("FB-")]
    return f"FB-{(max(nums) + 1) if nums else 1:03d}"


def merge(fb: Feedback, new_items: list[dict], *, today: str) -> Feedback:
    """Append new comments, assigning sequential FB-NNN ids and today's dates.

    Each item is `{component, comment, severity?, source?}`. Existing comments are left
    untouched (the nightly/operator owns their status). Returns a new validated Feedback.
    """
    comments = list(fb.comments)
    acc = Feedback(version=fb.version, comments=comments)
    for item in new_items:
        fid = next_id(acc)
        comp = item["component"]
        lo = catalog().get(comp)
        c = Comment(
            id=fid,
            component=comp,
            family=lo.family if lo else None,
            status="open",
            severity=item.get("severity") or "med",
            comment=item["comment"],
            created=today,
            updated=today,
            source=item.get("source"),
            notes="",
        )
        comments.append(c)
        acc = Feedback(version=fb.version, comments=comments)
    return acc


# ── markdown render (FEEDBACK.md) ──────────────────────────────────────────────────

def _cell(s: Optional[str]) -> str:
    return (s or "").replace("|", "/").replace("\n", " ").strip()


def render_markdown(fb: Feedback) -> str:
    by_status: dict[str, list[Comment]] = {s: [] for s in _STATUSES}
    for c in fb.comments:
        by_status[c.status].append(c)
    for s in by_status:
        by_status[s].sort(key=lambda c: c.id)

    updates = [c.updated for c in fb.comments if c.updated]
    last_change = max(updates) if updates else "—"

    lines: list[str] = []
    lines.append("# Layout feedback — slidekit")
    lines.append("")
    lines.append(
        "_Generated from `FEEDBACK.yaml` by `scripts/render_feedback.py` — do not "
        "hand-edit. `FEEDBACK.yaml` is the source of truth; file new comments with the "
        "**Layout feedback** issue form (see the README). The nightly reads `open` items, "
        "queues them on the board, and marks them `done`._"
    )
    lines.append("")
    counts = " · ".join(f"**{s}** {len(by_status[s])}" for s in _STATUSES)
    lines.append(f"{counts} · _last change {last_change}_")
    lines.append("")

    if not fb.comments:
        lines.append("_No feedback yet._")
        return "\n".join(lines) + "\n"

    headings = {"open": "Open", "done": "Done", "wontfix": "Won't fix"}
    for s in _STATUSES:
        rows = by_status[s]
        if not rows:
            continue
        lines.append(f"## {headings[s]} ({len(rows)})")
        lines.append("")
        lines.append("| ID | Layout | Sev | Comment | Notes |")
        lines.append("|---|---|---|---|---|")
        for c in rows:
            lines.append(
                f"| {c.id} | {_cell(c.component)} | {_cell(c.severity)} | "
                f"{_cell(c.comment)} | {_cell(c.notes)} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"
