# Layout selection guide

_Generated from `src/slidekit/catalog/registry.py` by `scripts/build_selection_guide.py` — do not hand-edit. The machine-readable form is `slidekit catalog --json`. A test (`tests/test_catalog`) fails if it drifts._

Pick a component per slide from its **content shape** — no rendering or vision needed. There are **29 components** across **21 distinct layouts**; variants share an anchor's geometry and differ only by marker / colour / orientation / fields.

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

## code-block — A dark terminal/IDE-style code block.

- **`code`**
  - use when: Showing source code, a CLI session, or a config snippet verbatim.
  - content shape: a block of monospace code/terminal lines
  - required fields: `code`

## comparison-matrix — An options × criteria grid; 1–2 winning cells highlighted (FB-039).

- **`comparison-matrix`**
  - use when: Comparing many options across criteria.
  - content shape: row headers × column headers + cells (+ up to 2 highlight cells)
  - required fields: `options`, `criteria`, `cells`

## emphasis-stack — Section break with number + title.

- **`section-divider`**
  - use when: Marking a new section.
  - content shape: a section number + a section title
  - required fields: `number`, `title`
- **`big-number`** · variant of `section-divider` (oversized accent value + label (+ context))
  - use when: A single number is the whole point.
  - content shape: one dominant value + a label (+ optional context)
  - required fields: `value`, `label`
- **`definition`** · variant of `section-divider` (accent term + definition body)
  - use when: Introducing/anchoring one key term.
  - content shape: a term + its definition
  - required fields: `term`, `definition`
- **`pull-quote`** · variant of `section-divider` (bold quote + attribution)
  - use when: Highlighting a quote/testimonial line.
  - content shape: a quote + an attribution
  - required fields: `quote`, `attribution`
- **`question`** · variant of `section-divider` (single question line)
  - use when: Framing a rhetorical/discussion prompt.
  - content shape: one question
  - required fields: `question`

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

## kpi-grid — A grid of KPIs (value + rule + label).

- **`kpi-grid`** · capacity 3–6
  - use when: A dashboard of 3–6 KPIs.
  - content shape: several {value, label} KPIs in a grid
  - required fields: `kpis`

## marker-list — A simple list of points (no bullet glyphs — operator style rule FB-026).

- **`bullet-list`** · capacity 2–8
  - use when: A plain vertical list of points.
  - content shape: a list of short lines
  - required fields: `title`, `items`
- **`numbered-steps`** · variant of `bullet-list` (numbered chips (vertical)) · capacity 2–6
  - use when: Sequential steps, read top-down.
  - content shape: ordered {title, body} steps
  - required fields: `steps`

## nested-circles — Nested circles, each stage inside the last (operator-requested 2026-07-05).

- **`nested-circles`** · capacity 2–4
  - use when: A narrowing sequence where each stage is a SUBSET of the previous (applications → interviews → offers).
  - content shape: ordered {value, label} stages, each a subset of the last
  - required fields: `stages`

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

## swot — A SWOT 2×2 — one defining statement per quadrant (FB-038).

- **`swot`**
  - use when: A SWOT analysis specifically.
  - content shape: four titled single statements
  - required fields: `strengths`, `weaknesses`, `opportunities`, `threats`

## table — A data table.

- **`table-slide`**
  - use when: Tabular rows and columns of values.
  - content shape: a header row + body rows
  - required fields: `headers`, `rows`

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

## two-column — Two titled bulleted columns side by side.

- **`comparison-columns`**
  - use when: Comparing two labelled options or presenting two parallel groups.
  - content shape: two titled groups of bullets
  - required fields: `left_title`, `right_title`, `left_items`, `right_items`
- **`chart-with-insight`** · variant of `comparison-columns` (chart (60%) + emphasis takeaway (40%))
  - use when: A chart needs a one-line 'so what'.
  - content shape: one chart + a short insight
  - required fields: `chart`, `insight`
- **`image-half-bleed`** · variant of `comparison-columns` (one column is a half-bleed image)
  - use when: A supporting image should share the slide with text.
  - content shape: one image + a group of content slots
  - required fields: `image`, `content`

## two-panel-list — Two contrasting bulleted panels (before/after, pros/cons, old/new).

- **`two-panel-list`**
  - use when: Contrasting two states or weighing two sides; the right panel is the accented one.
  - content shape: two titled groups of bullets (contrasting states)
  - required fields: `left`, `right`

## vs-badge — Head-to-head with a central VS badge.

- **`this-vs-that`**
  - use when: A direct A-vs-B face-off.
  - content shape: two short values opposed by a VS
  - required fields: `left`, `right`

