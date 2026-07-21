"""Tests for the web-feedback fold-in (scripts/feedback_intake_web.py).

Covers the verdict → FEEDBACK.yaml mapping, the review-state machine behind the website
(👍 approves a layout off the review page; 👎 flags it and snapshots the current preview
as the before/after "before"), unknown-component skipping, and inbox consumption.
Operates entirely on tmp paths so it never touches the repo's real FEEDBACK.yaml or
state.json.
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

_FRAG = {"width_px": 1280.0, "height_px": 720.0, "background": "#FFFFFF",
         "nodes_html": '<div class="node">v1</div>'}


def _write(path: Path, name: str, record: dict) -> None:
    (path / name).write_text(json.dumps(record), encoding="utf-8")


def _setup(tmp_path, previews_components=("code", "timeline", "title-slide", "agenda")):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    previews = tmp_path / "previews.json"
    previews.write_text(json.dumps({
        "components": [dict(component=c, **_FRAG) for c in previews_components]
    }), encoding="utf-8")
    return {
        "inbox": inbox,
        "feedback_yaml": tmp_path / "FEEDBACK.yaml",
        "feedback_md": tmp_path / "FEEDBACK.md",
        "state_json": tmp_path / "state.json",
        "previews_json": previews,
    }


def _record(items, when="2026-07-02T10:00:00.000Z"):
    return {"submitted_at": when, "items": items}


def test_verdicts_map_to_comments(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "bad", "comment": "font too small", "severity": "high"},
        {"component": "timeline", "verdict": "good", "comment": "nice", "severity": "med"},
        {"component": "title-slide", "verdict": "bad", "comment": "", "severity": "low"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 3
    fb = store.load(p["feedback_yaml"])
    by_comp = {c.component: c for c in fb.comments}
    assert by_comp["code"].comment == "👎 font too small"
    assert by_comp["timeline"].comment == "👍 nice"
    assert by_comp["title-slide"].comment == "👎 needs work"
    assert all(c.status == "open" for c in fb.comments)


def test_good_approves_and_leaves_review_queue(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "title-slide", "verdict": "good", "comment": "", "severity": "med"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 0                # bare 👍 adds no work item
    assert summary["positive_only"] == 1
    assert summary["approved"] == ["title-slide"]
    st = json.loads(p["state_json"].read_text())["components"]
    assert st["title-slide"] == {"status": "approved", "date": "2026-07-02"}


def test_bad_flags_and_snapshots_before(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "bad", "comment": "too dark", "severity": "med"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["flagged"] == ["code"]
    st = json.loads(p["state_json"].read_text())["components"]["code"]
    assert st["status"] == "flagged"
    assert st["comment"] == "too dark"
    assert st["before"] == _FRAG            # snapshot of the CURRENT preview at flag time


def test_good_clears_an_earlier_flag(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "1.json", _record(
        [{"component": "code", "verdict": "bad", "comment": "x", "severity": "med"}],
        when="2026-07-01T10:00:00.000Z"))
    fiw.fold(**p, write=True)
    _write(p["inbox"], "2.json", _record(
        [{"component": "code", "verdict": "good", "comment": "", "severity": "med"}]))
    fiw.fold(**p, write=True)
    st = json.loads(p["state_json"].read_text())["components"]["code"]
    assert st == {"status": "approved", "date": "2026-07-02"}   # flag + before gone


def test_repeat_bad_refreshes_snapshot(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "1.json", _record(
        [{"component": "code", "verdict": "bad", "comment": "v1 bad", "severity": "med"}],
        when="2026-07-01T10:00:00.000Z"))
    fiw.fold(**p, write=True)
    # A fix lands: previews.json changes.
    frag2 = dict(_FRAG, nodes_html='<div class="node">v2</div>')
    p["previews_json"].write_text(json.dumps(
        {"components": [dict(component="code", **frag2)]}), encoding="utf-8")
    _write(p["inbox"], "2.json", _record(
        [{"component": "code", "verdict": "bad", "comment": "still bad", "severity": "med"}]))
    fiw.fold(**p, write=True)
    st = json.loads(p["state_json"].read_text())["components"]["code"]
    assert st["comment"] == "still bad"
    assert st["before"]["nodes_html"] == '<div class="node">v2</div>'  # refreshed


def test_note_leaves_state_untouched(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "agenda", "verdict": "note", "comment": "thinking about this", "severity": "low"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 1                       # noted in FEEDBACK.yaml
    st = json.loads(p["state_json"].read_text())["components"]
    assert "agenda" not in st                          # but not approved/flagged


def test_stale_state_for_deleted_layouts_dropped(tmp_path):
    p = _setup(tmp_path)
    p["state_json"].write_text(fiw.dumps_state({
        "code": {"status": "approved", "date": "2026-07-01"},
        "retired-layout": {"status": "approved", "date": "2026-07-01"},
    }), encoding="utf-8")
    _write(p["inbox"], "a.json", _record(
        [{"component": "timeline", "verdict": "good", "comment": "", "severity": "med"}]))
    summary = fiw.fold(**p, write=True)
    assert summary["state_dropped"] == ["retired-layout"]
    st = json.loads(p["state_json"].read_text())["components"]
    assert set(st) == {"code", "timeline"}


def test_unknown_component_skipped(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "not-a-layout", "verdict": "bad", "comment": "x", "severity": "low"},
        {"component": "code", "verdict": "bad", "comment": "ok", "severity": "low"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["skipped_unknown"] == ["not-a-layout"]
    assert summary["added"] == 1


def test_inbox_consumed_and_ids_sequential(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "1.json", _record(
        [{"component": "code", "verdict": "bad", "comment": "a", "severity": "low"}],
        when="2026-07-01T10:00:00.000Z"))
    _write(p["inbox"], "2.json", _record(
        [{"component": "timeline", "verdict": "note", "comment": "b", "severity": "med"}]))
    fiw.fold(**p, write=True)
    assert list(p["inbox"].glob("*.json")) == []
    ids = [c.id for c in store.load(p["feedback_yaml"]).comments]
    assert ids == ["FB-001", "FB-002"]


# ── scope routing: deck-review (slide) vs layout ────────────────────────────────────

def test_slide_scope_records_deck_and_slide_but_not_layout_state(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "bad", "comment": "tighten indent",
         "severity": "med", "scope": "slide", "deck": "demo-5", "slide": 3},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 1
    c = store.load(p["feedback_yaml"]).comments[0]
    assert (c.scope, c.deck, c.slide) == ("slide", "demo-5", 3)
    assert c.comment == "👎 tighten indent"
    # A slide-scoped mark must NOT flag/approve the reusable layout.
    assert summary["flagged"] == [] and summary["approved"] == []
    state = json.loads(p["state_json"].read_text())["components"]
    assert "code" not in state


def test_layout_scope_from_deck_page_still_flags_layout(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "bad", "comment": "too dark everywhere",
         "severity": "med", "scope": "layout"},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["flagged"] == ["code"]
    c = store.load(p["feedback_yaml"]).comments[0]
    assert c.scope == "layout" and c.deck is None


def test_malformed_slide_scope_degrades_to_layout(tmp_path):
    """Missing deck coordinates must not crash the batch — they fall back to layout."""
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "note", "comment": "hmm",
         "scope": "slide"},                       # no deck/slide
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 1
    c = store.load(p["feedback_yaml"]).comments[0]
    assert c.scope == "layout" and c.deck is None and c.slide is None


def test_slide_scope_bare_good_is_positive_only(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record([
        {"component": "code", "verdict": "good", "comment": "",
         "scope": "slide", "deck": "demo-5", "slide": 1},
    ]))
    summary = fiw.fold(**p, write=True)
    assert summary["added"] == 0 and summary["positive_only"] == 1
    assert json.loads(p["state_json"].read_text())["components"] == {}


def test_dry_run_leaves_everything(tmp_path):
    p = _setup(tmp_path)
    _write(p["inbox"], "a.json", _record(
        [{"component": "code", "verdict": "bad", "comment": "x", "severity": "low"}]))
    fiw.fold(**p, write=False)
    assert not p["feedback_yaml"].exists()
    assert not p["state_json"].exists()
    assert len(list(p["inbox"].glob("*.json"))) == 1


# ── committed state.json stays valid ────────────────────────────────────────────────

def test_committed_state_is_valid():
    from slidekit.catalog.registry import catalog
    committed = json.loads((ROOT / "web" / "data" / "state.json").read_text(encoding="utf-8"))
    comps = committed["components"]
    assert set(comps) <= set(catalog()), "state.json references a deleted layout"
    for name, entry in comps.items():
        assert entry["status"] in ("approved", "flagged"), name
        assert entry.get("date"), name
        if entry["status"] == "flagged":
            assert entry.get("comment"), f"{name}: flagged without a comment"
            before = entry.get("before")
            if before is not None:
                assert set(before) == {"width_px", "height_px", "background", "nodes_html"}
    # Serialisation is canonical (sorted, stable) so CI commits diff cleanly.
    assert (ROOT / "web" / "data" / "state.json").read_text(encoding="utf-8") == \
        fiw.dumps_state(comps)
