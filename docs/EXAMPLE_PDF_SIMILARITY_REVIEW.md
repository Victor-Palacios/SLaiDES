# Example Output PDF Similarity Review

Date: 2026-06-18

This review covers the generated example PDFs in `examples/pdf/`, with emphasis on the single-slide numbered examples (`01_` through `42_`). The combined and deck PDFs (`09_full_deck.pdf`, `10_all_components.pdf`, `agents-in-ai.pdf`, `demo-5.pdf`, and `combined/all-examples_2026-06-18.pdf`) intentionally reuse the same component layouts, so they are treated as aggregations rather than independent similarity findings.

## Review method

- Compared the example PDF inventory in `examples/pdf/` against the matching YAML examples in `examples/`.
- Checked component names and layout intent in the source examples to identify templates that likely render with nearly identical structure.
- Flagged examples where a viewer scanning thumbnails could reasonably think two outputs are variants of the same slide rather than distinct examples.

## High-similarity pairs to consider differentiating

| Similar examples | Why they look too similar | Suggested differentiation |
| --- | --- | --- |
| `examples/pdf/13_quote_opener.pdf` and `examples/pdf/15_pull_quote.pdf` | Both are centered quote slides with a large quote and attribution. The primary difference is quote styling rather than composition. | Make one a full-bleed quote treatment, add an oversized quotation mark, or move the attribution into a side rail/card. |
| `examples/pdf/16_statement.pdf` and `examples/pdf/18_question.pdf` | Both render as a single oversized centered line/block of text. The semantic difference between statement and question may not be obvious visually. | Give the question slide a prompt-card layout, response space, or large question-mark motif; give the statement slide a manifesto/banner treatment. |
| `examples/pdf/23_before_after.pdf` and `examples/pdf/24_pros_cons.pdf` | Both are two side-by-side titled bullet panels with contrasting marker colors. The content labels change, but the layout reads nearly the same. | Make before/after more directional, e.g. left-to-right arrow, timeline transition, or split-screen transformation; keep pros/cons as balanced columns. |
| `examples/pdf/19_bullet_list.pdf` and `examples/pdf/21_checklist.pdf` | Both are title-plus-vertical-list slides with square markers at the left of each row. Checked/unchecked state is subtle in thumbnail view. | Add checkmark glyphs or progress-state cards for checklist; keep bullet list plain and denser. |
| `examples/pdf/20_feature_list.pdf` and `examples/pdf/22_numbered_steps.pdf` | Both use a title plus repeated horizontal rows with a left-side visual token and heading/body text. Icons vs numbers may not be enough separation. | Make numbered steps a connected process/ladder with arrows; keep feature list as independent rows/cards. |
| `examples/pdf/35_matrix_2x2.pdf` and `examples/pdf/36_swot.pdf` | Both are 2x2 analytical grids. SWOT labels create semantic distinction, but thumbnail structure is essentially the same. | Give SWOT quadrant colors and a central cross label; make matrix-2x2 use axes, quadrant labels, or plotted items. |
| `examples/pdf/33_funnel.pdf` and `examples/pdf/34_pyramid.pdf` | Both are stacked tier diagrams with progressively changing widths. Funnel vs pyramid direction is distinct, but still a close visual family. | Add conversion percentages and downward flow arrows to funnel; make pyramid hierarchical with base/support emphasis and different tier spacing. |

## Medium-similarity clusters

These are not necessarily duplicates, but they share enough visual DNA that they should be reviewed together when expanding the catalog.

### Two-column contrast layouts

- `examples/pdf/02_two_column.pdf`
- `examples/pdf/05_comparison_columns.pdf`
- `examples/pdf/23_before_after.pdf`
- `examples/pdf/24_pros_cons.pdf`
- `examples/pdf/25_this_vs_that.pdf`

These all communicate contrast through left/right grouping. `25_this_vs_that.pdf` has a VS badge, so it is more distinct; the others should avoid sharing identical column proportions, headings, and bullet treatments.

### Emphasis-stack slides

- `examples/pdf/11_section_divider.pdf`
- `examples/pdf/13_quote_opener.pdf`
- `examples/pdf/14_big_number.pdf`
- `examples/pdf/15_pull_quote.pdf`
- `examples/pdf/16_statement.pdf`
- `examples/pdf/17_definition.pdf`
- `examples/pdf/18_question.pdf`

These examples rely on a small number of large centered text elements. They are useful as primitives, but the catalog will feel broader if each has a stronger signature: number badge, definition card, question prompt, divider stripe, quote mark, etc.

### Repeated-card and grid layouts

- `examples/pdf/08_card_grid.pdf`
- `examples/pdf/26_kpi_grid.pdf`
- `examples/pdf/38_team_grid.pdf`
- `examples/pdf/40_image_grid.pdf`
- `examples/pdf/41_logo_wall.pdf`

These are all grids of repeated tiles. They differ by content type, but thumbnails can blur together. Stronger visual hierarchy per use case would help: KPI tiles with dominant numbers, team grid with portrait-first cards, image grid with masonry/caption treatment, logo wall with lighter tiles.

### Chart and metric slides

- `examples/pdf/04_stat_callout.pdf`
- `examples/pdf/14_big_number.pdf`
- `examples/pdf/26_kpi_grid.pdf`
- `examples/pdf/27_chart_slide.pdf`
- `examples/pdf/28_chart_with_insight.pdf`
- `examples/pdf/30_metric_comparison.pdf`

These all center on numerical evidence. They are not direct duplicates, but should be checked for repeated title/number/card positioning, especially when viewed as a sequence in `combined/all-examples_2026-06-18.pdf`.

## Priority recommendations

1. First differentiate the highest-overlap pairs: quote opener vs pull quote, statement vs question, before/after vs pros/cons, bullet list vs checklist, and feature list vs numbered steps.
2. Then add visual signatures to the 2x2 and stacked-shape examples so the analytical catalog does not feel template-repetitive.
3. Finally, review the aggregate PDFs after changes, because repeated components in decks can amplify perceived sameness even when individual examples are acceptable.
