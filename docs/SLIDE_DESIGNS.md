# slidekit slide-design catalog — 37 components (25 distinct layouts)

Target: **40 slide components** (up from the 8 shipped in v1). Each component is a
slidekit unit: one Pydantic model + one layout handler + golden test + example
+ SKILL gallery row. This file is the build blueprint for Phase 9.

Honesty note: the 37 components implement **25 genuinely distinct layout skeletons** —
the rest are styled variants of a family anchor (same geometry, different marker / colour /
orientation / fields). The authoritative mapping is generated in
[LAYOUT_TAXONOMY.md](LAYOUT_TAXONOMY.md) from `src/slidekit/catalog/registry.py`.

> **Research reconciliation pending.** Two research sources (a ChatGPT share and a
> Grok share) were provided to inform this catalog, but the execution environment's
> network egress allowlist blocks `chatgpt.com` and `grok.com`, so they could not be
> read. This catalog is drawn from established presentation-design practice. When the
> sources are made reachable (add the hosts to egress settings) or pasted in, diff
> them against this list and adjust before/while building.

## Where it fits in the repo (integration points per design)

Each new design touches the same five places the existing 8 do:

1. `src/slidekit/ir/models.py` — a `*Slide` Pydantic model with `component: Literal["<key>"]`
   and typed slot fields; add it to the slide `Union`.
2. `src/slidekit/layout/engine.py` — a `_layout_<key>()` handler returning `ResolvedNode`s,
   plus an `elif comp == "<key>"` branch in `_resolve_slide`'s dispatch.
3. `src/slidekit/lint/checks.py` — usually nothing (checks are generic over ResolvedNodes);
   add only design-specific rules if needed.
4. `tests/test_layout/golden/<key>.json` + an `examples/NN_<key>.yaml` example deck — a
   single-slide **specimen** of just this component (no `title-slide` cover; only the
   `09_full_deck`/`10_all_components`/`agents-in-ai`/`demo-5` showcases are multi-slide).
5. `SKILL.md` — one row in the component gallery; and a scaffold template if warranted.

Emit (`emit/pptx_emitter.py`) and the verify harness are already generic over
`ResolvedNode`, so most designs need no emitter changes.

## Design principle

Favor **deterministic, text/box/icon/image/chart** layouts (no freehand connectors).
Shapes like funnels, pyramids, and quadrants are colored rectangles with labels —
fully measurable, so the linter still proves fit. Keep every design on the 32pt body
floor and metric-safe fonts.

---

## The 40 designs

Legend: ✓ = already shipped in v1.  Slots use the existing typed slot vocabulary
(`text`, `image`, `icon`, `chart`, `spacer`).

### A. Openers & dividers
| # | key | required keys | use |
|---|---|---|---|
| 1 | ✓ `title-slide` | `title` (+`subtitle`,`logo`) | deck cover |
| 2 | `section-divider` | `number`, `title` | chapter break between sections |
| 3 | `agenda` | `items[]` (text) | table of contents / what's ahead |
| 4 | `quote-opener` | `quote`, `attribution` | open on a strong quotation |

### B. Single-message & emphasis
| # | key | required keys | use |
|---|---|---|---|
| 5 | `big-number` | `value`, `label` (+`context`) | one hero metric, full slide |
| 6 | `pull-quote` | `quote`, `attribution` | mid-deck emphasis quote |
| 7 | `statement` | `text` | one bold thesis sentence, centered |
| 8 | `definition` | `term`, `definition` | define a key concept |
| 9 | `question` | `question` | a single framing question |

### C. Lists & text
| # | key | required keys | use |
|---|---|---|---|
| 10 | ~~`two-column`~~ | _(retired 2026-07-02, FB-009)_ | redundant with `comparison-columns`, which now anchors the two-column family |
| 11 | `bullet-list` | `title`, `items[]` | a single titled list |
| 12 | ✓ `icon-text-rows` | `rows[]` = {icon,heading,body} | ~3 labelled points |
| 13 | `feature-list` | `features[]` = {icon,heading,body} | 3–5 features, denser |
| 14 | `checklist` | `items[]` = {text, checked?} | requirements / done-list |
| 15 | `numbered-steps` | `steps[]` = {title,body} | ordered vertical steps |

### D. Comparison
| # | key | required keys | use |
|---|---|---|---|
| 16 | ✓ `comparison-columns` | `left_title`,`right_title`,`left_items[]`,`right_items[]` | A vs B lists |
| 17 | `two-panel-list` | `left`/`right`={title,items[]} | any two-state contrast (before/after, pros/cons) |
| 19 | `this-vs-that` | `left`={value,label}, `right`={value,label} | two headline numbers head-to-head |

### E. Data & stats
| # | key | required keys | use |
|---|---|---|---|
| 20 | ✓ `stat-callout` | `stats[]` = {value,label,subtext?} | 3 headline numbers |
| 21 | `kpi-grid` | `kpis[]` = {value,label} (4–6) | dashboard of small metrics |
| 23 | `chart-with-insight` | `chart`, `insight` | chart + takeaway callout |
| 24 | `table-slide` | `headers[]`, `rows[][]` | a small text table |
| 25 | `metric-comparison` | `metrics[]` = {value,label,delta?} | 2–3 metrics with change |

### F. Process & flow
| # | key | required keys | use |
|---|---|---|---|
| 26 | `process-steps` | `steps[]` = {label,body} | horizontal numbered flow |
| 27 | ✓ `timeline` | `events[]` = {date,title,description?} | dated milestones |
| 28 | `roadmap` | `phases[]` = {title,items[]} | phased plan across lanes |
| 29 | `funnel` | `stages[]` = {label,value?} | narrowing stages |
| 30 | `pyramid` | `layers[]` = {label} | layered hierarchy |
| 31 | `matrix-2x2` | `x_label`,`y_label`,`quadrants[4]` | quadrant positioning |
| 32 | `swot` | `strengths[]`,`weaknesses[]`,`opportunities[]`,`threats[]` | 4-quadrant analysis |

### G. Structured relationships
| # | key | required keys | use |
|---|---|---|---|
| 33 | ✓ `comparison-matrix` | `options[]`, `criteria[]`, `cells[][]` | features × options grid |
| 34 | `card-grid` ✓ | `cards[]` = {title,body,icon?} | grid of short cards |
| 35 | ✓ `team-grid` | `members[]` = {name,role,image?} | people / team |

### H. Visual & image
| # | key | required keys | use |
|---|---|---|---|
| 36 | ✓ `image-half-bleed` | `image`, `content[]` (+`image_side`) | image beside text |
| 37 | ✓ `image-full-bleed` | `image` (+`overlay_title`) | full-bleed image + overlay |
| 38 | ✓ `image-grid` | `images[]` (2–4) (+`captions`) | gallery |
| 39 | ✓ `logo-wall` | `logos[]` = {image|label} | client / partner logos |
| 40 | ✓ `testimonial` | `quote`,`name`,`role` (+`image`) | customer testimonial |

### Closing (reuse openers)
A closing / call-to-action slide is covered by `statement` (#7), `big-number` (#5),
or `title-slide` (#1) with a CTA subtitle — no separate component needed.

---

## Build order (Phase 9)

Build in catalog order, **skipping the 8 already shipped**. Each design ships
complete (model + handler + dispatch + golden test + example + SKILL row) and
lint-clean before the next starts. Group suggestion per session (Opus): ~4–6 designs.
Hardest (deterministic shape math): `funnel`, `pyramid`, `matrix-2x2`, `swot`,
`comparison-matrix`, `table-slide` — give these extra care and their own golden tests.
