# Board — slidekit

_Generated from `board.yaml` by `scripts/render_board.py` — edit `board.yaml`, then re-render; do not hand-edit. Sprints, the user stories from `docs/USER_STORIES.md` scheduled into them, and the cards that delivered each; `PROGRESS.md` stays the acceptance ledger._

**backlog** 0 · **todo** 0 · **in_progress** 0 · **blocked** 0 · **done** 97 · _last change 2026-08-24_

_All cards are done — the kanban lanes are omitted. The sprint sections below are the record of the work._

## Epics

| Epic | Done | Total |
|---|---|---|
| Epic A — Authoring decks | 39 | 39 |
| Epic B — Output & sharing | 13 | 13 |
| Epic C — Quality & correctness | 22 | 22 |
| Epic D — Review & feedback loop | 15 | 15 |
| Epic E — Project management & development | 8 | 8 |

## Product backlog

_Every user story from `docs/USER_STORIES.md`, ordered by MoSCoW priority. `Tasks` counts delivered / total cards under the story._

| Story | Epic | Priority | Sprint | Status | Tasks |
|---|---|---|---|---|---|
| **US-01** Scaffold a themed starter deck | A | Must | S1 | ✅ done | 1/1 |
| **US-02** Author slides declaratively without computing geometry | A | Must | S1 | ✅ done | 5/5 |
| **US-03** Build a deck to PowerPoint in one command | A | Must | S1 | ✅ done | 5/5 |
| **US-04** Fix layout defects from lint output, not screenshots | A | Must | S1 | ✅ done | 3/3 |
| **US-06** Theme a deck consistently | A | Must | S1 | ✅ done | 3/3 |
| **US-09** Export to PDF | B | Must | S2 | ✅ done | 2/2 |
| **US-12** Block broken layouts at build time | C | Must | S1 | ✅ done | 7/7 |
| **US-14** Provable layout via metric-safe fonts | C | Must | S1 | ✅ done | 6/6 |
| **US-20** Trust generated artifacts stay in sync | E | Must | S2 | ✅ done | 5/5 |
| **US-05** Pick the right component with guidance | A | Should | S2 | ✅ done | 16/16 |
| **US-07** Cite sources as clickable links | A | Should | S3 | ✅ done | 3/3 |
| **US-08** Page numbers that renumber after edits | A | Should | S3 | ✅ done | 3/3 |
| **US-10** Google-Slides-readable PowerPoint | B | Should | S3 | ✅ done | 9/9 |
| **US-15** Review decks slide-by-slide on my phone | D | Should | S3 | ✅ done | 5/5 |
| **US-16** Mark each slide good / needs-work with a comment | D | Should | S3 | ✅ done | 6/6 |
| **US-18** Feedback flows into a work queue automatically | D | Should | S2 | ✅ done | 2/2 |
| **US-19** Track work on a kanban board | E | Should | S3 | ✅ done | 3/3 |
| **US-11** Preview a deck as HTML | B | Could | S1 | ✅ done | 2/2 |
| **US-13** Gauge visual quality beyond pass/fail | C | Could | S2 | ✅ done | 9/9 |
| **US-17** Request a new slide before/after one | D | Could | S3 | ✅ done | 2/2 |

## Sprints

| Sprint | Window | Stories | Tasks done |
|---|---|---|---|
| **S1** Provable layout core | 2026-06-01 → 2026-06-13 | 8 | 32/32 |
| **S2** Design library and measured quality | 2026-06-14 → 2026-07-02 | 5 | 34/34 |
| **S3** Review loop and shareable output | 2026-07-03 → 2026-08-24 | 7 | 31/31 |

### S1 — Provable layout core

_Build a deck from declarative YAML to PowerPoint with every rect proven from real font metrics, and prove defects are caught by a linter rather than by looking at screenshots._

**2026-06-01 → 2026-06-13** · 8 stories · 32/32 tasks done · _complete_

**US-01 · Scaffold a themed starter deck** — ✅ done (1/1 tasks)

- ✅ `T-130` slidekit new --template scaffolds a themed starter deck

**US-02 · Author slides declaratively without computing geometry** — ✅ done (5/5 tasks)

- ✅ `T-107` pydantic IR schema v1 with precise error paths
- ✅ `T-108` Typed content slots: text, image, chart, icon, spacer
- ✅ `T-109` First eight components, title-slide through card-grid
- ✅ `T-110` Export the IR as JSON Schema (slidekit schema)
- ✅ `T-111` Ten example decks covering every v1 component

**US-03 · Build a deck to PowerPoint in one command** — ✅ done (5/5 tasks)

