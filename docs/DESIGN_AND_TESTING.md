# Design & Testing Document — slidekit

_This document satisfies the MSSE Capstone requirement for a "detailed design and
testing document" covering **(1) design and architecture decisions** — technologies,
architectural choices and reasons, software/architectural patterns used and reasons,
and recommended deployment options with relative cost — and **(2) software testing
carried out** — all testing done, the automated tests, methods, and reasons. It is a
living document; team-specific process notes belong under §6._

---

## 1. What the system is

**slidekit** is an agent-first slide-deck build tool. It turns a declarative slide
description (YAML) into a PowerPoint (`.pptx`) — and PDF/HTML — whose layout
correctness is **proven arithmetically from the source**, not verified by rendering
and eyeballing screenshots. The core thesis: treat slide layout like a **compiler**
treats code — parse to an intermediate representation, run deterministic passes over
it, and fail the build on any defect — so a slide is correct *by construction*.

Primary users (see [`docs/USER_STORIES.md`](USER_STORIES.md)): a deck **author**
(often an AI agent), a **presenter** who exports/shares, a **reviewer** who gives
feedback from a phone, and a **maintainer** developing slidekit itself.

---

## 2. Technologies used (and why)

| Technology | Where | Why this choice |
|---|---|---|
| **Python 3.11+** | whole system | Rich text/geometry libraries; the target audience (data scientists) lives in Python; fast to iterate. |
| **Pydantic** | `src/slidekit/ir/` | Declarative schema + validation for the slide IR; discriminated unions model "one of N component types" cleanly and reject malformed decks at parse time. |
| **python-pptx** | `src/slidekit/emit/pptx_emitter.py` | Writes real Office Open XML `.pptx` with absolute EMU geometry — no LibreOffice/Office dependency at build time. |
| **reportlab** | `src/slidekit/emit/pdf_emitter.py` | Deterministic PDF drawing at absolute coordinates for the PDF export. |
| **Bundled font-metric tables** | `src/slidekit/metrics/` | Per-glyph advance widths for a metric-safe font set, so text width/height is computed offline and matches real renderers — the basis of "provable layout". |
| **PyYAML** | `src/slidekit/ir/parse.py` | The authoring surface is human- and agent-friendly YAML. |
| **pytest (+ Hypothesis)** | `tests/` | Unit/golden/property tests; Hypothesis fuzzes the text-measurement/wrap math. |
| **GitHub Actions** | `.github/workflows/` | CI: render-drift verification and the automated maintenance bot. |
| **Static site + Netlify (edge + functions)** | `web/`, `netlify/` | The mobile review site; a static gallery plus a serverless write path (see §4). |

---

## 3. Architecture and design decisions

### 3.1 Overall shape — a compiler pipeline

```
YAML  ──parse──▶  IR (validated)  ──resolve──▶  Resolved geometry  ──lint──▶  gate  ──emit──▶  .pptx / .pdf / .html
      ir/parse       ir/models          layout/engine (EMU)         lint/checks           emit/*
```

- **`ir/`** — parse + validate the deck into typed models (front end).
- **`layout/engine.py`** — the "resolve" pass: compute every node's absolute
  rectangle in EMU from real font metrics (middle end).
- **`lint/checks.py`** — the **gate**: arithmetic checks over the resolved geometry.
- **`emit/`** — back ends that serialize the resolved geometry to `.pptx`, `.pdf`,
  and an HTML preview.
- **`catalog/`, `select/`, `aesthetics/`, `verify/`** — component registry +
  selection guide, an advisory aesthetic scorer, and a CI-only render-drift harness.

**Why this architecture:** separating *what* a slide contains (IR) from *where things
land* (resolve) from *is it correct* (lint) from *file format* (emit) means each
concern is independently testable, a new output format is just another back end, and
correctness is a property of the geometry — checkable without opening the file.

### 3.2 Key decisions and their reasons

1. **Correctness is provable from source, not from screenshots.** The linter — not a
   human looking at a render — is the source of truth. *Reason:* visual QA is slow,
   non-deterministic, and (for an AI author) burns large image-token budgets; arithmetic
   over geometry is instant, deterministic, and CI-enforceable.
2. **Fail-closed build gate.** Any defect (text overflow, margin violation, node
   overlap, insufficient gap, sub-minimum body size, non-metric-safe font) makes
   `slidekit build` exit non-zero with machine-readable JSON (`node_path` +
   `suggested_fix`). *Reason:* nothing broken can ship, and an agent can self-repair.
3. **Metric-safe font set.** Fonts are restricted to those with bundled metric tables.
   *Reason:* layout math is only provable if glyph widths are known and match the
   renderer; an unknown font is rejected at author time.
