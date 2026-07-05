# Layout taxonomy

_Generated from `src/slidekit/catalog/registry.py` by `scripts/build_layout_taxonomy.py` — do not hand-edit. A test (`tests/test_catalog`) fails if it drifts._

**29 components** implement **21 distinct layout skeletons** (families); **8** are styled variants of a family anchor — same geometry, differing only by marker / colour / orientation / field-set. "40 distinct layouts" would overstate it; the honest figure is **21 distinct layouts**.

## Distinct layout families (21)

| Family | Anchor component | What the skeleton is |
|---|---|---|
| `agenda` | `agenda` | Numbered agenda / table of contents. |
| `card-grid` | `card-grid` | A grid of content cards. |
| `code-block` | `code` | A dark terminal/IDE-style code block. |
| `comparison-matrix` | `comparison-matrix` | An options × criteria grid; 1–2 winning cells highlighted (FB-039). |
| `emphasis-stack` | `section-divider` | Section break with number + title. |
| `funnel` | `funnel` | Narrowing funnel tiers. |
| `icon-text-rows` | `icon-text-rows` | Rows of icon + text. |
| `kpi-grid` | `kpi-grid` | A grid of KPIs (value + rule + label). |
| `marker-list` | `bullet-list` | A simple list of points (no bullet glyphs — operator style rule FB-026). |
| `nested-circles` | `nested-circles` | Nested circles, each stage inside the last (operator-requested 2026-07-05). |
| `process-flow` | `process-steps` | Horizontal numbered process. |
| `pyramid` | `pyramid` | Widening pyramid tiers. |
| `roadmap` | `roadmap` | Phased lanes with header bands. |
| `stat-callout` | `stat-callout` | A row of stat cards (value + label). |
| `swot` | `swot` | A SWOT 2×2 — one defining statement per quadrant (FB-038). |
| `table` | `table-slide` | A data table. |
| `timeline` | `timeline` | Horizontal dated events. |
| `title` | `title-slide` | Deck/section cover. |
| `two-column` | `comparison-columns` | Two titled bulleted columns side by side. |
| `two-panel-list` | `two-panel-list` | Two contrasting bulleted panels (before/after, pros/cons, old/new). |
| `vs-badge` | `this-vs-that` | Head-to-head with a central VS badge. |

## All components mapped to their skeleton

| Component | Family | Role | Differs from anchor by |
|---|---|---|---|
| `agenda` | `agenda` | **anchor** | — |
| `big-number` | `emphasis-stack` | variant | oversized accent value + label (+ context) |
| `bullet-list` | `marker-list` | **anchor** | — |
| `card-grid` | `card-grid` | **anchor** | — |
| `chart-with-insight` | `two-column` | variant | chart (60%) + emphasis takeaway (40%) |
| `code` | `code-block` | **anchor** | — |
| `comparison-columns` | `two-column` | **anchor** | — |
| `comparison-matrix` | `comparison-matrix` | **anchor** | — |
| `definition` | `emphasis-stack` | variant | accent term + definition body |
| `funnel` | `funnel` | **anchor** | — |
| `icon-text-rows` | `icon-text-rows` | **anchor** | — |
| `image-half-bleed` | `two-column` | variant | one column is a half-bleed image |
| `kpi-grid` | `kpi-grid` | **anchor** | — |
| `metric-comparison` | `stat-callout` | variant | adds a delta chip per metric |
| `nested-circles` | `nested-circles` | **anchor** | — |
| `numbered-steps` | `marker-list` | variant | numbered chips (vertical) |
| `process-steps` | `process-flow` | **anchor** | — |
| `pull-quote` | `emphasis-stack` | variant | bold quote + attribution |
| `pyramid` | `pyramid` | **anchor** | — |
| `question` | `emphasis-stack` | variant | single question line |
| `roadmap` | `roadmap` | **anchor** | — |
| `section-divider` | `emphasis-stack` | **anchor** | — |
| `stat-callout` | `stat-callout` | **anchor** | — |
| `swot` | `swot` | **anchor** | — |
| `table-slide` | `table` | **anchor** | — |
| `this-vs-that` | `vs-badge` | **anchor** | — |
| `timeline` | `timeline` | **anchor** | — |
| `title-slide` | `title` | **anchor** | — |
| `two-panel-list` | `two-panel-list` | **anchor** | — |

