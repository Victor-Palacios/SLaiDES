# SLaiDES / slidekit — session rules

slidekit builds slide decks from declarative YAML with provable, font-metric
layout. Read `SKILL.md` for the authoring workflow. The rules below exist
because each one was violated by a past session — follow them exactly.

## Git hygiene (non-negotiable)

- **Never `git add -A`, `git add .`, or `git add --all`.** Stage explicit
  paths only. A bulk add once committed the entire `.venv` (2,378 files,
  commit 48a19db; removed in ade1113).
- **Never commit environment or cache dirs**: `.venv/`, `.hypothesis/`,
  `.pytest_cache/`, `__pycache__/`, `node_modules/`. They are gitignored;
  do not force-add them. `tests/test_hygiene/` fails the suite if any
  tracked path matches.
- **Commit footer: the `Claude-Session:` link line only.** No
  `Co-Authored-By:` trailers, no "Generated with ..." lines, and no AI model
  identifiers (e.g. model marketing names or model IDs) anywhere in commit
  messages, PR text, or code comments. Writing "Claude Code" as a topic
  (e.g. a deck about the tool) is fine.
- Enforcement: versioned hooks in `.githooks/` check both rules. Claude Code
  sessions arm them automatically (SessionStart hook runs
  `git config core.hooksPath .githooks`). If you commit from an environment
  where they aren't armed, run that command first.

## Environment

- Use the repo venv: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
  if `.venv` is missing or was built by a different container.
- Run tests with the venv on PATH (some tests shell out to the `slidekit`
  CLI): `PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q`
- The suite must be fully green before pushing.

## Example decks (enforced by tests)

Every deck at `examples/<stem>.yaml` requires:

1. A committed render at `examples/pdf/<stem>.pdf` whose page count equals
   the slide count (emit with `slidekit.emit.pdf_emitter.emit_pdf(deck, resolved, path)` —
   arguments are deck-first).
2. Regenerating both derived artifacts after any example change:
   `python scripts/build_examples_index.py` and
   `python scripts/build_combined_pdf.py` (hash-sync-tested).

## Layout QA

Never QA a deck by rendering screenshots — `lint(deck, resolved)` is the
source of truth. Fix lint errors by editing the YAML copy to fit the proven
geometry, not by changing geometry to fit the copy.

## Operator feedback loop

Operator feedback lands in `ops/FEEDBACK.yaml` (via the review site and
`web/data/state.json`). Standing style rules from past feedback: no bullet
glyphs; text hugs its underline rule; matrix layouts highlight 1–2 items,
never whole categories; when the operator supplies explicit numbers, use
their literals verbatim.
