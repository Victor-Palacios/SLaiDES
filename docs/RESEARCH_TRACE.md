# Research trace — which paper influenced which decision

A single, auditable map from each **design decision in the aesthetic scorer** to the
**reference that influenced it**. It exists so the claim "the metrics are grounded in
research" can be checked, not just asserted.

- **Ref #N** points to the numbered entry in [`REFERENCES.md`](REFERENCES.md).
- **Status** is that reference's verification status (VERIFIED = confirmed from a
  primary source; SECONDHAND = carried from an operator synthesis, not yet confirmed).
- **Code** is the function/constant in [`../src/slidekit/aesthetics/score.py`](../src/slidekit/aesthetics/score.py)
  that implements the decision, with a matching `# ref #N` comment.
- **HEURISTIC (no primary source)** means the decision is our own engineering judgment,
  *not* taken from a paper. These are flagged honestly rather than dressed up with a
  loosely-related citation.

> Honesty note: an earlier description claimed "every sub-score traces to a verified
> paper." That was an overstatement. The truth is below: some sub-scores trace to a
> verified paper, some to a web standard, and some are our own heuristics with no
> primary source. This file is the corrected, complete record.

## Sub-scores

| Decision | Code | Ref | Status | Notes |
|---|---|---|---|---|
| Compute aesthetics from native geometry with **no rendering, no vision** | whole module | #1 AeSlides | VERIFIED | AeSlides defines "verifiable" layout metrics but computes them over **Playwright-rendered pixels** with proprietary formulas. slidekit's distinction: equivalent metrics over the exact `ResolvedDeck` geometry, open formulas, zero render. |
| **balance** — area-weighted moment about the centre axes (H + V scored separately) | `_balance` | #4 Ngo/Teo/Byrne; #16 Lok/Feiner/Ngai; #18 Zhang & Xue | VERIFIED | Ngo's "balance / equilibrium" over element bounding boxes, computed as the normalised difference of Σ(area × distance-from-axis) moments on the two sides of each axis; corroborated by #16/#18 (moment / symmetry models). The earlier single centroid-offset was the degenerate special case. (#9 Birkhoff is the conceptual ancestor but is SECONDHAND — not relied on.) |
| **whitespace** — coverage band only (occupied area ÷ canvas) | `_whitespace` | #1 AeSlides | VERIFIED | AeSlides "excessive whitespace" as a verifiable defect. The specific band `0.12–0.55` is **HEURISTIC (no primary source)** — our chosen comfortable-coverage range. Whitespace *distribution* evenness is **not** a separate term: an off-centre dominant void is already captured by `_balance`. A largest-empty-rectangle ("white-space free-flow", refs #10 Harrington / #14 O'Donovan) metric was evaluated 2026-06-22 and found redundant with balance — see NOTES.md. |
| **alignment** — reward **left edges** snapping to few implied columns | `_alignment` | #3 GRIDS; cf. #4 Ngo | VERIFIED | GRIDS treats alignment as an explicit layout objective (MILP constraint). Scoped to **left edges only** (one component of Ngo's `n_vap`), NOT Ngo's full x+y `1−(n_vap+n_hap)/2n`: the symmetric form roughly halves clean single-column text stacks (0.40 vs 0.80 for a 5-bullet column), so it is **not adopted** — see the alignment design note in AESTHETICS.md (assessed 2026-06-23). Tolerance `~0.06"` is **HEURISTIC**. |
| **non_overlap** — `1 − Σ intersection / Σ area`, excluding text inside its own container | `_non_overlap`, `_contains` | #1 AeSlides | VERIFIED | AeSlides "element collision." A label drawn inside its tile/band/image is intentional containment, not a collision, so those pairs are excluded (otherwise every designed box+label reads as overlap). |
| **contrast** — size-aware WCAG (3:1 ≥24pt, 4.5:1 below), judged against the text's ACTUAL background | `_contrast`, `_text_background`, `_LARGE_TEXT_PT`, `_TARGET_*` | WCAG 2.x + #11 Rebelo et al. | standard + VERIFIED | Thresholds are the **WCAG 2.x** web standard and PLAN.md Phase 4. WCAG contrast is text vs its real background, so a label on a filled tile is judged against the tile fill (not the slide surface); text over an image is unmeasurable and not penalised. #11 (EvoMUSART 2024) backs contrast-as-constraint. |
| **richness** — accent emphasis + structure + restrained colour variety | `_richness` | #12 Reinecke et al. (CHI 2013) | VERIFIED | Perceived colourfulness/complexity models. slidekit uses **palette colour variety** as a no-render proxy for colourfulness. The `0.45/0.35/0.20` split and the variety falloff past 3 colours are **HEURISTIC**. |
| **color_harmony** — hue-angle relationship between palette roles | `_color_harmony` | #19 Cohen-Or et al. (SIGGRAPH 2006) | VERIFIED (templates + exact widths) / HEURISTIC (tolerance) | Cohen-Or's **harmonic hue-wheel templates** (i/V/L/I/T/Y/X — pairs/sectors at fixed angular relationships) are the primary basis for rewarding palette roles in a recognised hue relationship (mono/analogous/complementary/triadic). **Exact sector widths now verified from the paper's Appendix (2026-06-26):** small sectors (i,L,I,Y) **18°**, large (V,Y,X) **93.6°**, L's large **79.2°**, T **180°**; centre separations **180°** (I/X/Y) and **90°** (L). slidekit's **30° falloff lies within** the 18°–93.6° range and its 180° reward matches the I/X/Y centre separation, so it is **consistent with** the published geometry — but **30° is not stated by the paper** (the published widths are 18/79.2/93.6/180°) and the 120°/150° reward angles trace to the artist colour-wheel tradition (Itten), not Cohen-Or's 90°/180° centres. The 30° tolerance therefore stays **HEURISTIC**. |
| **info_density** — words-per-slide + text-coverage vs comfortable bands | `_info_density`, `_band` | #20 Alley & Neeley (Tech. Comm. 2005) | VERIFIED (direction) / HEURISTIC (bands) | Alley & Neeley's **assertion–evidence** work is a presentation-specific primary source against text-dense slides (one idea per slide; text density impedes comprehension) — backs the metric's *direction* (penalise crowding). The word band `[1,45]→0@130` is generous on the low end so sparse hero layouts aren't penalised; coverage band `[0.02,0.45]→0@0.85`. The exact bands are **HEURISTIC**. Image-only slides earn full credit. |
| **hierarchy** — title:body size-ratio band | `_hierarchy` | #21 van Gog (signaling/cueing principle); #22 Brown (modular scale) | VERIFIED (direction + ratio family) / **HEURISTIC** (exact band) | #21 (Cambridge Handbook of Multimedia Learning, 2021) is the primary basis for the metric's *direction*: cues that **highlight the organization** of material — explicitly including text headings/emphasis — improve learning, so a clear title→body size step is a structural cue worth rewarding. The **1.5× threshold is now BOUNDED** (was "attested secondhand"): #22 (Brown, "More Meaningful Typography", A List Apart 2011, verified by fetching the primary article) defines the modular-scale convention — quoting Bringhurst's *Elements of Typographic Style* ("Shaping the Page") — and builds a scale from a chosen harmonious ratio whose menu includes the **perfect fifth (3:2 = 1.5)** and golden ratio (1.618). So 1.5 is the perfect-fifth member of an established harmonious-ratio family (the just perfect fifth is the 3:2 ratio = 1.5 by definition), **not arbitrary**. It **stays HEURISTIC** only because the source prescribes a *menu* (1.25/1.414/1.5/1.618…), not a single title:body value — slidekit's selection of 1.5 is "consistent-with, not stated-by" (parallel to #19 color_harmony). |
| **cross_slide_consistency** — deck multiplier on margin variance | `_cross_slide_consistency` | #7 PPTEval, #8 DECKBench | VERIFIED (direction) / **HEURISTIC** (formula) | Both references are now **VERIFIED** from primary sources (#7 2026-06-16, #8 2026-06-17), and #7's deck-level *Coherence* axis is human-correlated (Pearson 0.55) — they establish cross-slide coherence as a real, separable axis (the metric's *direction*). The specific **margin-variance** formula and `[0.9,1.0]` bound are slidekit's own **HEURISTIC**, not taken from either paper. |

