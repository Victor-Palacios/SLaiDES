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
| **balance** — area-weighted centroid vs. slide centre | `_balance` | #4 Ngo/Teo/Byrne | VERIFIED | Ngo's "balance / equilibrium" measures over element bounding boxes. (#9 Birkhoff is the conceptual ancestor but is SECONDHAND — not relied on.) |
| **whitespace** — coverage band + penalise one dominant empty region | `_whitespace` | #1 AeSlides | VERIFIED | AeSlides "excessive whitespace" as a verifiable defect. The specific band `0.12–0.55` is **HEURISTIC (no primary source)** — our chosen comfortable-coverage range. |
| **alignment** — reward edges snapping to few implied grid lines | `_alignment` | #3 GRIDS | VERIFIED | GRIDS treats alignment as an explicit layout objective (MILP constraint). Tolerance `~0.06"` is **HEURISTIC**. |
| **non_overlap** — `1 − Σ intersection / Σ area` | `_non_overlap` | #1 AeSlides | VERIFIED | AeSlides "element collision." Grades what the Phase-4 linter only pass/fails. |
| **contrast** — size-aware WCAG (3:1 ≥24pt, 4.5:1 below) | `_contrast`, `_LARGE_TEXT_PT`, `_TARGET_*` | WCAG 2.x + #11 Rebelo et al. | standard + VERIFIED | Thresholds are the **WCAG 2.x** web standard (not a paper) and PLAN.md Phase 4. #11 (EvoMUSART 2024) backs "legibility/contrast as a deterministic constraint." |
| **richness** — accent emphasis + structure + restrained colour variety | `_richness` | #12 Reinecke et al. (CHI 2013) | VERIFIED | Perceived colourfulness/complexity models. slidekit uses **palette colour variety** as a no-render proxy for colourfulness. The `0.45/0.35/0.20` split and the variety falloff past 3 colours are **HEURISTIC**. |
| **color_harmony** — hue-angle relationship between palette roles | `_color_harmony` | — | **HEURISTIC (no primary source)** | Classical colour-theory relationships (mono/analogous/triadic/split-comp/complementary). No specific primary paper is cited; the 30° tolerance is our choice. |
| **hierarchy** — title:body size-ratio band | `_hierarchy` | — | **HEURISTIC (no primary source)** | Motivated by multimedia-learning intuition, but **no specific primary source** backs the exact ratio thresholds. Candidate for a future verified citation. |
| **cross_slide_consistency** — deck multiplier on margin variance | `_cross_slide_consistency` | #7 PPTEval, #8 DECKBench | **SECONDHAND** | Both references are still unverified. The metric ships, but its citation is not yet primary-confirmed — verify #7/#8 before relying on this lineage. |

## Composite & weights

| Decision | Code | Ref | Status | Notes |
|---|---|---|---|---|
| Composite as a **weighted mean** of sub-scores | `score_deck` / `DEFAULT_WEIGHTS` | #9 Birkhoff (M=O/C) | SECONDHAND | Conceptual basis for a single composite score. |
| **Non-linear** combiner (one bad feature dominates) — **NOT yet implemented** | — (design note in AESTHETICS.md) | #10 Harrington et al. (DocEng 2004) | VERIFIED | Harrington combines geometric measures non-linearly. Documented as the intended improvement; the current composite is still a weighted mean. **OPEN.** |
| Weights `non_overlap/contrast/richness = 1.5`, others 1.0 | `DEFAULT_WEIGHTS` | — | **HEURISTIC (no primary source)** | Our judgment that unreadable/overlapping/bare slides are "ugly" in ways balance can't offset. Weight **calibration is DEFERRED** — would require a labelled slide-pair dataset (cf. #2 EvoPresent's 2,000 pairs). No human-correlation claim is made. |
| `deck = mean(slide scores) · consistency`, consistency bounded `[0.9, 1.0]` | `score_deck` | #7/#8 | SECONDHAND | Gentle deck-level modulation; bound is **HEURISTIC**. |

## Scoreboard

- Sub-scores backed by a **VERIFIED** primary paper: balance (#4), whitespace (#1),
  alignment (#3), non_overlap (#1), richness (#12) — plus contrast (WCAG standard + #11).
- Sub-scores that are **HEURISTIC with no primary source**: color_harmony, hierarchy
  (and several internal constants noted above).
- Sub-scores resting on a **SECONDHAND** (unverified) reference: cross_slide_consistency
  (#7/#8), and the composite's conceptual basis (#9 Birkhoff).
- **OPEN research-to-product gaps:** (1) implement Harrington's non-linear combiner
  (#10, VERIFIED but not yet coded); (2) find primary sources for color_harmony and
  hierarchy; (3) verify #5/#7/#8/#9; (4) weight calibration (DEFERRED, needs data).

_Maintained alongside `REFERENCES.md` and `AESTHETICS.md` by the nightly routine. When a
new metric or threshold is added, add its row here with the ref number and status, and a
matching `# ref #N` comment in `score.py`._
