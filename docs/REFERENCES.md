# References — mathematical & computational slide aesthetics

A living bibliography of research on **defining, measuring, or optimizing slide /
layout / presentation aesthetics mathematically**. Grown by the nightly routine
(see NIGHTLY_PROMPT.md → "STANDING RESEARCH TASK"): each session finds 1–3 new
works, verifies them against a primary source, records how each informs slidekit,
and integrates concrete deterministic metrics into Phase 10 (`docs/AESTHETICS.md`).

**Goal: ~20 distinct VERIFIED references.**  **Current: 15 (15 verified, 0 secondhand).**

Status key — **VERIFIED**: confirmed from a primary source (arXiv / venue / DOI /
official code). **SECONDHAND**: carried from an operator-pasted synthesis, not yet
independently confirmed; verify and upgrade before relying on it.

| # | Reference | Year | Status | How it informs slidekit |
|---|---|---|---|---|
| 1 | **AeSlides: Incentivizing Aesthetic Layout in LLM-Based Slide Generation via Verifiable Rewards** — arXiv:2604.22840; code github.com/ympan0508/aeslides | 2026 | **VERIFIED** | Verifiable metrics: aspect ratio, excessive whitespace, element collision, visual imbalance. Directly maps to slidekit's whitespace/non-overlap/balance scores. NB: AeSlides computes these over Playwright-**rendered** pixels with proprietary formulas; slidekit computes equivalents over native geometry, no render. |
| 2 | **EvoPresent / PresAesth: Presenting a Paper is an Art — Self-Improvement Aesthetic Agents for Academic Presentations** — arXiv:2510.05571 (ICLR 2026) | 2025 | **VERIFIED** | Multi-task RL aesthetic model (scoring, defect adjustment, pairwise compare); benchmark of 650 papers + 2,000 slide pairs. Informs the (deferred) human-calibration approach for slidekit's weights. |
| 3 | **GRIDS: Interactive Layout Design with Integer Programming** — Dayama, Todi, Saarelainen & Oulasvirta; CHI 2020; DOI 10.1145/3313831.3376553; arXiv:2001.02921 | 2020 | **VERIFIED** | MILP layout model with explicit objectives for packing, **alignment**, grouping, and preferential positioning → informs slidekit's alignment & balance metrics as scorable geometric constraints. (Verified 2026-06-14 from ACM DL + arXiv.) |
| 4 | **Ngo, Teo & Byrne — Modelling interface aesthetics** — Information Sciences 152:25–46; DOI 10.1016/S0020-0255(02)00404-8 | 2003 | **VERIFIED** | **14** measures (balance, equilibrium, symmetry, sequence, cohesion, unity, proportion, simplicity, density, regularity, economy, homogeneity, rhythm, order-and-complexity), each a closed-form function of element bounding boxes → primary source for slidekit's balance/density/regularity/proportion definitions, all computable from ResolvedDeck geometry. (Verified 2026-06-14 from ScienceDirect/DOI.) |
| 5 | **SlidesGen-Bench: Evaluating Slides Generation via Computational and Quantitative Metrics** — Yang, Li, Ren, Lu, Wang, Huang, Zong, Zhan & Li; arXiv:2601.09487 | 2026 | **VERIFIED** | Scores slides on three reproducible axes — **Content, Aesthetics, Editability** — with a human-preference dataset (Slides-Align1.5k, 9 systems × 7 scenarios) → establishes aesthetics as a quantitative, reproducible, human-aligned axis, motivating `slidekit score`. NB: the benchmark is a **unified visual framework that treats outputs as renderings** (method-agnostic but vision-based); slidekit deliberately computes geometry-only analogues with no render. (Verified 2026-06-17 from arXiv abstract.) |
| 6 | **Seeing Like a Designer Without One: Unsupervised Slide Quality Assessment via Designer Cue Augmentation** — arXiv:2508.19289 | 2025 | **VERIFIED** | 7 expert-inspired visual-design metrics (whitespace, colorfulness, edge density, brightness contrast, text density, color harmony, layout balance) + CLIP-ViT; correlation **up to 0.83** with human slide-quality ratings (paper's headline stat is **Spearman ρ = −0.83**, 1.79–3.23× stronger than VLMs; not Pearson as the synthesis stated). Trained on 12k lecture slides, eval on 6 talks/115 slides. NB: edge-density/brightness-contrast/colorfulness need **rendered pixels**; slidekit computes the geometry-only analogues (whitespace, layout balance, text density, colour harmony) with NO render and explicitly omits the pixel-only ones. (Verified 2026-06-15 from arXiv.) |
| 7 | **PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides** (introduces the **PPTEval** framework) — Zheng, Guan, Kong, Zheng, Zhou, Lin, Lu, He, Han & Sun; arXiv:2501.03936; code github.com/icip-cas/PPTAgent | 2025 | **VERIFIED** | PPTEval scores presentations on three dimensions — **Content, Design, Coherence** — establishing design + cross-slide coherence as explicit, separable axes → motivates slidekit's design-vs-coherence split and the deck-level cross-slide consistency metric. (Verified 2026-06-16 from arXiv abstract + authors. NB: the specific Design sub-metrics "color/contrast/harmony/no-overlap" and the "Pearson ≈ 0.90" figure in the prior synthesis are NOT in the abstract and remain unconfirmed; do not cite those numbers until checked against the full paper.) |
| 8 | **DECKBench: Benchmarking Multi-Agent Frameworks for Academic Slide Generation and Editing** — Jang, Heisler, Xing, Li, Wang, Xiong, Zhang & Fan; arXiv:2602.13318 | 2026 | **VERIFIED** | Evaluation protocol that systematically assesses **slide-level AND deck-level fidelity, coherence, layout quality**, and multi-turn instruction following → primary motivation for slidekit treating coherence/layout at both the slide and the deck level, backing the deck-level **cross-slide consistency** metric. (Verified 2026-06-17 from arXiv abstract.) |
| 9 | **G. D. Birkhoff — Aesthetic Measure** — Harvard University Press; DOI 10.4159/harvard.9780674734470 | 1933 | **VERIFIED** | Defines aesthetic measure as **M = f(O/C)** (order over complexity), with O and C as object-specific closed-form quantities → the historical basis for slidekit treating beauty as a computed ratio of structure (order: alignment, balance, regularity) to clutter (complexity: element/colour count, density), and for a non-linear composite. (Verified 2026-06-16 from Harvard UP / DeGruyter DOI + AMS Bulletin 1934 review.) |
| 10 | **Harrington, Naveda, Price Jones, Roetling & Thakkar — Aesthetic measures for automated document layout** — Proc. ACM DocEng '04; DOI 10.1145/1030397.1030419 | 2004 | **VERIFIED** | Closed-form heuristic measures for **alignment, regularity, separation, balance, white-space fraction, white-space free-flow, proportion, uniformity, page security**, combined **non-linearly** so one bad feature dominates the score. Directly maps to slidekit's alignment/whitespace/balance metrics and argues for a non-linear (not simple weighted-mean) composite. All computable from native geometry — no render. (Verified 2026-06-14 from ACM DL.) |
| 11 | **Rebelo, Merelo, Bicker & Machado — Evaluation Metrics for Automated Typographic Poster Generation** — EvoMUSART 2024 (Springer LNCS); arXiv:2402.06945 | 2024 | **VERIFIED** | Heuristic metrics in three families — **legibility** (text visibility), **aesthetics** (visual quality), **semantics** — used as computational constraints inside an evolutionary design loop. The legibility family is a primary source for slidekit's text-visibility/contrast scoring as a deterministic constraint; the aesthetics heuristics inform the richness/whitespace scores. (Verified 2026-06-15 from arXiv.) |
| 12 | **Reinecke, Yeh, Miratrix, Mardiko, Zhao, Liu & Gajos — Predicting Users' First Impressions of Website Aesthetics with a Quantification of Perceived Visual Complexity and Colorfulness** — Proc. SIGCHI (CHI) 2013; DOI 10.1145/2470654.2481281 | 2013 | **VERIFIED** | Computational models of perceived **visual complexity** and **colorfulness** from image statistics, validated against 548 users × 450 sites; explains ~half the variance in 500ms appeal judgments. Primary source for slidekit's **richness/colour-variety** sub-score and a (deferred) info-density metric. NB: their formulas use rendered-pixel statistics; slidekit approximates colourfulness via theme-palette colour variety (no render). (Verified 2026-06-15 from ACM DOI + Harvard DASH.) |
| 13 | **Kikuchi, Simo-Serra, Otani & Yamaguchi — Constrained Graphic Layout Generation via Latent Optimization** — Proc. ACM MM '21, pp. 88–96; DOI 10.1145/3474085.3475497; arXiv:2108.00871; code github.com/ktrk115/const_layout | 2021 | **VERIFIED** | Defines the now-standard **Alignment** and **Overlap** layout metrics as closed-form functions of element bounding boxes (overlap = pairwise intersection area; alignment = minimal edge/centre misalignment), normalised by element count — exactly slidekit's no-render regime. Primary source backing slidekit's `alignment` and `non-overlap` metric definitions (and the linter's `E_OVERLAP`). (Verified 2026-06-16 from arXiv + ACM DL + official code.) |
| 14 | **O'Donovan, Agarwala & Hertzmann — Learning Layouts for Single-Page Graphic Designs** — IEEE TVCG 20(8):1200–1213; DOI 10.1109/TVCG.2014.48; project dgp.toronto.edu/~donovan/layout/ | 2014 | **VERIFIED** | Energy-based layout model whose terms — **alignment, overlap, white space**, plus predicted importance and balance — are closed-form functions of element bounding boxes, with the term weights learned by Nonlinear Inverse Optimization from a few examples. Primary source for slidekit's alignment/non-overlap/whitespace metrics AND, like Harrington (#10), strong evidence that the composite should be a learned/non-linear combination rather than an ad-hoc weighted mean. All terms geometry-based — no render. (Verified 2026-06-17 from IEEE TVCG DOI + authors' project page.) |
| 15 | **Miniukovich & De Angeli — Computation of Interface Aesthetics** — Proc. ACM CHI 2015, pp. 1163–1172; DOI 10.1145/2702123.2702575 | 2015 | **VERIFIED** | Eight automatic GUI-aesthetics metrics across three dimensions: **information amount** (visual clutter, colour variability), **information organization** (symmetry, grid, ease-of-grouping, prototypicality), **information discriminability** (contour density, figure-ground contrast); explained up to 49% of webpage-aesthetics variance. The geometry/theme-computable subset — **symmetry, grid alignment, colour variability, visual clutter, white space** — backs slidekit's balance/alignment, richness/colour-variety, and density scores. NB: contour density & figure-ground contrast need rendered pixels and are deliberately omitted (no-render rule). (Verified 2026-06-17 from ACM DOI.) |

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
- 2026-06-16: verified **#7 PPTAgent/PPTEval** (arXiv:2501.03936, Zheng et al. 2025) and
  **#9 Birkhoff — Aesthetic Measure** (Harvard UP 1933, DOI 10.4159/harvard.9780674734470)
  from primary sources, SECONDHAND→VERIFIED. Flagged that PPTEval's specific Design
  sub-metrics and the "Pearson ≈ 0.90" figure are NOT in the abstract and stay unconfirmed.
  Added **#13 Kikuchi et al., Constrained Graphic Layout Generation via Latent Optimization**
  (ACM MM '21, DOI 10.1145/3474085.3475497, arXiv:2108.00871, VERIFIED) — its closed-form,
  element-count-normalised **Alignment** and **Overlap** metrics are the canonical primary
  source for slidekit's geometry-only `alignment`/`non-overlap` scores and the `E_OVERLAP`
  linter rule (no render). Running count **13/~20 (11 verified, 2 secondhand)**; remaining
  SECONDHAND to verify: #5 SlidesGen-Bench, #8 DECKBench.
- 2026-06-17: cleared the SECONDHAND backlog — verified **#5 SlidesGen-Bench** (arXiv:2601.09487,
  Yang et al. 2026) and **#8 DECKBench** (arXiv:2602.13318, Jang et al. 2026) from primary arXiv
  abstracts, SECONDHAND→VERIFIED. #5's three reproducible axes (Content/Aesthetics/Editability) and
  #8's explicit slide-level + deck-level coherence/layout assessment confirm the design-vs-coherence
  split and the deck-level cross-slide consistency metric — but both are render/vision-based, so
  slidekit keeps its geometry-only analogues. Added two verified geometry-based primary sources:
  **#14 O'Donovan, Agarwala & Hertzmann** (IEEE TVCG 2014, DOI 10.1109/TVCG.2014.48) — energy-based
  layout model (alignment/overlap/white-space terms, NIO-learned weights), reinforcing the
  non-linear-composite direction from Harrington (#10); and **#15 Miniukovich & De Angeli**
  (CHI 2015, DOI 10.1145/2702123.2702575) — eight GUI-aesthetics metrics whose geometry/theme-
  computable subset (symmetry, grid, colour variability, clutter, white space) backs slidekit's
  balance/richness/density scores. Running count **15/~20, all 15 verified, 0 secondhand**. With the
  SECONDHAND backlog cleared, future sessions add only genuinely novel high-quality works and shift
  toward integration + (deferred) calibration, per the standing task.
