# Visual Storyteller → Deck Builder handoff

**Deck:** Meridian Analytics — sales pitch (4 slides)
**Prepared by:** Visual Storyteller / Content Creator
**Consumed by:** Deck Builder

This is the second upstream artifact in the orchestrated pipeline. It is a
structured slide outline in exactly the markdown shape the Deck Builder's
"From Visual Storyteller / Content Creator" seam expects: one `## Slide N`
block per slide, each carrying `intent`, a suggested `component`, the `copy`,
and `assets`. The component suggestions are advisory — the Deck Builder may
switch components if the copy will not fit one.

## Slide 1
- intent: Open with the product name and a one-line promise.
- component: title-slide
- copy: Title "Meridian Analytics"; subtitle "Turn raw events into decisions".
- assets: none

## Slide 2
- intent: Lead with the proof — three numbers that make teams switch.
- component: stat-callout
- copy: "Why Teams Switch". 3.2x Faster Insights (median query time); 40% Lower Cost (vs prior stack); 99.9% Uptime (trailing 12 months).
- assets: none

## Slide 3
- intent: Explain the product in three steps, each with a glanceable icon.
- component: icon-text-rows
- copy: "How It Works". Ingest — stream events from any source. Model — define metrics once, reuse everywhere. Decide — dashboards update in real time.
- assets: icons bolt, check, chart

## Slide 4
- intent: Contrast the old spreadsheet workflow with Meridian, point by point.
- component: comparison-columns
- copy: "Old Way vs Meridian". Left "Spreadsheets": manual exports, stale numbers, no lineage. Right "Meridian": live pipelines, always current, full lineage.
- assets: none