## Composite & weights

| Decision | Code | Ref | Status | Notes |
|---|---|---|---|---|
| Composite as a **weighted mean** of sub-scores | `score_deck` / `DEFAULT_WEIGHTS` | #9 Birkhoff (M=O/C) | SECONDHAND | Conceptual basis for a single composite score. |
| **Non-linear** combiner (one bad feature dominates) — **BUILT (T-020)** | `_combine_harrington` / `COMBINERS` / `slidekit score --combine harrington` | #10 Harrington et al. (DocEng 2004) | VERIFIED | Weighted **geometric mean** `100·Π subscore_i^{w_i/Σw}` (Harrington desirability): one near-zero sub-score drives the composite toward 0. Opt-in mode alongside the default weighted `mean`; AM-GM ⇒ harrington ≤ mean, equal iff sub-scores uniform. Sub-scores/warnings/deck roll-up mode-independent. |
| Weights `non_overlap/contrast/richness = 1.5`, others 1.0 | `DEFAULT_WEIGHTS` | — | **HEURISTIC (no primary source)** | Our judgment that unreadable/overlapping/bare slides are "ugly" in ways balance can't offset. Weight **calibration is DEFERRED** — would require a labelled slide-pair dataset (cf. #2 EvoPresent's 2,000 pairs). No human-correlation claim is made. |
| `deck = mean(slide scores) · consistency`, consistency bounded `[0.9, 1.0]` | `score_deck` | #7/#8 | VERIFIED (direction) / HEURISTIC (formula) | Gentle deck-level modulation; refs verified, but the multiplier + bound are **HEURISTIC**. |

