# Layout taxonomy

_Generated from `src/slidekit/catalog/registry.py` by `scripts/build_layout_taxonomy.py` — do not hand-edit. A test (`tests/test_catalog`) fails if it drifts._

**33 components** implement **22 distinct layout skeletons** (families); **11** are styled variants of a family anchor — same geometry, differing only by marker / colour / orientation / field-set. "40 distinct layouts" would overstate it; the honest figure is **22 distinct layouts**.

## Distinct layout families (22)

| Family | Anchor component | What the skeleton is |
|---|---|---|
| `agenda` | `agenda` | Numbered agenda / table of contents. |
| `card-grid` | `card-grid` | A grid of content cards. |
| `code-block` | `code` | A dark terminal/IDE-style code block. |
| `comparison-matrix` | `comparison-matrix` | An options × criteria grid; 1–2 winning cells highlighted (FB-039). |
| `emphasis-stack` | `statement` | A single bold centered line — a manifesto/claim. |
| `funnel` | `funnel` | Narrowing funnel tiers. |
| `icon-text-rows` | `icon-text-rows` | Rows of icon + text. |
| `kpi-grid` | `kpi-grid` | A grid of KPIs (value + rule + label). |
| `labeled-image-grid` | `logo-wall` | A wall of logos. |
| `marker-list` | `bullet-list` | A simple list of points (no bullet glyphs — operator style rule FB-026). |
| `matrix-2x2` | `matrix-2x2` | A 2×2 axes matrix. |
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
| `feature-list` | `icon-text-rows` | variant | icon + heading + body per feature |
| `funnel` | `funnel` | **anchor** | — |
| `icon-text-rows` | `icon-text-rows` | **anchor** | — |
| `image-half-bleed` | `two-column` | variant | one column is a half-bleed image |
| `kpi-grid` | `kpi-grid` | **anchor** | — |
| `logo-wall` | `labeled-image-grid` | **anchor** | — |
| `matrix-2x2` | `matrix-2x2` | **anchor** | — |
| `metric-comparison` | `stat-callout` | variant | adds a delta chip per metric |
| `numbered-steps` | `marker-list` | variant | numbered chips (vertical) |
| `process-steps` | `process-flow` | **anchor** | — |
| `pull-quote` | `emphasis-stack` | variant | bold quote + attribution |
| `pyramid` | `pyramid` | **anchor** | — |
| `question` | `emphasis-stack` | variant | single question line |
| `quote-opener` | `emphasis-stack` | variant | italic quote + attribution |
| `roadmap` | `roadmap` | **anchor** | — |
| `section-divider` | `emphasis-stack` | variant | section number + title (two roles) |
| `stat-callout` | `stat-callout` | **anchor** | — |
| `statement` | `emphasis-stack` | **anchor** | — |
| `swot` | `swot` | **anchor** | — |
| `table-slide` | `table` | **anchor** | — |
| `this-vs-that` | `vs-badge` | **anchor** | — |
| `timeline` | `timeline` | **anchor** | — |
| `title-slide` | `title` | **anchor** | — |
| `two-panel-list` | `two-panel-list` | **anchor** | — |

