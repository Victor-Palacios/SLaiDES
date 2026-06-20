# Layout selection guide

_Generated from `src/slidekit/catalog/registry.py` by `scripts/build_selection_guide.py` — do not hand-edit. The machine-readable form is `slidekit catalog --json`. A test (`tests/test_catalog`) fails if it drifts._

Pick a component per slide from its **content shape** — no rendering or vision needed. There are **40 components** across **26 distinct layouts**; variants share an anchor's geometry and differ only by marker / colour / orientation / fields.

## agenda — Numbered agenda / table of contents.

- **`agenda`** · capacity 2–8
  - use when: Listing what the deck covers.
  - content shape: an ordered list of section titles
  - required fields: `items`

## card-grid — A grid of content cards.

- **`card-grid`** · capacity 2–8
  - use when: Several peer items as cards.
  - content shape: a set of {title, body, icon?} cards
  - required fields: `cards`

## chart — A single chart.

- **`chart-slide`**
  - use when: One chart is the focus.
  - content shape: one chart (+ optional caption)
  - required fields: `chart`

## code-block — A dark terminal/IDE-style code block.

- **`code`**
  - use when: Showing source code, a CLI session, or a config snippet verbatim.
  - content shape: a block of monospace code/terminal lines
  - required fields: `code`

## comparison-matrix — An options × criteria grid.

- **`comparison-matrix`**
  - use when: Comparing many options across criteria.
  - content shape: row headers × column headers + cells
  - required fields: `options`, `criteria`, `cells`

## emphasis-stack — A single bold centered line — a manifesto/claim.

- **`statement`**
  - use when: One short, high-impact sentence should fill the slide.
  - content shape: one short line of text
  - required fields: `text`
- **`big-number`** · variant of `statement` (oversized accent value + label (+ context))
  - use when: A single number is the whole point.
  - content shape: one dominant value + a label (+ optional context)
  - required fields: `value`, `label`
- **`definition`** · variant of `statement` (accent term + definition body)
  - use when: Introducing/anchoring one key term.
  - content shape: a term + its definition
  - required fields: `term`, `definition`
- **`pull-quote`** · variant of `statement` (bold quote + attribution)
  - use when: Highlighting a testimonial-style line.
  - content shape: a quote + an attribution
  - required fields: `quote`, `attribution`
- **`question`** · variant of `statement` (single question line)
  - use when: Framing a rhetorical/discussion prompt.
  - content shape: one question
  - required fields: `question`
- **`quote-opener`** · variant of `statement` (italic quote + attribution)
  - use when: Leading a section with a quotation.
  - content shape: a quote + an attribution
  - required fields: `quote`, `attribution`
- **`section-divider`** · variant of `statement` (section number + title (two roles))
  - use when: Marking a new section.
  - content shape: a section number + a section title
  - required fields: `number`, `title`

## funnel — Narrowing funnel tiers.

- **`funnel`** · capacity 3–6
  - use when: A converging/narrowing sequence (e.g. a funnel).
  - content shape: ordered tiers that narrow
  - required fields: `stages`

## icon-text-rows — Rows of icon + text.

- **`icon-text-rows`** · capacity 2–6
  - use when: A few labelled points, each with an icon.
  - content shape: rows of {icon, heading, body}
  - required fields: `rows`
- **`feature-list`** · variant of `icon-text-rows` (icon + heading + body per feature) · capacity 2–6
  - use when: Listing product features with icons.
  - content shape: rows of {icon, heading, body}
  - required fields: `features`

## image-full-bleed — A full-bleed image (+ overlay title).

- **`image-full-bleed`**
  - use when: One image should fill the slide.
  - content shape: one image (+ optional overlay title)
  - required fields: `image`

## image-grid — A gallery grid of images.

- **`image-grid`** · capacity 2–4
  - use when: Showing several images together.
  - content shape: a set of images (+ captions)
  - required fields: `images`

## kpi-grid — A grid of KPIs (value + rule + label).

- **`kpi-grid`** · capacity 3–6
  - use when: A dashboard of 3–6 KPIs.
  - content shape: several {value, label} KPIs in a grid
  - required fields: `kpis`

## labeled-image-grid — A grid of people (portrait + name + role).

- **`team-grid`** · capacity 2–9
  - use when: Introducing a team.
  - content shape: members {portrait, name, role}
  - required fields: `members`
- **`logo-wall`** · variant of `team-grid` (logo tiles (image/label) instead of portrait+name+role) · capacity 3–12
  - use when: Showing customer/partner logos.
  - content shape: logo tiles {image|label}
  - required fields: `logos`