- ✅ `T-115` Layout engine: two-pass measure-then-assign solver, all math in EMU
- ✅ `T-116` ResolvedDeck with absolute rects + slidekit layout --json
- ✅ `T-117` pptx emitter: exact EMU rects, auto-fit off, literal RGB runs
- ✅ `T-118` slidekit build CLI: resolve -> lint -> emit, non-zero on any error
- ✅ `T-119` First-light demo: examples/demo-5.yaml -> demo-5.pptx

**US-04 · Fix layout defects from lint output, not screenshots** — ✅ done (3/3 tasks)

- ✅ `T-127` JSON lint output: code, slide, node_path, message, suggested_fix
- ✅ `T-128` SKILL.md agent guide: IR cheatsheet, gallery, build/fix loop
- ✅ `T-129` Measure fresh-agent repair rate from lint output alone

**US-06 · Theme a deck consistently** — ✅ done (3/3 tasks)

- ✅ `T-112` Theme block: palette roles, type scale, spacing unit, motif, font
- ✅ `T-113` Hard 32pt body floor enforced in the type scale
- ✅ `T-114` Page numbers as built-in chrome with a reserved bottom-right box

**US-12 · Block broken layouts at build time** — ✅ done (7/7 tasks)

- ✅ `T-120` E_OVERFLOW, E_OVERLAP, E_MARGIN and E_GAP checks over resolved geometry
- ✅ `T-121` E_MIN_BODY_SIZE with chrome and caption-tier exemptions
- ✅ `T-122` E_PAGE_NUMBER and E_FONT checks
- ✅ `T-123` Advisory warnings: repeated component, text-only slide, weak hierarchy
- ✅ `T-124` Fixture deck carrying one instance of every defect class
- ✅ `T-125` Golden-file layout tests, byte-determinism and a Hypothesis fuzz pass
- ✅ `T-126` Verification harness: render examples and check ink stays inside the rects

**US-14 · Provable layout via metric-safe fonts** — ✅ done (6/6 tasks)

- ✅ `T-101` Vendor per-glyph advances, kerning pairs and vertical metrics via fonttools
- ✅ `T-102` measure_text(text, font, size, bold, italic) -> width in EMU, kerning included
- ✅ `T-103` Reject fonts outside the metric-safe set at IR validation (E_FONT)
- ✅ `T-104` Calibration harness vs LibreOffice — HARD GATE at 2%
- ✅ `T-105` Greedy line breaking matching PowerPoint; wrap() returns measured Lines
- ✅ `T-106` Text-box insets and single line spacing (1.2x) fixed in one place

**US-11 · Preview a deck as HTML** — ✅ done (2/2 tasks)

- ✅ `T-131` HTML preview positioned from the resolved EMU geometry
- ✅ `T-132` Preview-fidelity tests tying HTML and pptx to the same nodes

### S2 — Design library and measured quality

_Grow eight components into a thirty-component library an agent can choose from without vision, add a PDF path, and put numbers on visual quality with a research-grounded aesthetics score._

**2026-06-14 → 2026-07-02** · 5 stories · 34/34 tasks done · _complete_

**US-09 · Export to PDF** — ✅ done (2/2 tasks)

- ✅ `T-217` Native PDF emitter on reportlab, no LibreOffice in the build path
- ✅ `T-218` Committed per-deck PDFs with a page-count test

**US-20 · Trust generated artifacts stay in sync** — ✅ done (5/5 tasks)

- ✅ `T-228` Golden files for every example deck's resolved geometry
- ✅ `T-229` Generated docs kept in sync by --check tests
- ✅ `T-230` Dated combined-PDF archive keyed by a layout fingerprint
- ✅ `T-231` Verify harness green across every example deck
- ✅ `T-232` Repo-hygiene tests and versioned git hooks

**US-05 · Pick the right component with guidance** — ✅ done (16/16 tasks)

- ✅ `T-201` Emphasis group: section-divider, big-number, pull-quote, definition, question
- ✅ `T-202` List group: agenda, bullet-list, numbered-steps, two-panel-list
- ✅ `T-203` Comparison group: this-vs-that plus comparison-columns refinements
- ✅ `T-204` Data group: kpi-grid, chart-with-insight, table-slide, metric-comparison
- ✅ `T-205` Flow group: process-steps, roadmap, funnel, pyramid
- ✅ `T-206` Matrix group: swot and comparison-matrix
- ✅ `T-207` Code layout: dark IDE panel with per-token syntax colouring
- ✅ `T-208` File-tree layout on a rounded dark card
- ✅ `T-209` Nested-circles layout with first-class ellipse nodes
- ✅ `T-210` Retire seven low-value layouts after operator review
- ✅ `T-211` Component-metadata registry as the single source of truth
- ✅ `T-212` Honest taxonomy: 30 components over 22 distinct skeletons
- ✅ `T-213` slidekit catalog and a generated selection guide
- ✅ `T-214` Deterministic content-shape recommender and slidekit author
- ✅ `T-215` Apply operator layout feedback FB-001..FB-017
- ✅ `T-216` Strip cover slides from the single-component specimens

