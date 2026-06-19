"""Guards for the operator layout-feedback loop.

Mirrors the board's generated-file pattern: FEEDBACK.md and the issue form are generated
and committed, and tests assert they stay in sync with their sources (FEEDBACK.yaml and
the catalog) so neither can silently drift. Also covers the store schema, id/date merge
behaviour, and the issue-form parser the intake workflow relies on.
"""
import importlib.util
from pathlib import Path

import pytest
import yaml

from slidekit.catalog.registry import catalog
from slidekit.feedback import store
from slidekit.feedback.intake import FeedbackParseError, parse_issue_form

ROOT = Path(__file__).resolve().parent.parent.parent


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render_feedback = _load_script("render_feedback")
build_feedback_form = _load_script("build_feedback_form")


# ── source-of-truth + generated-file sync ──────────────────────────────────────────

def test_feedback_yaml_validates():
    fb = store.load()
    assert fb.version == 1


def test_render_is_deterministic():
    fb = store.load()
    assert store.render_markdown(fb) == store.render_markdown(fb)


def test_feedback_md_in_sync():
    fb = store.load()
    committed = (ROOT / "FEEDBACK.md").read_text(encoding="utf-8")
    assert committed == store.render_markdown(fb), (
        "FEEDBACK.md is stale — run `python scripts/render_feedback.py` and commit it"
    )


def test_issue_form_in_sync_with_catalog():
    committed = (ROOT / ".github" / "ISSUE_TEMPLATE" / "layout-feedback.yml").read_text(
        encoding="utf-8"
    )
    assert committed == build_feedback_form.render(), (
        "layout-feedback.yml is stale — run `python scripts/build_feedback_form.py`"
    )


def test_form_dropdown_lists_exactly_the_catalog():
    form = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / "layout-feedback.yml").read_text("utf-8")
    )
    dropdown = next(b for b in form["body"] if b.get("id") == "component")
    assert dropdown["attributes"]["options"] == sorted(catalog())


# ── schema validation ───────────────────────────────────────────────────────────────

def _comment(**kw):
    base = dict(id="FB-001", component="big-number", comment="x")
    base.update(kw)
    return store.Comment(**base)


def test_known_component_required():
    with pytest.raises(Exception):
        _comment(component="not-a-layout")


def test_bad_status_rejected():
    with pytest.raises(Exception):
        _comment(status="urgent")


def test_bad_severity_rejected():
    with pytest.raises(Exception):
        _comment(severity="critical")


def test_duplicate_ids_rejected():
    with pytest.raises(Exception):
        store.Feedback(comments=[_comment(), _comment()])


# ── merge: sequential ids, preserved history, stamped dates ─────────────────────────

def test_merge_assigns_sequential_ids_and_dates():
    fb = store.Feedback()
    fb = store.merge(fb, [{"component": "big-number", "comment": "lift the value"}],
                     today="2026-06-19")
    fb = store.merge(fb, [{"component": "funnel", "comment": "tiers too tight",
                           "severity": "high"}], today="2026-06-20")
    assert [c.id for c in fb.comments] == ["FB-001", "FB-002"]
    assert fb.comments[0].created == "2026-06-19" and fb.comments[0].status == "open"
    assert fb.comments[1].severity == "high"
    # family is filled from the registry
    assert fb.comments[0].family == catalog()["big-number"].family


def test_merge_preserves_existing_comments():
    fb = store.merge(store.Feedback(), [{"component": "agenda", "comment": "a"}],
                     today="2026-06-19")
    fb.comments[0].status = "done"
    fb2 = store.merge(fb, [{"component": "swot", "comment": "b"}], today="2026-06-19")
    assert fb2.comments[0].status == "done"  # untouched
    assert fb2.comments[1].id == "FB-002"


def test_dumps_roundtrips():
    fb = store.merge(store.Feedback(), [{"component": "pyramid", "comment": "hi"}],
                     today="2026-06-19")
    again = store.Feedback.model_validate(yaml.safe_load(store.dumps(fb)))
    assert again.comments[0].component == "pyramid"


# ── issue-form parser ───────────────────────────────────────────────────────────────

_BODY = """### Layout

big-number

### Your comment

The hero value sits too low; lift it to the optical centre.

### Severity

high
"""


def test_parse_issue_form_happy_path():
    item = parse_issue_form(_BODY)
    assert item == {
        "component": "big-number",
        "comment": "The hero value sits too low; lift it to the optical centre.",
        "severity": "high",
    }


def test_parse_no_response_severity_defaults_to_med():
    body = "### Layout\n\nfunnel\n\n### Your comment\n\ntoo tight\n\n### Severity\n\n_No response_\n"
    assert parse_issue_form(body)["severity"] == "med"


def test_parse_unknown_component_raises():
    body = "### Layout\n\nnot-a-layout\n\n### Your comment\n\nhi\n"
    with pytest.raises(FeedbackParseError):
        parse_issue_form(body)


def test_parse_missing_comment_raises():
    body = "### Layout\n\nbig-number\n\n### Your comment\n\n_No response_\n"
    with pytest.raises(FeedbackParseError):
        parse_issue_form(body)


def test_parse_missing_layout_raises():
    with pytest.raises(FeedbackParseError):
        parse_issue_form("### Your comment\n\nsomething\n")
