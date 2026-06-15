# Computational aesthetics for slidekit — Phase 10 integration

This integrates operator-provided research (synthesized from the AeSlides,
EvoPresent, GRIDS, Ngo/Teo/Byrne, SlidesGen-Bench, "Seeing Like a Designer
Without One", PPTAgent/PPTEval, DECKBench, and Birkhoff lines of work) into
slidekit. The two original sources were ChatGPT/Grok shares blocked by the
egress allowlist; the operator pasted the synthesis, recorded here.

## Premise (what the research establishes)

Slide aesthetics are **not purely subjective**. Important components — layout
balance, alignment, whitespace, contrast, non-overlap, color harmony, cross-slide
consistency, information density, visual hierarchy — can be **formally defined,
measured, optimized, and validated against human judgment**. Reported human
correlations: "Seeing Like a Designer" up to Pearson **0.83** on 7 visual metrics;
PPTEval design dimension up to Pearson **0.90**. AeSlides defines verifiable
metrics (aspect ratio, excessive whitespace, element collision, visual imbalance)
and optimizes them with RL. GRIDS shows layout objectives (alignment, balance,
grouping, packing) become MILP constraints. Caveat the research itself states:
this is **not** a universal "beauty equation" — weights and thresholds are
calibratable proxies, and cultural/subjective factors remain.

## Why this fits slidekit exactly

slidekit already produces a **ResolvedDeck**: every node carries an exact EMU rect,
and the theme defines exact colors and fonts. So every metric below is **arithmetic
over geometry slidekit already computes** — deterministic, reproducible, **zero
rendering, zero vision**. This is the same thesis as the Phase 4 linter, extended
from "no user-visible defects" (pass/fail) to "measurably well-composed" (a score
with reasons). It stays fully within the project's no-screenshot rule: aesthetics
are proven from source, like correctness.

## Metric definitions (computed over ResolvedDeck)

Per slide, `elements = [node rects (x,y,w,h)]` plus theme colors. Each sub-score is
normalized to [0,1]:

| Sub-score | Definition over the resolved geometry | Lineage |
|---|---|---|
| **Balance** | area-weighted centroid of element rects vs. slide center; `1 − normalized_distance` | Birkhoff / Ngo equilibrium |
| **Alignment** | cluster element edges (left/right/cx, top/bottom/cy) at a tolerance; reward few distinct alignment lines (elements snap to an implied grid) | GRIDS alignment objective |
| **Whitespace** | empty-area proportion **and** evenness of its distribution (penalize one dominant empty region — slidekit already warns when largest empty > 3× median) | AeSlides excessive-whitespace |
| **Non-overlap** | `1 − (Σ pairwise rect-intersection area / Σ element area)`; intentional `stack` exempt | AeSlides collision; grades the binary E_OVERLAP |
| **Contrast** | min WCAG ratio of text vs. effective background across nodes, normalized | promotes the E_CONTRAST stub to a scored metric |
| **Color harmony** | over the theme palette: hue-angle relationships (complementary/analogous/triadic proximity), saturation/lightness spread, count of distinct hues | computational color theory |
| **Info density** | text-area / content-area and words-per-slide vs. a target band; penalize both crowding and barrenness | "Math Behind Effective Slide Design" |
| **Visual hierarchy** | title:body and header:body size ratios within recommended bands (slidekit already warns < 1.4×) | multimedia-learning research |
| **Cross-slide consistency** (deck-level) | variance across slides of margins, fonts, type sizes, palette usage, component start positions; low variance = coherent | PPTEval coherence; DECKBench deck-level |

## Composite score

```
AestheticScore(slide) = Σ w_i · subscore_i               # weights configurable
AestheticScore(deck)  = mean(slide scores) · CrossSlideConsistency
```
Report per-slide and per-deck on a 0–100 scale with the sub-metric breakdown.

> **Design note (ref #10, Harrington et al., DocEng 2004).** Harrington combines
> geometric layout measures **non-linearly** so that a single bad feature (e.g. one
> overlap or a badly broken margin) dominates rather than being averaged away. When
> Phase 10 is built, offer a configurable aggregation mode alongside the weighted
> sum above — e.g. a penalty/min-skewed combiner `100 · Π subscore_i^{w_i}` or
> `min`-biased mean — so a deck with one severe flaw cannot score well on the
> strength of the others. Default weights/mode stay documented and calibration
> DEFERRED (see below).

## How it surfaces (deterministic, CI-friendly)

- `slidekit score deck.yaml --json` — per-slide + deck score with sub-metric
  breakdown. No rendering; same determinism guarantees as `slidekit layout`.
- New **advisory** warnings `W_AESTH_*` (e.g. `W_AESTH_BALANCE`,
  `W_AESTH_WHITESPACE`) when a sub-score falls below threshold — warnings only,
  never blocking the build (consistent with Phase 4 semantics).
- Optional `--min-score` gate for teams that want a hard aesthetic floor in CI.
- Tie-in to Phase 9: every example deck in the 40-design library should clear a
  baseline aesthetic score by construction; add a test asserting it.

## Validation / calibration (honest scope)

The cited work validates such metrics against human ratings (Pearson 0.83–0.90),
but that requires a **human-labeled slide-pair dataset** (cf. EvoPresent's 2,000
pairs). slidekit v1 of this feature ships the deterministic metrics with sensible
**default weights**, documented with rationale. It must **not** claim human
correlation until calibrated against such a dataset — that is a later, data-
dependent step. The metrics are useful and reproducible immediately as design
guidance; the "matches human taste" claim is gated on calibration data.

## Relationship to the linter

The linter (Phase 4) stays the **gate** (errors block; objective defects). Aesthetic
scoring is an **advisor** (warnings + a score; graded quality). A deck can be
lint-clean yet score 62/100 — that's the intended separation: correctness is binary
and enforced; beauty is graded and advisory.

## Primary-source verification (added 2026-06-14)

The metric set above was first drafted from an operator-pasted synthesis plus
background knowledge — **not** from the primary papers. Follow-up verification
(web search + fetch) established the following, and corrects the record:

- **AeSlides** — arXiv:2604.22840, "Incentivizing Aesthetic Layout in LLM-Based
  Slide Generation via Verifiable Rewards" (2026-04-21; code:
  github.com/ympan0508/aeslides). VERIFIED metrics: distorted aspect ratio,
  excessive whitespace, element collision, visual imbalance; GRPO RL; reported
  aspect-ratio compliance 36%→85%, whitespace −44%, collisions −43%, imbalance
  −28%, human score 3.31→3.56. **KEY DETAIL the synthesis omitted:** AeSlides
  computes these "verifiable" metrics over **Playwright-rendered output**
  (pixel/variance-map analysis) and keeps the full implementation **proprietary**
  ("we do not release the full system implementation… decoupled render
  infrastructure… tool implementations").
- **EvoPresent / PresAesth** — arXiv:2510.05571 (ICLR 2026); multi-task RL (GRPO)
  for scoring / defect-adjustment / pairwise-comparison; benchmark 650 papers +
  2,000 slide pairs. VERIFIED.

**Implication for slidekit (now primary-sourced):** the leading verifiable-metric
system *renders* slides (Playwright) to recover the geometry these metrics need,
and does not publish its formulas. slidekit already has exact geometry from the
ResolvedDeck, so it computes equivalent metrics with **no rendering and no
black box** — but it must define its OWN open formulas (this document). That is a
real, defensible distinction, stronger than first stated.

**STILL UNVERIFIED — treat as secondhand until checked against primary sources:**
GRIDS, Ngo/Teo/Byrne, SlidesGen-Bench, "Seeing Like a Designer Without One"
(Pearson 0.83), PPTAgent/PPTEval (Pearson 0.90), DECKBench, Birkhoff. These
citations and figures come from the pasted synthesis, not from papers I have read.

## First-cut scorer + a key finding (2026-06-14)

A first `slidekit score` shipped (`slidekit/aesthetics/`): deterministic 0–100 over the
ResolvedDeck (balance, whitespace, alignment, non-overlap, hierarchy, contrast). It
immediately exposed the calibration gap this doc warned about: **the geometric metrics
measure tidiness, not beauty.** Plain, sparse decks score AS HIGH OR HIGHER than
richly-designed ones (e.g. a bare deck 92.7 vs a designed big-number slide 86.2), and
accent-coloured emphasis text is wrongly dinged on contrast. Consequences for the build:
- Add a **visual-richness / engagement** sub-score so deliberate accent-colour use and
  non-text elements (within restraint) raise the score — otherwise the scorer pushes
  toward bland minimalism, the opposite of the goal.
- Use the WCAG **large-text 3:1** threshold for big text (4.5:1 stays for body).
- The geometric score is necessary but not sufficient; pair it with a **visual-polish
  pass on the component layout handlers** (the actual source of "ugly").