## marker-list — A simple bulleted list.

- **`bullet-list`** · capacity 2–8
  - use when: A plain vertical list of points.
  - content shape: a list of short lines
  - required fields: `title`, `items`
- **`numbered-steps`** · variant of `bullet-list` (numbered chips (vertical)) · capacity 2–6
  - use when: Sequential steps, read top-down.
  - content shape: ordered {title, body} steps
  - required fields: `steps`

## matrix-2x2 — A 2×2 axes matrix.

- **`matrix-2x2`**
  - use when: Plotting items against two axes / four quadrants.
  - content shape: four quadrants (+ axis labels)
  - required fields: `x_label`, `y_label`, `quadrants`

## process-flow — Horizontal numbered process.

- **`process-steps`** · capacity 2–5
  - use when: A left-to-right sequence of steps.
  - content shape: ordered {label, body} steps (horizontal)
  - required fields: `steps`

## pyramid — Widening pyramid tiers.

- **`pyramid`** · capacity 3–6
  - use when: A hierarchy built on a broad base.
  - content shape: ordered tiers that widen
  - required fields: `layers`

## roadmap — Phased lanes with header bands.

- **`roadmap`** · capacity 2–5
  - use when: A roadmap of phases each with items.
  - content shape: phases, each a titled list of items
  - required fields: `phases`

## stat-callout — A row of stat cards (value + label).

- **`stat-callout`** · capacity 2–4
  - use when: 2–4 headline stats in a row.
  - content shape: several {value, label} pairs
  - required fields: `stats`
- **`metric-comparison`** · variant of `stat-callout` (adds a delta chip per metric) · capacity 2–3
  - use when: Showing metrics plus up/down deltas.
  - content shape: several {value, label, delta} metrics
  - required fields: `metrics`

## swot — A SWOT 2×2 of titled bulleted panels.

- **`swot`**
  - use when: A SWOT analysis specifically.
  - content shape: four titled groups of bullets
  - required fields: `strengths`, `weaknesses`, `opportunities`, `threats`

## table — A data table.

- **`table-slide`**
  - use when: Tabular rows and columns of values.
  - content shape: a header row + body rows
  - required fields: `headers`, `rows`

## testimonial — A testimonial (portrait + quote + name/role).

- **`testimonial`**
  - use when: One customer quote with a face.
  - content shape: a quote + name + role (+ portrait)
  - required fields: `quote`, `name`, `role`

## timeline — Horizontal dated events.

- **`timeline`** · capacity 2–6
  - use when: A sequence of dated milestones.
  - content shape: ordered {date, title, description} events
  - required fields: `events`

## title — Deck/section cover.

- **`title-slide`**
  - use when: Opening or closing a deck or a major section.
  - content shape: a title (+ optional subtitle/logo), no body content
  - required fields: `title`

## two-column — Two weighted columns of free content.

- **`two-column`**
  - use when: Two parallel content groups (text/images) side by side.
  - content shape: two groups of content slots
  - required fields: `left`, `right`
- **`chart-with-insight`** · variant of `two-column` (chart (60%) + emphasis takeaway (40%))
  - use when: A chart needs a one-line 'so what'.
  - content shape: one chart + a short insight
  - required fields: `chart`, `insight`
- **`comparison-columns`** · variant of `two-column` (fixed 50/50, titled, bulleted)
  - use when: Comparing two labelled options.
  - content shape: two titled groups of bullets
  - required fields: `left_title`, `right_title`, `left_items`, `right_items`
- **`image-half-bleed`** · variant of `two-column` (one column is a half-bleed image)
  - use when: A supporting image should share the slide with text.
  - content shape: one image + a group of content slots
  - required fields: `image`, `content`

## two-panel-list — Two contrasting bulleted panels (before vs after).

- **`before-after`**
  - use when: Showing a transformation between two states.
  - content shape: two titled groups of bullets (states)
  - required fields: `before`, `after`
- **`pros-cons`** · variant of `before-after` (pros (accent) vs cons (muted) colour roles)
  - use when: Weighing advantages against disadvantages.
  - content shape: two titled groups of bullets (for/against)
  - required fields: `pros`, `cons`

## vs-badge — Head-to-head with a central VS badge.

- **`this-vs-that`**
  - use when: A direct A-vs-B face-off.
  - content shape: two short values opposed by a VS
  - required fields: `left`, `right`