4. **Single source of truth + generated artifacts.** The component **registry**
   generates the taxonomy and selection guide; `ops/board.yaml` generates
   `ops/BOARD.md`; `ops/FEEDBACK.yaml` generates `FEEDBACK.md`; example decks generate
   the web preview JSON. Each pair is guarded by a **sync test**. *Reason:* derived docs
   can never drift from their source without CI failing.
5. **Deterministic output.** Given the same input, the build produces the same geometry
   (byte/hash-stable where the format allows). *Reason:* makes golden-master testing and
   review diffs meaningful.

### 3.3 Software and architectural patterns used (and why)

| Pattern | Where | Why used |
|---|---|---|
| **Pipeline / compiler (IR + passes + code-gen)** | whole system | Isolates concerns; each stage is independently testable; new outputs = new back ends. |
| **Discriminated (tagged) union** | `ir/models.py` (`component:` field) | One validated type per slide component; malformed decks rejected at parse. |
| **Two-pass layout (measure → place)** | `layout/engine.py` | Text is measured from metrics first, then positioned, so overflow is known before emit. |
| **Linter-as-gate / fail-closed** | `lint/checks.py`, `cli.py` | Correctness enforced at build time, not review time. |
| **Emitter / visitor (dispatch on node type)** | `emit/pptx,pdf,html` | The same resolved node tree renders to three formats through parallel back ends. |
| **Registry (single source of truth)** | `catalog/registry.py` | One authoritative list of components drives docs, selection, and coverage tests. |
| **Generated-artifact + sync check** | `scripts/*` + `--check` tests | Derived files (board, taxonomy, guide, indexes, web JSON) can't go stale. |
| **Golden master** | `tests/test_layout/golden/*.json` | Any change to resolved geometry is a reviewable, intentional diff. |
| **Adapter** | `emit/pptx_emitter.py` (`_LayoutCanvas`), palette proxy | Reuse the slide-drawing paths for layout templates; thread a theme override without changing every signature. |
| **Strategy** | `metrics/` font tables | Per-font measurement strategy behind one `measure_text`/`wrap` API. |

### 3.4 Recommended deployment options and relative cost

slidekit's core deliverable is a **command-line tool / Python library**, not a
long-running service, so "deployment" mainly means **distribution + CI**, not hosting.

| Option | What it looks like | Relative cost |
|---|---|---|
| **On-premises / local (recommended for the library)** | `pip install -e .`; authors and CI generate decks on their own machines. No server. | **$0** — uses existing compute. |
| **Cloud CI (recommended for automation)** | GitHub Actions runners build decks and run the test suite on push. | **≈$0** — free-tier Actions minutes (public repos free; private repos get a monthly allotment, overage ≈ $0.008/min). |
| **Package distribution** | Publish to PyPI for `pip install slidekit`. | **$0** — PyPI hosting is free. |
| **Optional review website** | Static `web/` + a small write path. Currently Netlify (edge-auth + serverless function). | **$0 on Netlify free tier** (bandwidth + function-call limits); GitHub Pages is a $0 static alternative if the password gate is dropped. |

**Recommendation:** ship the core as a **pip-installable library/CLI run locally and
in GitHub Actions** — no always-on infrastructure, so **no recurring hosting cost**.
Keep the review site on a **free PaaS tier** (Netlify today; GitHub Pages if public
viewing is acceptable). An always-on cloud VM is **not** recommended: it would add
monthly cost for a build tool that has no server component.

---

## 4. The review-and-feedback subsystem (supporting architecture)

A private, mobile-friendly site (`web/`) renders every deck **slide-by-slide from the
same resolved geometry** (not screenshots) so a reviewer can mark each slide
👍 / 👎 / "add slide before/after" with a comment. Submissions commit a JSON file to
`web/feedback-inbox/`; the [`web-feedback-intake`](../.github/workflows/web-feedback-intake.yml)
GitHub Action folds them into `ops/FEEDBACK.yaml` via `scripts/feedback_intake_web.py`,
which an author (or the maintenance bot) then works through. This closes the loop from
"review on a phone" to "tracked, actionable work item" with no manual re-entry.

---

## 5. Testing

### 5.1 Strategy and method

Testing mirrors the architecture: because correctness is defined as **arithmetic over
resolved geometry**, the tests assert that arithmetic directly, rather than comparing
pixels. The suite is **pytest**-based (with **Hypothesis** property tests for the
measurement math) and is the **hard gate** — it must be fully green before any push.
Run it with:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

### 5.2 What is tested (by area)

