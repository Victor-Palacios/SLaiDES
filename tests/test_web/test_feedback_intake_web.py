"""Tests for the web-feedback fold-in (scripts/feedback_intake_web.py).

Covers the verdict → comment mapping, positive-only filtering, unknown-component skipping,
and that processed inbox files are consumed. Operates entirely on tmp paths so it never
touches the repo's real FEEDBACK.yaml.
"""
import importlib.util
import json
from pathlib import Path

from slidekit.feedback import store

ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "feedback_intake_web", ROOT / "scripts" / "feedback_intake_web.py"
)
fiw = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fiw)


def _write(inbox: Path, name: str, record: dict) -> None:
    (inbox / name).write_text(json.dumps(record), encoding="utf-8")


def _setup(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    return inbox, tmp_path / "FEEDBACK.yaml", tmp_path / "FEEDBACK.md"


def test_verdicts_map_to_comments(tmp_path):
    inbox, fy, fm = _setup(tmp_path)
    _write(inbox, "a.json", {
        "submitted_at": "2026-07-02T10:00:00.000Z",
        "items": [
            {"component": "code", "verdict": "bad", "comment": "font too small", "severity": "high"},
            {"component": "timeline", "verdict": "good", "comment": "nice", "severity": "med"},
            {"component": "title-slide", "verdict": "bad", "comment": "", "severity": "low"},
        ],
    })
    summary = fiw.fold(inbox=inbox, feedback_yaml=fy, feedback_md=fm, write=True)
    assert summary["added"] == 3  # bad+comment, good+comment, and bad-without-comment
    fb = store.load(fy)
    by_comp = {c.component: c for c in fb.comments}
    assert by_comp["code"].comment == "👎 font too small"
    assert by_comp["code"].severity == "high"
    assert by_comp["timeline"].comment == "👍 nice"
    assert by_comp["title-slide"].comment == "👎 needs work"  # default text for empty bad
    assert all(c.status == "open" for c in fb.comments)
    assert fm.read_text(encoding="utf-8").startswith("# Layout feedback")


def test_bare_positive_not_recorded(tmp_path):
    inbox, fy, fm = _setup(tmp_path)
    _write(inbox, "a.json", {
        "submitted_at": "2026-07-02T10:00:00.000Z",
        "items": [{"component": "title-slide", "verdict": "good", "comment": "", "severity": "med"}],
    })
    summary = fiw.fold(inbox=inbox, feedback_yaml=fy, feedback_md=fm, write=True)
    assert summary["added"] == 0
    assert summary["positive_only"] == 1
    assert store.load(fy).comments == []


def test_unknown_component_skipped(tmp_path):
    inbox, fy, fm = _setup(tmp_path)
    _write(inbox, "a.json", {
        "submitted_at": "2026-07-02T10:00:00.000Z",
        "items": [
            {"component": "not-a-layout", "verdict": "bad", "comment": "x", "severity": "low"},
            {"component": "code", "verdict": "bad", "comment": "ok", "severity": "low"},
        ],
    })
    summary = fiw.fold(inbox=inbox, feedback_yaml=fy, feedback_md=fm, write=True)
    assert summary["skipped_unknown"] == ["not-a-layout"]
    assert summary["added"] == 1


def test_inbox_consumed_and_ids_sequential(tmp_path):
    inbox, fy, fm = _setup(tmp_path)
    _write(inbox, "1.json", {
        "submitted_at": "2026-07-01T10:00:00.000Z",
        "items": [{"component": "code", "verdict": "bad", "comment": "a", "severity": "low"}],
    })
    _write(inbox, "2.json", {
        "submitted_at": "2026-07-02T10:00:00.000Z",
        "items": [{"component": "timeline", "verdict": "note", "comment": "b", "severity": "med"}],
    })
    fiw.fold(inbox=inbox, feedback_yaml=fy, feedback_md=fm, write=True)
    assert list(inbox.glob("*.json")) == []
    ids = [c.id for c in store.load(fy).comments]
    assert ids == ["FB-001", "FB-002"]


def test_dry_run_leaves_everything(tmp_path):
    inbox, fy, fm = _setup(tmp_path)
    _write(inbox, "a.json", {
        "submitted_at": "2026-07-02T10:00:00.000Z",
        "items": [{"component": "code", "verdict": "bad", "comment": "x", "severity": "low"}],
    })
    fiw.fold(inbox=inbox, feedback_yaml=fy, feedback_md=fm, write=False)
    assert not fy.exists()
    assert len(list(inbox.glob("*.json"))) == 1
