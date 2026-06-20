# Layout taxonomy

_Generated from `src/slidekit/catalog/registry.py` by `scripts/build_layout_taxonomy.py` — do not hand-edit. A test (`tests/test_catalog`) fails if it drifts._

**40 components** implement **26 distinct layout skeletons** (families); **14** are styled variants of a family anchor — same geometry, differing only by marker / colour / orientation / field-set. "40 distinct layouts" would overstate it; the honest figure is **26 distinct layouts**.

## Distinct layout families (26)

| Family | Anchor component | What the skeleton is |
|---|---|---|
| `agenda` | `agenda` | Numbered agenda / table of contents. |
| `card-grid` | `card-grid` | A grid of content cards. |
| `chart` | `chart-slide` | A single chart. |
| `code-block` | `code` | A dark terminal/IDE-style code block. |
| `comparison-matrix` | `comparison-matrix` | An options × criteria grid. |
| `emphasis-stack` | `statement` | A single bold centered line — a manifesto/claim. |
| `funnel` | `funnel` | Narrowing funnel tiers. |
| `icon-text-rows` | `icon-text-rows` | Rows of icon + text. |
| `image-full-bleed` | `image-full-bleed` | A full-bleed image (+ overlay title). |
| `image-grid` | `image-grid` | A gallery grid of images. |
| `kpi-grid` | `kpi-grid` | A grid of KPIs (value + rule + label). |
| `labeled-image-grid` | `team-grid` | A grid of people (portrait + name + role). |
| `marker-list` | `bullet-list` | A simple bulleted list. |
| `matrix-2x2` | `matrix-2x2` | A 2×2 axes matrix. |
| `process-flow` | `process-steps` | Horizontal numbered process. |
| `pyramid` | `pyramid` | Widening pyramid tiers. |
| `roadmap` | `roadmap` | Phased lanes with header bands. |
| `stat-callout` | `stat-callout` | A row of stat cards (value + label). |
| `swot` | `swot` | A SWOT 2×2 of titled bulleted panels. |
| `table` | `table-slide` | A data table. |
| `testimonial` | `testimonial` | A testimonial (portrait + quote + name/role). |
| `timeline` | `timeline` | Horizontal dated events. |
| `title` | `title-slide` | Deck/section cover. |
| `two-column` | `two-column` | Two weighted columns of free content. |
| `two-panel-list` | `before-after` | Two contrasting bulleted panels (before vs after). |
| `vs-badge` | `this-vs-that` | Head-to-head with a central VS badge. |

## All components mapped to their skeleton

| Component | Family | Role | Differs from anchor by |
|---|---|---|---|
| `agenda` | `agenda` | **anchor** | — |
| `before-after` | `two-panel-list` | **anchor** | — |
| `big-number` | `emphasis-stack` | variant | oversized accent value + label (+ context) |
| `bullet-list` | `marker-list` | **anchor** | — |
| `card-grid` | `card-grid` | **anchor** | — |
| `chart-slide` | `chart` | **anchor** | — |
| `chart-with-insight` | `two-column` | variant | chart (60%) + emphasis takeaway (40%) |
| `code` | `code-block` | **anchor** | — |
| `comparison-columns` | `two-column` | variant | fixed 50/50, titled, bulleted |
| `comparison-matrix` | `comparison-matrix` | **anchor** | — |
| `definition` | `emphasis-stack` | variant | accent term + definition body |
| `feature-list` | `icon-text-rows` | variant | icon + heading + body per feature |
| `funnel` | `funnel` | **anchor** | — |
| `icon-text-rows` | `icon-text-rows` | **anchor** | — |
| `image-full-bleed` | `image-full-bleed` | **anchor** | — |
| `image-grid` | `image-grid` | **anchor** | — |
| `image-half-bleed` | `two-column` | variant | one column is a half-bleed image |
| `kpi-grid` | `kpi-grid` | **anchor** | — |
| `logo-wall` | `labeled-image-grid` | variant | logo tiles (image/label) instead of portrait+name+role |
| `matrix-2x2` | `matrix-2x2` | **anchor** | — |
| `metric-comparison` | `stat-callout` | variant | adds a delta chip per metric |
| `numbered-steps` | `marker-list` | variant | numbered chips (vertical) |
| `process-steps` | `process-flow` | **anchor** | — |
| `pros-cons` | `two-panel-list` | variant | pros (accent) vs cons (muted) colour roles |
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
| `team-grid` | `labeled-image-grid` | **anchor** | — |
| `testimonial` | `testimonial` | **anchor** | — |
| `this-vs-that` | `vs-badge` | **anchor** | — |
| `timeline` | `timeline` | **anchor** | — |
| `title-slide` | `title` | **anchor** | — |
| `two-column` | `two-column` | **anchor** | — |

