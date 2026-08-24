# User stories — slidekit

_Initial backlog of 20 user stories for the slidekit slide-generation system.
Written in the standard `As a <role>, I want <capability>, so that <benefit>`
form with lightweight acceptance criteria. These are product-level intents; each
can seed one or more cards in `ops/board.yaml`. Priority uses MoSCoW
(Must / Should / Could)._

## Personas

- **Author** — a data scientist or presenter (often an AI agent) who writes deck
  YAML and builds it.
- **Agent** — an automated Claude session authoring or fixing decks unattended.
- **Presenter** — someone who takes the built deck and shows/shares it (PDF,
  PowerPoint, Google Slides).
- **Reviewer** — the operator reviewing rendered decks and giving feedback, often
  from a phone.
- **Maintainer** — a contributor developing slidekit itself.

---

## Epic A — Authoring decks

### US-01 · Scaffold a themed starter deck · _Must_
As an **author**, I want to scaffold a themed starter deck with one command
(`slidekit new --template standard -o deck.yaml`), so that I can start from valid,
on-theme placeholder copy instead of a blank file.
- **Acceptance:** running the command writes a YAML deck that builds lint-clean
  before any edits; the template carries a coherent palette, type scale, and font.

### US-02 · Author slides declaratively without computing geometry · _Must_
As an **author**, I want to describe each slide's content in declarative YAML
(component + fields), so that I never hand-position text or compute sizes.
- **Acceptance:** a slide is fully specified by a `component` and its content
  fields; the engine resolves all absolute geometry from font metrics.

### US-03 · Build a deck to PowerPoint in one command · _Must_
As an **author**, I want `slidekit build deck.yaml -o deck.pptx` to produce a
`.pptx`, so that I get a shippable artifact in a single step.
- **Acceptance:** exit 0 writes the file and reports slide count + "lint-clean";
  exit 1 emits machine-readable errors and writes nothing broken.

### US-04 · Fix layout defects from lint output, not screenshots · _Must_
As an **agent**, I want build failures reported as JSON errors with a
`node_path` and a `suggested_fix`, so that I can repair a deck without rendering
or inspecting images.
- **Acceptance:** each error names its slide, node, defect code, and a concrete
  fix; applying the fixes and rebuilding reaches exit 0 in at most one round.

### US-05 · Pick the right component with guidance · _Should_
As an **author**, I want a catalog of components with "use when" guidance and a
generated selection guide, so that I can choose the best layout for my content
without trial and error.
- **Acceptance:** every component appears in the catalog with purpose, capacity,
  and content-shape metadata; the selection guide is derived from that registry.

### US-06 · Theme a deck consistently · _Must_
As an **author**, I want to set a theme once (palette, type scale, font, headline
role), so that every slide is visually consistent.
- **Acceptance:** changing a palette role or the headline role restyles all
  affected slides on rebuild; no per-slide color/size duplication is required.

### US-07 · Cite sources as clickable links · _Should_
As an **author**, I want to attach a `source` URL to a slide and have it render
as a clickable "Source" link in the bottom-right, so that claims are traceable.
- **Acceptance:** a valid http(s) `source` produces a hyperlinked chrome node in
  pptx/pdf/html; the link is exempt from margin lint but still proven to fit.

### US-08 · Page numbers that renumber after edits · _Should_
As a **presenter**, I want page numbers to be real auto-updating slide-number
fields, so that they renumber when I move or add slides in PowerPoint/Google
Slides.
- **Acceptance:** the pptx page number is a `slidenum` field showing the same
  value slidekit computed; a skipped title slide carries no number.

---

## Epic B — Output & sharing

### US-09 · Export to PDF · _Must_
As a **presenter**, I want to export a deck to PDF, so that I can share or print a
fixed-layout copy.
- **Acceptance:** the PDF page count equals the slide count and reproduces the
  resolved geometry; hyperlinks are preserved.

