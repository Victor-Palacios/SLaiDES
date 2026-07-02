---
name: slidekit
description: >-
  Build PowerPoint (.pptx) slide decks from declarative YAML with deterministic,
  provable layout correctness. Use when asked to create, generate, or fix a slide
  deck / presentation. Layout is verified by an arithmetic linter, NOT by
  rendering screenshots — never inspect images to QA a slidekit deck.
---

# slidekit — agent-first slide builder

slidekit turns a declarative slide IR (YAML) into a `.pptx` whose layout is
**computed from real font metrics and checked by a linter before emit**. Overflow,
overlap, margin, and contrast defects are caught as arithmetic over the resolved
geometry — so you fix them by editing YAML and re-running the build, never by
looking at a rendered slide.

## When to use

- "Make me a deck / presentation / slides about X" → author IR YAML, build, fix lint.
- "Fix the layout problems in this deck" → run `slidekit build`, act on the JSON lint errors.
- NOT for editing arbitrary inbound third-party `.pptx` files (out of scope; those
  still need the inspect-render workflow).

## The one hard rule: never render to check your work

Do **not** take screenshots, convert to images, or visually inspect a deck to verify
layout. The whole point of slidekit is that correctness is provable from source. The
linter is the source of truth. (A CI-only pixel harness exists to catch renderer
drift — it is not part of your build/fix loop and you never invoke it to QA a deck.)

## The build / fix loop

```
1. slidekit new --template standard -o deck.yaml   # scaffold a themed starter
2. edit deck.yaml                                   # replace placeholder copy
3. slidekit build deck.yaml -o deck.pptx
4. exit 0 → done. exit 1 → read the JSON lint errors on stderr,
   apply each error's `suggested_fix` at its `node_path`, go to 3.
```

Every lint error is JSON: `{code, slide, node_path, message, suggested_fix}`. Fix by
editing the IR at `node_path` per `suggested_fix`. Warnings (codes starting `W_`) do
**not** block the build — address them for quality, but `build` still exits 0.

Useful commands:
- `slidekit new --list` — list starter templates (`title-slide`, `standard`, `comparison`, `pitch`).
- `slidekit layout deck.yaml --json` — inspect resolved EMU geometry without rendering.
- `slidekit schema -o schema.json` — export the JSON Schema for editor validation.

## IR cheatsheet

```yaml
version: 1                     # required, must be 1
theme:
  palette:                     # reference roles, never raw hex in slide bodies
    primary: "#1B4F8A"
    surface: "#FFFFFF"         # slide background
    accent:  "#E84545"
    text:    "#1A1A2E"
    muted:   "#8A8A9A"         # page numbers / captions
  type_scale:                  # points; body floor is 32pt — HARD, never below
    title: 60                  # 54-66
    header: 42                 # 40-44
    body: 34                   # 32-36
    caption: 25                # 24-26
  font: arial                  # metric-safe set ONLY (see below)
  motif: minimal
page_numbers:                  # built-in chrome, bottom-right, on by default
  enabled: true
  start_at: 1
  skip_title_slide: true
slides:
  - component: ...             # one of the 8 components below
```

**Metric-safe fonts (the only allowed set):** Arial, Calibri, Cambria,
Times New Roman, Courier New, Bookman Old Style, Century Schoolbook. Any other font
is an `E_FONT` error at validation.

**Content slots** (used inside `left`/`right`/`content` lists):
- `{type: text, content: "...", max_lines: N?}`
- `{type: image, path: "...", fit: cover|contain}`
- `{type: icon, name: "..."}`
- `{type: chart, chart_type: bar|line|pie|scatter, ...}`  (stub)
- `{type: spacer}`

## Component gallery

Each component compiles to a row/column tree; you fill typed slots.

**Choosing a layout (no vision).** Pick a component per slide from its *content shape*, not
by rendering anything: [docs/LAYOUT_SELECTION_GUIDE.md](docs/LAYOUT_SELECTION_GUIDE.md)
lists every component's purpose, when-to-use, capacity, and required fields, grouped by the
~25 distinct layout families (see [docs/LAYOUT_TAXONOMY.md](docs/LAYOUT_TAXONOMY.md)). The
same data is machine-readable via `slidekit catalog --json`.

**Authoring from an outline.** `slidekit author outline.yaml [--pdf]` builds a deck from a
lean outline — a `slides:` list where each slide is a chosen `component` + its fields, or a
`recommend: {<content shape>}` block the deterministic recommender resolves to a component
(theme/version default if omitted). It validates, lints, and emits with no rendering. See
[examples/author-demo/outline.yaml](examples/author-demo/outline.yaml).