| Test area (`tests/…`) | What it proves | Method |
|---|---|---|
| `test_ir` | Decks parse and validate; malformed input is rejected. | Unit tests over the Pydantic models. |
| `test_metrics` | Font measurement and line-wrapping are correct. | Unit + **Hypothesis** property tests. |
| `test_layout` | The resolve pass produces the exact expected geometry. | **Golden-master** JSON comparison per example. |
| `test_lint` | Every defect class (overflow, margin, overlap, gap, min-body-size, font) is caught. | Unit tests with crafted failing/passing decks. |
| `test_emit` | `.pptx`/`.pdf`/`.html` reproduce the resolved geometry; hyperlinks, word-wrap, and the auto-renumbering slide-number field are correct. | **Round-trip** (emit → reopen → assert). |
| `test_catalog` | The registry covers exactly the implemented components. | Coverage/consistency tests. |
| `test_select` / `test_author` | Component recommendation and the outline→validate pipeline behave. | Unit tests. |
| `test_aesthetics` | The advisory scorer's sub-scores and warnings behave; designed slides beat plain ones. | Unit tests. |
| `test_board`, `test_examples_index`, `test_combined_pdf`, `test_feedback`, `test_web` | Every **generated artifact** matches a fresh regeneration (`--check`). | **Sync/golden** tests. |
| `test_examples_pdf` | Each example deck has a committed PDF whose page count equals its slide count. | Structural assertion. |
| `test_hygiene` | No environment/cache directories (`.venv`, caches) are ever tracked. | Repo-hygiene assertion. |
| `test_cli`, `test_integration` | The CLI commands and end-to-end build flows work. | Integration tests. |
| `test_verify` | A real renderer (LibreOffice + poppler) doesn't drift from the computed geometry. | **CI-only pixel harness** — see §5.3. |

### 5.3 Continuous integration

- [`.github/workflows/tests.yml`](../.github/workflows/tests.yml) — the **full test
  suite**: runs `pytest -q` on Python 3.11 and 3.12 for every push to `main` and
  every pull request, so the green-suite gate is visible in the Actions tab.
- [`.github/workflows/verify.yml`](../.github/workflows/verify.yml) — the
  **render-drift harness**: on changes to layout/metrics/emit/verify/examples it
  renders the example decks through LibreOffice + poppler and checks cheap pixel
  heuristics against the computed geometry, catching any drift between the math and a
  real renderer. This is **explicitly not** part of the author's build loop.
- [`.github/workflows/web-feedback-intake.yml`](../.github/workflows/web-feedback-intake.yml)
  — folds review-site submissions into the feedback queue.
- [`.github/workflows/nightly.yml`](../.github/workflows/nightly.yml) — the automated
  maintenance session.

**Method note / reason:** the full `pytest` suite is enforced as the pre-push gate
(project rule; versioned git hooks in `.githooks/` also block unhygienic commits). The
render-drift harness runs in CI because it needs system renderers; if it ever disagrees
with the linter, the fix goes into the metrics/layout constants — never into a per-deck
visual loop. The full `pytest -q` suite runs in CI on every push/PR
([`tests.yml`](../.github/workflows/tests.yml)); versioned git hooks in `.githooks/`
additionally block unhygienic commits locally.

### 5.4 Why this testing approach

The whole value proposition is *provable* layout. The tests therefore prove the two
things that make the proof trustworthy: (a) the **geometry** the engine computes is
what we expect (golden tests), and (b) the **linter** actually catches every defect
class it claims to (lint tests) — with round-trip tests ensuring the emitters don't
corrupt that geometry, sync tests ensuring no derived artifact goes stale, and the CI
pixel harness ensuring a real renderer agrees.

---

## 6. Sprints and process

The project ran as **three completed agile sprints**, tracked in
[`ops/board.yaml`](../ops/board.yaml) (rendered to [`ops/BOARD.md`](../ops/BOARD.md))
as **sprints → user stories → constituent tasks** — each story's status is
cross-checked against its own task cards by the board renderer.

| Sprint | Focus | Dates | User stories | Status |
|---|---|---|---|---|
| **S1 — Provable layout core** | YAML → PowerPoint with every rectangle proven from real font metrics; defects caught by the linter, not by screenshots | 2026-06-01 → 06-13 | US-01, 02, 03, 04, 06, 11, 12, 14 | ✅ complete |
| **S2 — Design library and measured quality** | grow 8 components into a ~30-component library selectable without vision; add the PDF path; a research-grounded aesthetics score | 2026-06-14 → 07-02 | US-05, 09, 13, 18, 20 | ✅ complete |
| **S3 — Review loop and shareable output** | a private per-slide review site whose feedback becomes work automatically; decks that survive Google Slides import as editable, correctly numbered slides | 2026-07-03 → 08-24 | US-07, 08, 10, 15, 16, 17, 19 | ✅ complete |

The full per-sprint task breakdown and completion status live in the board; the user
stories themselves are in [`docs/USER_STORIES.md`](USER_STORIES.md).

**Still team-specific (fill in per submission):**
- **Roles:** Product Owner, Scrum Master, Code Owner(s).
- **Collaborative tools:** GitHub (repo, Actions/CI, code review), the `ops/` board
  and feedback queue.
- **Proposal / Group Project Agreement:** link or note where submitted.