### US-10 · Google-Slides-readable PowerPoint · _Should_
As a **presenter**, I want the exported `.pptx` to render faithfully after import
into Google Slides, so that I can present from Drive.
- **Acceptance:** single-line text (code, citations, numerals) does not re-wrap on
  import; imported slide numbers stay live.

### US-11 · Preview a deck as HTML · _Could_
As an **author**, I want an HTML preview built from the same resolved geometry,
so that I can eyeball a deck in a browser without the full render pipeline.
- **Acceptance:** the preview positions nodes from the exact EMU layout (no
  screenshots) and is theme-accurate in light/dark.

---

## Epic C — Quality & correctness

### US-12 · Block broken layouts at build time · _Must_
As an **author**, I want the build to fail on any layout defect (overflow,
margin, overlap, gap, min-body-size, unsafe font), so that nothing visually
broken can ship.
- **Acceptance:** each defect class has a lint check over resolved geometry; a
  deck with any error exits non-zero and names the offending nodes.

### US-13 · Gauge visual quality beyond pass/fail · _Could_
As an **author**, I want an aesthetics score and advisory warnings, so that I can
judge polish even when a deck already passes the linter.
- **Acceptance:** a scorer reports sub-scores and `W_AESTH_*` advisories; an
  optional `--min-score` gate can be enabled without changing the hard lint gate.

### US-14 · Provable layout via metric-safe fonts · _Must_
As a **maintainer**, I want font choices restricted to a metric-safe set, so that
layout math is provable and matches real renderers.
- **Acceptance:** an unknown font is rejected at author time with a clear message
  listing the allowed set.

---

## Epic D — Review & feedback loop

### US-15 · Review decks slide-by-slide on my phone · _Should_
As a **reviewer**, I want a private site that shows every deck rendered
slide-by-slide, so that I can review on the go.
- **Acceptance:** the site lists showcase decks and renders each slide from the
  committed geometry (not screenshots); access is restricted.

### US-16 · Mark each slide good / needs-work with a comment · _Should_
As a **reviewer**, I want to mark a slide 👍/👎 and add a comment, so that I can
capture precise, per-slide feedback.
- **Acceptance:** a submitted mark is scoped to the deck + slide index and lands
  as an actionable item downstream.

### US-17 · Request a new slide before/after one · _Could_
As a **reviewer**, I want "add slide before ↑ / after ↓" actions with a comment
describing the wanted slide, so that I can request new content in place.
- **Acceptance:** the request is recorded with the deck + position and a
  direction marker so an agent knows where to insert.

### US-18 · Feedback flows into a work queue automatically · _Should_
As a **reviewer**, I want my submissions to fold automatically into a canonical
feedback queue (`ops/FEEDBACK.yaml`), so that an agent can act on them without me
re-entering anything.
- **Acceptance:** a submission becomes an `open` comment in the ledger (with
  verdict/severity/scope); positive-only marks are counted, not queued as tasks.

---

## Epic E — Project management & development

### US-19 · Track work on a kanban board · _Should_
As a **maintainer**, I want an agile board (`ops/board.yaml` rendered to
`ops/BOARD.md`) with backlog/todo/in-progress/blocked/done lanes and epics, so
that I can see active work at a glance.
- **Acceptance:** editing `board.yaml` and re-rendering updates `BOARD.md`
  column tallies and epic burn-down; a test keeps the two in sync.

### US-20 · Trust generated artifacts stay in sync · _Must_
As a **maintainer**, I want every generated file (goldens, taxonomy, selection
guide, examples index, combined PDF, web JSON) guarded by a sync/golden test, so
that regressions and stale artifacts are caught in CI.
- **Acceptance:** a `--check` (or golden) test fails when a committed derived
  artifact does not match its regenerated output.

---

_All 20 stories are scheduled and delivered across three closed sprints — see
`ops/BOARD.md` for the product backlog, the sprint each story landed in, and the
cards that delivered it. A test keeps the story ids here and on the board in sync._