| Component | Required keys | Optional |
|---|---|---|
| `title-slide` | `title` | `subtitle`, `logo` (image) |
| `icon-text-rows` | `rows[]` = `{icon, heading, body}` | `title` |
| `stat-callout` | `stats[]` = `{value, label, subtext?}` | `title` |
| `comparison-columns` | `left_title`, `right_title`, `left_items[]`, `right_items[]` = `{text, icon?}` | `title` |
| `timeline` | `events[]` = `{date, title, description?}` | `title` |
| `image-half-bleed` | `image` (image slot), `content[]` | `title`, `image_side: left\|right` |
| `card-grid` | `cards[]` = `{title, body, icon?}` | `title` |
| `section-divider` | `number`, `title` | — |
| `agenda` | `items[]` (text) | `title` (default `Agenda`) |
| `quote-opener` | `quote`, `attribution` | — |
| `big-number` | `value`, `label` | `context` |
| `pull-quote` | `quote`, `attribution` | — |
| `statement` | `text` | — |
| `definition` | `term`, `definition` | — |
| `question` | `question` | — |
| `bullet-list` | `title`, `items[]` (text) | — |
| `feature-list` | `features[]` = `{icon, heading, body}` (≤3 keeps ≥32pt) | `title` |
| `checklist` | `title`, `items[]` = `{text, checked?}` | — |
| `numbered-steps` | `title`?, `steps[]` = `{title, body}` (≤3) | `title` |
| `before-after` | `before`/`after` = `{title, items[]}` (≤3 each) | `title` |
| `pros-cons` | `pros[]`, `cons[]` (≤3 each) | `title`, `pros_title`, `cons_title` |
| `this-vs-that` | `left`/`right` = `{value, label}` | `title` |
| `kpi-grid` | `kpis[]` = `{value, label}` (4–6) | `title` |
| `chart-slide` | `chart` (chart slot) | `title`, `caption` |
| `chart-with-insight` | `chart`, `insight` | `title` |
| `table-slide` | `headers[]`, `rows[][]` (≤4 rows × ≤3 cols keeps ≥32pt) | `title` |
| `metric-comparison` | `metrics[]` = `{value, label, delta?}` (2–3) | `title` |
| `process-steps` | `steps[]` = `{label, body}` (≤4 keeps ≥32pt) | `title` |
| `roadmap` | `phases[]` = `{title, items[]}` (≤4 lanes) | `title` |
| `funnel` | `stages[]` = `{label, value?}` (narrowing bars) | `title` |
| `pyramid` | `layers[]` = `{label}` (widening bars) | `title` |
| `matrix-2x2` | `x_label`, `y_label`, `quadrants[4]` (text) | `title` |
| `swot` | `strengths[]`, `weaknesses[]`, `opportunities[]`, `threats[]` (≤2 each keeps ≥32pt) | `title` |
| `comparison-matrix` | `options[]`, `criteria[]`, `cells[][]` | `title` |
| `team-grid` | `members[]` = `{name, role, image?}` | `title` |
| `image-full-bleed` | `image` | `overlay_title` |
| `image-grid` | `images[]` (2–4 best) | `title`, `captions[]` |
| `logo-wall` | `logos[]` = `{label? image?}` | `title` |
| `testimonial` | `quote`, `name`, `role` | `image` |

A `chart` slot is `{type: chart, chart_type: bar, labels[], series[] = {name, values[]}}`.
Bar charts render as measured colored rectangles + labels (deterministic, lint-provable);
other `chart_type`s render as a labelled placeholder region.

Minimal examples of each live in `examples/01..42_*.yaml` — one single-slide specimen per
component (no cover slide); copy and adapt. The `09_full_deck`, `10_all_components`,
`agents-in-ai`, and `demo-5` decks are multi-slide examples of composing a full presentation.

## Lint error codes and how to fix them

| Code | Meaning | Typical fix |
|---|---|---|
| `E_OVERFLOW` | text/content exceeds its box (after slack) | shorten the text, split across slides, or remove a slot — never shrink below 32pt |
| `E_OVERLAP` | two non-stacked rects intersect | reduce content or use a component that allocates more room |
| `E_MARGIN` | content within 0.5" of a slide edge | remove content or rebalance; do not pin into the margin |
| `E_GAP` | sibling blocks closer than 0.3" | reduce the number of items in the slot |
| `E_MIN_BODY_SIZE` | body text below the 32pt floor | cut text so it fits at ≥32pt (the honest fix is less text or another slide) |
| `E_PAGE_NUMBER` | page number missing/mispositioned/overlapped | move content out of the bottom-right corner |
| `E_FONT` | font outside the metric-safe set | switch `theme.font` to an allowed font |
| `E_CONTRAST` | text vs background contrast too low | pick palette roles with more contrast |

`E_OVERFLOW` and `E_MIN_BODY_SIZE` almost always mean **too much text on the slide**.
The system has a hard 32pt body floor by design: the correct fix is fewer words or an
extra slide, not a smaller font.

## What slidekit will not do

- Shrink body text below 32pt (hard floor, everywhere except the 16pt page-number chrome).
- Hyphenate or justify (v1 is left-aligned Latin text).
- Edit foreign `.pptx` templates.
- Tell you a deck "looks fine" from a screenshot — it proves fit arithmetically instead.
