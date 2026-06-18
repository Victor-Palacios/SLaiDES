"""Phase 10 — `slidekit score` CLI: advisory output + optional --min-score gate.

The score command is ADVISORY: by default it always exits 0 (the linter stays the
build gate). `--min-score` is an opt-in CI floor that exits non-zero below the bar.
"""
from __future__ import annotations

import json
import subprocess
import sys

DECK = "examples/agents-in-ai.yaml"


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "slidekit.cli", "score", *args],
        capture_output=True,
        text=True,
    )


def test_score_default_exits_zero():
    """No --min-score → advisory only → always exit 0."""
    r = _run(DECK)
    assert r.returncode == 0
    assert "deck aesthetic score" in r.stdout


def test_json_report_includes_warnings_key():
    r = _run(DECK, "--json")
    assert r.returncode == 0
    report = json.loads(r.stdout)
    assert "warnings" in report
    assert isinstance(report["warnings"], list)


def test_min_score_below_floor_fails():
    r = _run(DECK, "--min-score", "99")
    assert r.returncode == 1
    assert "below" in r.stderr


def test_min_score_above_floor_passes():
    r = _run(DECK, "--min-score", "10")
    assert r.returncode == 0
