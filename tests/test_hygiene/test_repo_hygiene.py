"""Guard: environment/cache junk must never be tracked by git.

The entire .venv (2,378 files) was accidentally committed once via a bulk
`git add -A` (commit 48a19db; removed in ade1113). The .githooks/pre-commit
hook blocks this at commit time, but hooks only run where core.hooksPath is
armed — this test makes the invariant fail the suite (and CI) regardless.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

BLOCKED = re.compile(
    r"^(\.venv/|\.hypothesis/|\.pytest_cache/|node_modules/)"
    r"|/__pycache__/|\.py[cod]$|\.egg-info/"
)


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout.splitlines()


def test_no_environment_junk_is_tracked():
    bad = [p for p in _tracked_files() if BLOCKED.search(p)]
    assert not bad, (
        f"environment/cache files are tracked by git: {bad[:10]}"
        " — untrack them (git rm -r --cached <path>) and never use 'git add -A'"
    )


def test_gitignore_covers_venv():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert ".venv/" in ignored


def test_repo_git_hooks_are_executable():
    for name in ("pre-commit", "commit-msg"):
        hook = ROOT / ".githooks" / name
        assert hook.is_file(), f".githooks/{name} is missing"
        assert hook.stat().st_mode & 0o111, f".githooks/{name} is not executable"
