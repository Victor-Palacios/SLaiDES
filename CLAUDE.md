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
their literals verbatim; bullet-list items fit on ONE line — keep each short
enough that it never wraps (FB-098).

**Run a repetition pass before shipping any deck.** Drafting produces slides
that restate each other, and the operator notices. After the deck lints clean
and before emitting anything, reduce every slide to a one-line claim, read the
claims as a list, and find the pairs that say the same thing. Then:

- **Delete, do not reword.** Two slides making one point are one slide plus
  filler. Cutting the weaker one is the fix; rephrasing it is not.
- **Variance must be true.** A second slide on a topic earns its place only by
  adding a distinction the first does not make — a different axis, a concrete
  example of an abstract rule, a counter-case, or a mirror ("always safe to
  stub" / "never safe to stub"). Restating the same claim in a different
  component is repetition wearing a costume.
- **Recurring structure across decks is not repetition.** Deliberate devices
  that repeat once per session — the agenda, the exit checklist, "if you are
  behind", "write this down now" — are navigation, and they stay.
- Say in the reply what the pass removed, or that it found nothing.

Standing operator instruction (2026-09-05).

**At most three colours on a slide, counting the background.** A white
background with blue and black text is the ceiling. A fourth colour — grey body
text, a muted caption, a second accent — is not allowed, even when it is subtle.
Combined with the no-black-and-white rule above, every slide lands on exactly
two or three colours: the background, an ink, and at most one more. Standing
operator instruction (2026-09-05).

**No slide may be black and white.** Every slide must carry at least one element
the eye reads as colour — the page number does NOT count (it is chrome). This is
enforced by the linter as `E_MONOCHROME`, judged perceptually (a very dark navy
"ink" reads as black and does not satisfy it; a saturated backdrop like the code
panel does). The default `theme.headline` role is `accent`, which colours slide
titles and satisfies the rule for free. Standing operator instruction (2026-08-26).

**The page number hugs the bottom-right corner.** Its chrome box is right-aligned
against the right margin, not parked inboard. Standing operator instruction
(2026-08-26).

**Speaker notes are mandatory.** Every slide of every deck you author carries a
`notes:` field. Notes render to the pptx notes page only — never on the slide —
so they never affect layout or lint. Standing operator instruction (2026-08-26).

**Notes are the spoken narrative, not stage direction.** A note is what a
presenter would say out loud, so that reading a deck's notes end to end tells its
story. Four rules (operator decision 2026-08-27, after reviewing three candidate
styles):

- **Say the slide.** One or two sentences speaking the slide's own content in
  full prose. No argument the slide does not make, no example it does not have.
- **Voice is a natural presenter mix**: "we" for what the room does together,
  "you" for the audience's own work. Never "they"/"teams" *about* the audience.
- **Logistics are rewritten as speech, never dropped.** "The gate is 10:45"
  becomes "we swap logs at 10:45, whatever state your testing is in."
- **No stage directions** — nothing of the form *Stress…, Flag…, Point out…,
  Ask it and wait, Return here whenever…, Read this at 11:40, Have each…*

Example — slide `definition: Workflow / "Ordered steps from raw input to
delivered output."` → *"A workflow is the ordered set of steps that carries you
from raw input all the way to a delivered output. Both ends of that sentence
matter as much as the middle."*
