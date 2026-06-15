# References — mathematical & computational slide aesthetics

A living bibliography of research on **defining, measuring, or optimizing slide /
layout / presentation aesthetics mathematically**. Grown by the nightly routine
(see NIGHTLY_PROMPT.md → "STANDING RESEARCH TASK"): each session finds 1–3 new
works, verifies them against a primary source, records how each informs slidekit,
and integrates concrete deterministic metrics into Phase 10 (`docs/AESTHETICS.md`).

**Goal: ~20 distinct VERIFIED references.**  **Current: 12 (8 verified, 4 secondhand).**

Status key — **VERIFIED**: confirmed from a primary source (arXiv / venue / DOI /
official code). **SECONDHAND**: carried from an operator-pasted synthesis, not yet
independently confirmed; verify and upgrade before relying on it.

| # | Reference | Year | Status | How it informs slidekit |
|---|---|---|---|---|
| 1 | **AeSlides: Incentivizing Aesthetic Layout in LLM-Based Slide Generation via Verifiable Rewards** — arXiv:2604.22840; code github.com/ympan0508/aeslides | 2026 | **VERIFIED** | Verifiable metrics: aspect ratio, excessive whitespace, element collision, visual imbalance. Directly maps to slidekit's whitespace/non-overlap/balance scores. NB: AeSlides computes these over Playwright-**rendered** pixels with proprietary formulas; slidekit computes equivalents over native geometry, no render. |
| 2 | **EvoPresent / PresAesth: Presenting a Paper is an Art — Self-Improvement Aesthetic Agents for Academic Presentations** — arXiv:2510.05571 (ICLR 2026) | 2025 | **VERIFIED** | Multi-task RL aesthetic model (scoring, defect adjustment, pairwise compare); benchmark of 650 papers + 2,000 slide pairs. Informs the (deferred) human-calibration approach for slidekit's weights. |
| 3 | **GRIDS: Interactive Layout Design with Integer Programming** — Dayama, Todi, Saarelainen & Oulasvirta; CHI 2020; DOI 10.1145/3313831.3376553; arXiv:2001.02921 | 2020 | **VERIFIED** | MILP layout model with explicit objectives for packing, **alignment**, grouping, and preferential positioning → informs slidekit's alignment & balance metrics as scorable geometric constraints. (Verified 2026-06-14 from ACM DL + arXiv.) |
| 4 | **Ngo, Teo & Byrne — Modelling interface aesthetics** — Information Sciences 152:25–46; DOI 10.1016/S0020-0255(02)00404-8 | 2003 | **VERIFIED** | **14** measures (balance, equilibrium, symmetry, sequence, cohesion, unity, proportion, simplicity, density, regularity, economy, homogeneity, rhythm, order-and-complexity), each a closed-form function of element bounding boxes → primary source for slidekit's balance/density/regularity/proportion definitions, all computable from ResolvedDeck geometry. (Verified 2026-06-14 from ScienceDirect/DOI.) |
| 5 | **SlidesGen-Bench** (slide-generation benchmark: content / aesthetics / editability) | — | SECONDHAND | Establishes "aesthetics" as a quantitative, reproducible, human-aligned axis → motivates `slidekit score`. |
| 6 | **Seeing Like a Designer Without One: Unsupervised Slide Quality Assessment via Designer Cue Augmentation** — arXiv:2508.19289 | 2025 | **VERIFIED** | 7 expert-inspired visual-design metrics (whitespace, colorfulness, edge density, brightness contrast, text density, color harmony, layout balance) + CLIP-ViT; correlation **up to 0.83** with human slide-quality ratings (paper's headline stat is **Spearman ρ = −0.83**, 1.79–3.23× stronger than VLMs; not Pearson as the synthesis stated). Trained on 12k lecture slides, eval on 6 talks/115 slides. NB: edge-density/brightness-contrast/colorfulness need **rendered pixels**; slidekit computes the geometry-only analogues (whitespace, layout balance, text density, colour harmony) with NO render and explicitly omits the pixel-only ones. (Verified 2026-06-15 from arXiv.) |
| 7 | **PPTAgent / PPTEval** (presentation eval: content / design / coherence) | — | SECONDHAND | Design dimension (color, contrast, harmony, no overlap) + coherence; reported Pearson up to 0.90 → informs slidekit's cross-slide consistency metric. |
| 8 | **DECKBench** (deck-level slide-generation benchmark) | — | SECONDHAND | Argues for slide-level AND deck-level fidelity/coherence/layout → motivates deck-level cross-slide consistency scoring. |
| 9 | **G. D. Birkhoff — Aesthetic Measure** (M = O/C) | 1933 | SECONDHAND | Historical formalization of aesthetics as order/complexity → conceptual basis for a composite, weighted aesthetic score. |
| 10 | **Harrington, Naveda, Price Jones, Roetling & Thakkar — Aesthetic measures for automated document layout** — Proc. ACM DocEng '04; DOI 10.1145/1030397.1030419 | 2004 | **VERIFIED** | Closed-form heuristic measures for **alignment, regularity, separation, balance, white-space fraction, white-space free-flow, proportion, uniformity, page security**, combined **non-linearly** so one bad feature dominates the score. Directly maps to slidekit's alignment/whitespace/balance metrics and argues for a non-linear (not simple weighted-mean) composite. All computable from native geometry — no render. (Verified 2026-06-14 from ACM DL.) |
| 11 | **Rebelo, Merelo, Bicker & Machado — Evaluation Metrics for Automated Typographic Poster Generation** — EvoMUSART 2024 (Springer LNCS); arXiv:2402.06945 | 2024 | **VERIFIED** | Heuristic metrics in three families — **legibility** (text visibility), **aesthetics** (visual quality), **semantics** — used as computational constraints inside an evolutionary design loop. The legibility family is a primary source for slidekit's text-visibility/contrast scoring as a deterministic constraint; the aesthetics heuristics inform the richness/whitespace scores. (Verified 2026-06-15 from arXiv.) |
| 12 | **Reinecke, Yeh, Miratrix, Mardiko, Zhao, Liu & Gajos — Predicting Users' First Impressions of Website Aesthetics with a Quantification of Perceived Visual Complexity and Colorfulness** — Proc. SIGCHI (CHI) 2013; DOI 10.1145/2470654.2481281 | 2013 | **VERIFIED** | Computational models of perceived **visual complexity** and **colorfulness** from image statistics, validated against 548 users × 450 sites; explains ~half the variance in 500ms appeal judgments. Primary source for slidekit's **richness/colour-variety** sub-score and a (deferred) info-density metric. NB: their formulas use rendered-pixel statistics; slidekit approximates colourfulness via theme-palette colour variety (no render). (Verified 2026-06-15 from ACM DOI + Harvard DASH.) |

## Integration log

- 2026-06-14: refs #1–#2 verified; informed `docs/AESTHETICS.md` metric set and the
  "no-render, open-formula" distinction. Refs #3–#9 recorded from the operator's
  synthesis as SECONDHAND, pending verification by upcoming nightly sessions.
- 2026-06-14 (session 4): verified refs #3 (GRIDS, CHI 2020) and #4 (Ngo/Teo/Byrne,
  Information Sciences 2003) from primary DOIs and upgraded SECONDHAND→VERIFIED;
  corrected Ngo's count to 14 measures. Added ref #10 (Harrington et al., DocEng
  2004, VERIFIED) — its non-linear combination of geometric measures is a concrete
  design input for Phase 10's composite score (consider a min-/penalty-weighted
  aggregate rather than a pure weighted mean). Running count 10/~20 (5 verified).
  Candidate for next session: "Evaluation Metrics for Automated Typographic Poster
  Generation" (arXiv:2402.06945) — found but not yet primary-verified; add as
  SECONDHAND after confirming its metric formulas.
- 2026-06-15: verified ref #6 ("Seeing Like a Designer Without One", arXiv:2508.19289)
  from arXiv and upgraded SECONDHAND→VERIFIED — **corrected the synthesis**: its
  headline correlation is **Spearman ρ = −0.83**, not "Pearson 0.83", and three of its
  seven metrics (edge density, brightness contrast, colorfulness) are pixel-based, so
  slidekit can only compute the geometry-only subset without rendering. Added ref #11
  (Rebelo et al., EvoMUSART 2024, arXiv:2402.06945, VERIFIED) — the prior session's
  flagged candidate, now confirmed; its legibility metrics back the contrast-as-
  constraint design. Added ref #12 (Reinecke et al., CHI 2013, DOI 10.1145/2470654.2481281,
  VERIFIED) — perceived visual-complexity/colourfulness models; backs the new Phase 10
  `richness`/colour-variety sub-score (slidekit uses palette colour variety as a no-
  render proxy for colourfulness). Running count **12/~20 (8 verified, 4 secondhand)**.
  Remaining SECONDHAND to verify: #5 SlidesGen-Bench, #7 PPTAgent/PPTEval, #8 DECKBench,
  #9 Birkhoff.
