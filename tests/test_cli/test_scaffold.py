"""Phase 7 — agent interface: scaffold templates and lint-error quality.

Two acceptance threads:
1. `slidekit new --template <mix>` scaffolds a themed deck that builds lint-clean.
2. Lint errors name the IR path and a concrete fix, so an agent can self-correct
   from the error text alone (no rendering).
"""
from __future__ import annotations

import pytest

from slidekit.ir import loads
from slidekit.layout import resolve
from slidekit.lint import lint
from slidekit.scaffold import list_templates, render_template, DEFAULT_TEMPLATE


# --- scaffold templates -----------------------------------------------------

def test_default_template_is_listed():
    assert DEFAULT_TEMPLATE in list_templates()


def test_templates_nonempty():
    assert set(list_templates()) >= {"title-slide", "standard", "comparison", "pitch"}


def test_unknown_template_raises():
    with pytest.raises(KeyError):
        render_template("does-not-exist")


@pytest.mark.parametrize("name", list_templates())
def test_template_builds_lint_clean(name):
    """ACCEPTANCE: every scaffold template parses, resolves, and has zero E_ errors."""
    deck = loads(render_template(name))
    rd = resolve(deck)
    errors = [i for i in lint(deck, rd) if i.code.startswith("E_")]
    assert not errors, (
        f"template '{name}' produced lint errors: "
        + ", ".join(f"{e.code}@{e.node_path}" for e in errors)
    )


@pytest.mark.parametrize("name", list_templates())
def test_template_has_theme_and_slides(name):
    deck = loads(render_template(name))
    assert deck.version == 1
    assert deck.theme.font in {"arial"}  # scaffolds default to a metric-safe font
    assert len(deck.slides) >= 1


# --- lint error quality -----------------------------------------------------

def _overflowing_deck():
    long = "supercalifragilistic" * 12  # one unbreakable token wider than any box
    return loads(
        f"""version: 1
slides:
  - component: two-column
    title: Overfull
    left:
      - type: text
        content: "{long}"
    right:
      - type: text
        content: short
"""
    )


def test_lint_error_names_path_and_fix():
    """ACCEPTANCE: each error carries a non-empty node_path and a concrete fix."""
    deck = _overflowing_deck()
    rd = resolve(deck)
    errors = [i for i in lint(deck, rd) if i.code.startswith("E_")]
    assert errors, "expected at least one E_ error from the overfull deck"
    for e in errors:
        assert e.node_path and e.node_path.strip(), f"{e.code} has empty node_path"
        assert e.suggested_fix and len(e.suggested_fix.strip()) >= 10, (
            f"{e.code} suggested_fix is not concrete: {e.suggested_fix!r}"
        )
        assert isinstance(e.slide, int) and e.slide >= 0
        # the fix should be actionable prose, not just the code echoed back
        assert e.suggested_fix.lower() != e.code.lower()


def test_lint_issue_serializes_with_required_keys():
    deck = _overflowing_deck()
    rd = resolve(deck)
    errors = [i for i in lint(deck, rd) if i.code.startswith("E_")]
    for e in errors:
        d = e.to_dict()
        assert {"code", "slide", "node_path", "message", "suggested_fix"} <= set(d)