**US-18 · Feedback flows into a work queue automatically** — ✅ done (2/2 tasks)

- ✅ `T-233` FEEDBACK.yaml ledger with a rendered FEEDBACK.md view
- ✅ `T-234` Issue-form intake folding operator reports into the ledger

**US-13 · Gauge visual quality beyond pass/fail** — ✅ done (9/9 tasks)

- ✅ `T-219` Aesthetics scorer with weighted sub-scores
- ✅ `T-220` W_AESTH_* advisories and an opt-in --min-score gate
- ✅ `T-221` Balance, richness, contrast and colour-harmony sub-scores
- ✅ `T-222` Info-density sub-score over words-per-slide and text coverage
- ✅ `T-223` Harrington non-linear score combiner as an opt-in mode
- ✅ `T-224` Grow REFERENCES.md to 20 primary-source-verified works
- ✅ `T-225` RESEARCH_TRACE.md mapping paper -> decision -> code
- ✅ `T-226` Close the outstanding research caveats and correct two doc overclaims
- ✅ `T-227` Assess and reject metrics that would duplicate existing sub-scores

### S3 — Review loop and shareable output

_Close the loop with the operator: a private per-slide review site whose feedback becomes work automatically, and decks that survive import into Google Slides as editable, correctly numbered slides._

**2026-07-03 → 2026-08-24** · 7 stories · 31/31 tasks done · _complete_

**US-07 · Cite sources as clickable links** — ✅ done (3/3 tasks)

- ✅ `T-314` source field on a slide renders as a clickable Source link
- ✅ `T-315` Link chrome exempt from margin lint but still proven to fit
- ✅ `T-316` Sourced slides added to the Claude Code deck

**US-08 · Page numbers that renumber after edits** — ✅ done (3/3 tasks)

- ✅ `T-317` Emit the page number as an <a:fld type=slidenum> field
- ✅ `T-318` Align firstSlideNum with the deck's page_numbers.start_at
- ✅ `T-319` Wrap the field in a sldNum placeholder in the bottom-right corner

**US-10 · Google-Slides-readable PowerPoint** — ✅ done (9/9 tasks)

- ✅ `T-320` Emit one named slide layout per design
- ✅ `T-321` Make layout text a real placeholder so a picked design is editable
- ✅ `T-322` Promote layout shapes to placeholders so designs can be recoloured
- ✅ `T-323` Suppress inherited layout graphics on emitted slides
- ✅ `T-324` Turn word-wrap off for single-line nodes
- ✅ `T-325` Give single-line boxes width slack, with the centre held fixed
- ✅ `T-326` Zero horizontal text insets so glyphs start at exactly rect.x
- ✅ `T-327` E_WRAP: text must fit on one line
- ✅ `T-328` Ignore the rasteriser's edge fringe in the verify harness

**US-15 · Review decks slide-by-slide on my phone** — ✅ done (5/5 tasks)

- ✅ `T-301` Static review site served from committed geometry
- ✅ `T-302` Single-password edge gate over the whole site
- ✅ `T-303` Slide-by-slide gallery rendered from resolved rects
- ✅ `T-304` Deck review page with per-slide, scope-aware comments
- ✅ `T-305` Deploy only when the served site can actually change

**US-16 · Mark each slide good / needs-work with a comment** — ✅ done (6/6 tasks)

- ✅ `T-306` Thumbs-up / thumbs-down marks with a free-text comment
- ✅ `T-307` Serverless submit function committing one JSON file per submission
- ✅ `T-308` Workflow folding the inbox into FEEDBACK.yaml automatically
- ✅ `T-309` Rebuild the EDA-library talk as a slidekit deck
- ✅ `T-310` Apply operator feedback FB-050..FB-116 across the review decks
- ✅ `T-311` Midnight dark colour scheme for the EDA deck

**US-19 · Track work on a kanban board** — ✅ done (3/3 tasks)

- ✅ `T-329` board.yaml as source of truth, rendered to BOARD.md
- ✅ `T-330` Write the 20 user stories in docs/USER_STORIES.md
- ✅ `T-331` Restructure the board into sprints, stories and constituent tasks

**US-17 · Request a new slide before/after one** — ✅ done (2/2 tasks)

- ✅ `T-312` Add-slide-before / add-slide-after actions on the review page
- ✅ `T-313` Record the requested position and direction with the comment

