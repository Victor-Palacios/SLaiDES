# PDF slide repetition summary

## Why many PDFs have multiple pages

The PDF emitter writes one PDF page for every resolved slide in a deck; it loops through `resolved.slides` and calls `showPage()` after each slide. Therefore a PDF's page count equals the number of slides in the matching `examples/*.yaml` file, not the number of example files.

Most component examples intentionally contain two slides: a reusable `title-slide` cover followed by the component being demonstrated. Only `01_title_slide.yaml` has one slide, because the title slide is itself the demonstration. Larger showcase decks contain more slides: `09_full_deck.yaml` has 5, `10_all_components.yaml` has 8, `demo-5.yaml` has 5, and `agents-in-ai.yaml` has 10.

## Page-count inventory

- 1 page: `01_title_slide.pdf`.
- 2 pages: `02_two_column.pdf` through `08_card_grid.pdf`, `11_section_divider.pdf` through `42_testimonial.pdf`.
- 5 pages: `09_full_deck.pdf`, `demo-5.pdf`.
- 8 pages: `10_all_components.pdf`.
- 10 pages: `agents-in-ai.pdf`.

## Repetition observed

1. **Cover-page repetition:** 41 of the 42 numbered component example PDFs begin with a `title-slide` cover before the actual component slide, which doubles most files from one page to two.
2. **Same narrative scaffold:** most example decks use identical field order and rhythm: theme, page-number settings, then a title slide, then one component slide.
3. **Repeated title/section framing:** full-deck examples reuse `title-slide` as both opener and closer, and many examples use the same centered title/subtitle hierarchy.
4. **Repeated card/list grids:** multi-item content often resolves into similar rows, columns, cards, or quadrants with a heading and short supporting text.
5. **Repeated chrome:** page numbers and palette-driven backgrounds/accents repeat across the example library, which is useful for test stability but visually homogeneous in review PDFs.

## Alternative designs to reduce sameness

### Alternative 1: one-page component specimen

For each component example PDF, remove the cover page and make the component slide self-identifying with a small eyebrow label such as `Component specimen: two-column`. This makes the expectation explicit: one example file produces one example page.

### Alternative 2: contact-sheet catalog

Create a single catalog PDF where each page shows 6 to 9 miniature component specimens with component name, purpose, and supported content fields. This is better for reviewing the library and quickly spotting duplicate design patterns.

### Alternative 3: variant triptych

For repetitive components, show three design variants on one page: baseline, editorial/large-type, and visual/data-forward. This preserves the component's schema while demonstrating how layout, emphasis, and imagery can vary.