## Scoreboard

- Sub-scores backed by a **VERIFIED** primary paper: balance (#4/#16/#18), whitespace (#1),
  alignment (#3), non_overlap (#1), richness (#12), color_harmony (#19 templates),
  info_density (#20 direction), hierarchy (#21 direction + #22 ratio family) — plus contrast (WCAG standard + #11).
- Sub-scores still **HEURISTIC with no primary source**: **none** — every sub-score now traces
  at least its *direction* to a verified primary source or web standard. What remains HEURISTIC
  is several internal **constants/bands**: the hierarchy 1.5× threshold (now bounded — shown
  2026-06-27 to be the perfect-fifth (3:2) member of the Bringhurst/Brown modular-scale
  harmonious-ratio family, ref #22, but the source prescribes a *menu* of ratios, not a single
  value), the color_harmony 30° tolerance (now bounded — shown 2026-06-26 to fall *within* Cohen-Or's
  verified 18°–93.6° template sector range, but not a value the paper states), the info_density bands,
  the whitespace 0.12–0.55 band, the alignment 0.06" tolerance — honestly flagged as our engineering
  choices even where the metric's direction (and, for hierarchy/color_harmony, the ratio family /
  template geometry) is sourced.
- References resting on a **conceptual/direction-only** basis (verified papers, but the
  exact slidekit formula is our heuristic): the composite's conceptual basis (#9 Birkhoff,
  verified as a book, used conceptually); cross_slide_consistency cites #7/#8 (both verified;
  as of 2026-06-21 #7's Design/Coherence sub-aspects + Pearson figures are confirmed from the
  full text, so nothing in this trace rests on an *unverified* source any longer — only on
  honestly-labelled heuristic formulas).
- **OPEN research-to-product gaps:** (1) ~~Harrington's non-linear combiner~~ **DONE
  (T-020)** — shipped as the `harrington` combine mode; (2) hierarchy ratio band — the
  *direction* is sourced (**#21 van Gog signaling**, 2026-06-25) and the **1.5× ratio is now
  bounded** to the perfect-fifth (3:2) member of the Bringhurst/Brown modular-scale family
  (**#22 Brown**, verified 2026-06-27); only the *selection* of 1.5 from that ratio menu stays
  HEURISTIC (no empirical title:body value — calibration would settle it);
  (3) weight calibration (DEFERRED, needs a labelled dataset).
- **Ngo #4 measures ASSESSED & DECLINED** (no code): of the 14, balance + density are
  integrated; **regularity, rhythm, spacing-regularity** (2026-06-23) and **proportion,
  economy** (2026-06-24) were each assessed against a primary/faithful source and declined —
  either unfaithful on the scoring function (no extractable closed form: rhythm,
  spacing-regularity, proportion's normalization constant) or redundant/conflicting for
  slides (regularity halves clean text columns; economy penalises deliberate type-scale
  hierarchy; proportion injects content-driven aspect-ratio noise). See NOTES.md +
  REFERENCES.md integration log. Per-measure mining of #4 is now closed; favour
  integration/calibration over further single-measure additions.

_Maintained alongside `REFERENCES.md` and `AESTHETICS.md` by the nightly routine. When a
new metric or threshold is added, add its row here with the ref number and status, and a
matching `# ref #N` comment in `score.py`._
