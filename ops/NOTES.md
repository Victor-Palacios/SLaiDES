# NOTES — objections and out-of-scope proposals

Per PLAN.md work rule 6: features not in PLAN.md are recorded here as
proposals, not code. Objections to the plan are recorded here and the plan
is followed anyway.

## Deviations recorded at setup (2026-06-13)

- **Scheduling mechanism.** PLAN.md prefers Claude Code's built-in scheduled
  tasks (`/schedule` Routines) and falls back to a crontab entry. This project
  is hosted in Claude Code on the web, where each session runs in an ephemeral
  container: a crontab written here would vanish when the container is
  reclaimed, and Routines cannot be registered from inside a session. The
  durable equivalent chosen instead is a scheduled GitHub Actions workflow
  (`.github/workflows/nightly.yml`) running Claude Code headless with the
  verbatim NIGHTLY_PROMPT.md, scoped to `--allowedTools "Read,Edit,Write,Bash"`
  as the plan specifies. Requires the `CLAUDE_CODE_OAUTH_TOKEN` repo secret
  (subscription auth, per operator decision 2026-06-13; `ANTHROPIC_API_KEY`
  is the API-billing alternative) — see README. The operator may alternatively
  register a Routine from the Claude Code UI pointing at this repo with the
  same prompt; if so, disable the workflow to avoid double runs.

## Deviations recorded during Phase 6 (2026-06-13, session 2)

- **CI workflow originally shipped under `ci/`, now installed.** The Phase 6
  verification harness needs its own GitHub Actions workflow. The unattended
  nightly bot authenticates as a GitHub App whose token lacks the `workflows`
  permission, so `git push` is rejected when the diff creates or edits any file
  under `.github/workflows/`. The bot therefore parked it at `ci/verify.yml`.
  RESOLVED 2026-06-13 (session 2 follow-up): installed to
  `.github/workflows/verify.yml` from an operator-scoped session that carries the
  `workflows` permission; the `ci/` parking directory was removed.

- **Icon emitter changed from text label to colored circle.** The Phase 5 icon
  emitter rendered an unmeasured `[name]` text label, centered with word-wrap off,
  into the icon slot. The Phase 6 harness caught this as ~1.7% stray ink on
  icon-bearing decks: in LibreOffice the label overflowed its slot symmetrically.
  Per PLAN.md's rule that harness/linter disagreements are fixed in emit/layout
  (never a per-deck visual loop), the emitter now draws a colored circle inscribed
  in the slot — which is what the Phase 2 spec specified for icons all along
  ("rendered into a colored circle"). Round-trip tests are unaffected (they inspect
  text-box shapes only); all example decks now pass the harness.

## Phase 8 approach (2026-06-13, operator-directed)

- **agency-agents vendored into this repo on a dedicated branch.** Per operator
  decision, Phase 8 is done entirely inside slaides rather than against the external
  `msitarzewski/agency-agents` repo (which this session can't write to). The repo is
  copied to `integrations/agency-agents/` (MIT, point-in-time snapshot; upstream SHA
  in `.VENDORED_FROM`) on branch `agency-agents-integration`, kept off the slidekit
  dev branch so the foreign tree doesn't tangle with slidekit's source. Nothing is
  pushed upstream; contributing the Deck Builder agent back to msitarzewski is a
  separate, optional fork-and-PR step.

- **NIGHTLY_PROMPT.md is no longer strictly verbatim.** PLAN.md's setup said to keep
  it verbatim, but the operator directed changing the instructions so an unattended
  Opus session can finish Phase 8. A clearly-marked "PHASE 8 ADDENDUM" was appended
  (the original prompt body is unchanged above it). It tells the routine that Phase 8
  lives on `agency-agents-integration`, where the vendored repo and Deck Builder agent
  are, how to validate agent files (`lint-agents.sh`), and the remaining items.

- **Phase 8 runs on `agency-agents-integration`, not `claude/busy-rubin-mzpvfu`.** To
  have Opus finish Phase 8, dispatch the nightly workflow against this branch (same
  mechanism used for runs 6-8). The scheduled cron only picks up Phase 8 automatically
  if this branch is made the default branch; otherwise drive it by dispatch.

## Proposals

(none yet)

## Phase 9 scope expansion + research-access blocker (2026-06-14, operator-directed)

- **Scope expansion beyond original PLAN.md.** The operator directed growing the
  component library from 8 to **40 core slide designs**. This is past the v1 plan's
  scope, so per work rule 6 it is recorded here; it is operator-authorized, not an
  unsanctioned addition. Blueprint: `docs/SLIDE_DESIGNS.md`; tracked as Phase 9 in
  PROGRESS.md; build instructions appended to NIGHTLY_PROMPT.md.

- **Research sources unreachable.** The operator provided a ChatGPT share and a Grok
  share to inform the 40-design catalog. The execution environment's network egress
  allowlist blocks `chatgpt.com` and `grok.com` ("Host not in allowlist"), so neither
  WebFetch nor curl can read them. The catalog was therefore built from established
  presentation-design practice. To integrate the research, add those hosts to the
  environment's egress settings (see code.claude.com/docs/en/claude-code-on-the-web)
  or paste the content; then reconcile against docs/SLIDE_DESIGNS.md.

## Phase 10: computational-aesthetics research integrated (2026-06-14, operator-provided)

- The operator pasted a research synthesis (the chatgpt.com/grok.com shares being
  egress-blocked) arguing slide aesthetics are mathematically definable/measurable.
  Integrated as Phase 10: a deterministic aesthetic scoring layer over the
  ResolvedDeck (balance, alignment, whitespace, non-overlap, contrast, color
  harmony, density, hierarchy, cross-slide consistency). Spec: `docs/AESTHETICS.md`.
- Fit rationale: slidekit already computes exact element geometry, so these metrics
  are arithmetic over existing data — no screenshots, consistent with the project
  thesis. Scoring is ADVISORY (warnings + 0–100 score); the linter remains the gate.
- Honesty guard recorded in the spec: do not claim human-judgment correlation
  without a labeled slide-pair dataset (calibration deferred).

## Nightly cron re-enabled + standing research task (2026-06-14, operator-directed)

- **Cron re-enabled.** The schedule in `.github/workflows/nightly.yml` (07:00 UTC ≈
  midnight Pacific) was re-enabled to continue the work: each run advances the current
  build phase (Phase 9 designs → Phase 10 aesthetics) AND the standing research task.
  Recurring Opus spend resumes (~$7–50/session) — operator-accepted.
  *(Update 2026-06-16: shifted 2h later to 09:00 UTC ≈ 02:00 Pacific, operator request.)*
- **Web tools added to the nightly allowlist.** `claude_args` now includes
  `WebSearch,WebFetch` (added to Read/Edit/Write/Bash) so the unattended session can
  discover and verify new research online. GitHub runners have open egress (unlike the
  Claude-Code-web environment whose allowlist blocks chatgpt.com/grok.com).
- **Standing research task.** Every session grows `docs/REFERENCES.md` toward ~20
  VERIFIED references on mathematical/aesthetic slide design and integrates concrete
  deterministic metrics into Phase 10. Verify before citing; keep all metrics
  render-free; never gate the build on a learned score.

## North-star realignment (2026-06-18, operator-directed)

An operator audit re-anchored the project on its core goal: **~40 slide layouts that render
reproducibly from recorded geometry, with an LLM (no vision) picking which layout per slide
for a given topic.** Three read-only audits found: (1) the deterministic render/geometry core
is exactly on-goal and done; (2) "40 distinct layouts" was padded — only ~25 are structurally
distinct skeletons, ~15 are styled variants; (3) the LLM-selection half of the pipeline did
not exist in-repo (only un-wired agency-agent scaffolds). Recent advisory/meta work
(aesthetic scorer, research bibliography, board, brainstorm, dated PDF archive, example index)
was disciplined but did not advance (2) or (3).

Fix (operator decisions: consolidate to an honest taxonomy; build BOTH an LLM selection
guide + `slidekit author` AND a deterministic recommender):
- `src/slidekit/catalog/registry.py` — single source of truth: 40 components → 25 distinct
  families + 15 variants, plus selection metadata; fields derived from the IR models.
- `docs/LAYOUT_TAXONOMY.md` (honest count) and `docs/LAYOUT_SELECTION_GUIDE.md` +
  `slidekit catalog --json` (LLM picks layouts, vision-free), both generated + sync-tested.
- `src/slidekit/select/recommend.py` (content-shape → component) and `slidekit author`
  (outline → recommend/validate → lint → render), with `examples/author-demo/`.
The aesthetic scorer and standing research are now BACKGROUND (kept, not deleted). See the
NIGHTLY_PROMPT "NORTH-STAR PRIORITY" section.

## Schedule changes — nightly to 10pm Pacific, brainstorm cron off (2026-06-19)

Operator request: "turn off the second job at night, and move the first job to 10pm
California time." Implemented:
- **Nightly build** (`.github/workflows/nightly.yml`): cron moved `0 9 * * *` → `0 5 * * *`.
  GitHub cron is UTC and ignores DST; 05:00 UTC = 22:00 (10pm) America/Los_Angeles during PDT,
  i.e. ~4h earlier than the previous 09:00 UTC / 02:00 PDT slot. (When PST returns in November,
  05:00 UTC = 21:00 / 9pm Pacific — acceptable; the cron stays fixed in UTC by design.)
- **PR-brainstorm** (`.github/workflows/pr-brainstorm.yml`): the nightly `schedule:` cron
  (was `30 13 * * *`) is commented out — the session is now MANUAL ONLY via `workflow_dispatch`
  (Actions tab → Run workflow). Re-enable by uncommenting the schedule block.
- README schedule wording updated to match. GitHub may take a cycle to register the new cron,
  so the 05:00 UTC slot likely first fires the following night.

## Operator layout-feedback loop (2026-06-19)

Added a phone-native channel for per-layout feedback that feeds the nightly, reusing the
established "structured file → rendered markdown → AI consumes & annotates" pattern (cf.
board.yaml/IDEAS.md): the *Layout feedback* GitHub issue form
(`.github/ISSUE_TEMPLATE/layout-feedback.yml`, dropdown generated from the catalog) →
`feedback-intake.yml` (owner-gated, untrusted-body-safe) records each comment in
`FEEDBACK.yaml` and regenerates `FEEDBACK.md` → the nightly treats `status: open` comments as
actionable (no approval step, since they're operator-authored), queues board tasks under the
`feedback` epic, and marks them `done`/`wontfix`. Chosen over a GitHub Pages console because
Pages can't serve a private repo without a paid plan; Issue Forms render natively in the GitHub
mobile app with zero hosting. See `src/slidekit/feedback/`, the new scripts, and the
NIGHTLY_PROMPT "FEEDBACK INTAKE" addendum.

## Evaluation: largest-empty-rectangle whitespace metric (2026-06-22) — NOT adopted

The 2026-06-21 report flagged evaluating a *largest-empty-rectangle* ("white-space
free-flow") refinement to `_whitespace`, primary-source verified first. Outcome:

- **Source check:** Harrington et al. (ref #10, DocEng 2004) lists "white-space
  free-flow" among its measures and O'Donovan et al. (ref #14) has a "white space"
  energy term, but neither publishes a closed-form free-flow formula (confirmed
  against the ACM abstract and the authors' patent US20070208996A1 — the exact
  free-flow computation is not disclosed). So any implementation would be HEURISTIC,
  not a faithful reproduction of a verified formula.
- **Redundancy:** the aesthetic concern the docs ascribed to it ("penalise one
  dominant empty region") is the *uneven whitespace* case — content clustered to one
  side leaving a large void on the opposite side. That is exactly what `_balance`
  already scores (area-weighted moment about the centre axes, refs #4/#16/#17/#18).
  A centred sparse hero slide (big-number) has lots of *evenly distributed*
  whitespace and is correctly NOT penalised by balance — which a naive
  largest-empty-rectangle penalty would wrongly punish. Adding it would duplicate
  balance and risk the well-tuned baselines + the designed-beats-plain invariant.
- **Honesty fix applied:** `docs/AESTHETICS.md` and `docs/RESEARCH_TRACE.md` claimed
  `_whitespace` already penalised distribution ("warns when largest empty > 3×
  median"). The code only ever scored a coverage band. Corrected both docs to match
  the code and to cross-reference balance for distribution. No code changed.

Decision: do NOT add a largest-empty-rectangle metric. Revisit only if a
non-redundant, primary-source-formula formulation emerges (e.g. fragmentation of
*trapped* interior whitespace distinct from off-centre imbalance).

## 2026-06-23 — Ngo (#4) regularity / rhythm assessment (research, T-048)

Carried over from the 2026-06-22 next-step: assess whether Ngo/Teo/Byrne's
*regularity* and *rhythm* measures (ref #4) offer a non-redundant deterministic
addition distinct from slidekit's existing alignment/balance metrics.

- **Alignment-regularity** `1 − (n_vap + n_hap)/(2n)` — the one Ngo term cleanly
  reproducible from secondary sources (confirmed verbatim across several). It counts
  vertical alignment points (`n_vap`: distinct x-columns of left/centre/right edges)
  AND horizontal alignment points (`n_hap`: distinct y-rows of top/centre/bottom).
  slidekit's `_alignment` clusters **left edges (x) only** — a deliberate subset.
  Adopting the full symmetric x+y form **regresses the dominant slide pattern**: a
  clean single left-aligned text column gets `n_vap=1, n_hap=n`, so a tidy 5-bullet
  column scores `1−(1+5)/10 = 0.40` vs the left-edge metric's `1−1/5 = 0.80`. That
  halving would threaten the designed-beats-plain invariant for no real gain (a clean
  left column IS well aligned for a slide). **Not adopted.**
- **Spacing-regularity** and **rhythm (RHM)** — closed-form definitions are **not
  available from any extractable primary/faithful source**: Information Sciences is
  paywalled; the arXiv reproductions (e.g. 1101.1606) are FlateDecode-compressed and
  the readable secondaries reproduce only the alignment term. Implementing them would
  be heuristic-with-a-citation — declined, same discipline as the 2026-06-22
  largest-empty-rect rejection. The spacing-consistency concern is also partly served
  by `_balance` (off-centre voids).
- **Doc-honesty fix (applied):** AESTHETICS.md's Alignment row claimed the metric
  clusters "left/right/cx, top/bottom/cy"; the code (`_alignment`) only ever clustered
  the left edge x. Corrected AESTHETICS.md + RESEARCH_TRACE.md to match the code, and
  added an alignment design note recording this assessment. **No code changed.**

Decision: do NOT add Ngo regularity/rhythm metrics. Current left-edge alignment is the
better-suited choice for slides. Revisit only if (a) a faithful spacing-regularity
closed-form becomes obtainable from a primary source, and (b) it proves non-redundant
with `_alignment`/`_balance`.

## 2026-06-24 — Ngo (#4) proportion / economy assessment (research, T-049)

Carried-forward 2026-06-23 next-step: do Ngo/Teo/Byrne's **proportion** or **economy**
measures (ref #4) admit a faithful, non-redundant deterministic form that improves the
slide scorer? Primary source re-checked first.

Source-faithfulness check (same discipline as the regularity/rhythm pass):
- Information Sciences original remains paywalled; arXiv reproduction 1101.1606 still
  FlateDecode-compressed. NEW this session: checked the **Aalto Interface Metrics (AIM)**
  open codebase (github.com/aalto-ui/aim) — its open metrics are **image/pixel-based**
  (PNG file size, contour density/congestion, figure-ground contrast, saliency,
  quadtree, grid quality), NOT Ngo's geometric bounding-box closed forms; AIM is **not**
  a faithful source for the proportion/economy scoring functions.
- What IS confirmed from a faithful reproduction (Deng & Wang, PMC7085848, which
  explicitly reproduces Ngo's proportion ratios): the "good proportion" set is
  **{1:1, 1:√2 (1.414), 1:1.618 (golden), 1:√3 (1.732), 1:2}**. Economy's standard
  textbook form is **ECM = 1/(number of distinct object sizes)**.

**Proportion — NOT adopted.** Two independent reasons: (a) the *good-ratio set* is solid
but the exact aggregation/normalization constant is NOT cleanly extractable from any open
primary/faithful source → adopting it would be heuristic-with-a-citation on the scoring
function (same bar that rejected spacing-regularity/rhythm and largest-empty-rect). (b)
Even granted a formula, object/layout aspect-ratio-to-golden-ratio is a poor fit for
slides: content boxes (text stacks, callouts) take their aspect ratio from content length
and the flex solver, not from a golden-ratio intent, and the canvas is a fixed 16:9
(1.778, not in the good set, not author-controlled). Scoring boxes against golden ratio
injects content-dependent noise uncorrelated with the deterministic fit+restraint thesis
and pulls against the flex solver. Redundant-with-noise.

**Economy — NOT adopted.** It is faithfully computable (count distinct sizes), but it
*conflicts* with slidekit's deliberate design choices: the type scale rewards **hierarchy**
(title 54–66 / header 40–44 / body 32–36 / caption 24–26 — multiple intentional sizes),
whereas economy *penalizes* multiple sizes. A well-structured slide with clear title/body/
caption hierarchy (3+ sizes) would score LOW on economy precisely because it is well
structured — backwards for slides. It would reward flat, sizeless decks, regressing the
designed-beats-plain invariant the richness sub-score was added to fix. The genuine
"restraint" intuition is already served by `_hierarchy` (clear scale, not sameness) and
`_cross_slide_consistency` (consistent treatment across slides). Redundant-and-conflicting.

Decision: do NOT add Ngo proportion or economy metrics. Both are declined — proportion as
unfaithful-on-the-scoring-function and ill-fitting; economy as redundant-and-conflicting
with hierarchy/richness. No metric code changed. This closes the productive line of
single-measure Ngo #4 mining: of the 14 measures, balance/density are already integrated,
and regularity, rhythm, spacing-regularity, proportion and economy have each been assessed
and declined with reasons. Future research effort should favour integration/calibration
over further per-measure mining of #4.

## 2026-06-25 — hierarchy sub-score grounding (research, T-050) — ADOPTED (direction only)

Acted on the 2026-06-24 next-step (shift from #4-mining to *integration*): `hierarchy` was
the **last sub-score in RESEARCH_TRACE tracing to NO primary source** (open gap #2). The
metric scores the theme's title:body type-scale ratio (full credit ≥1.5×, none ≤1.0×).

Found + verified a primary source for the metric's **direction**: **ref #21 — van Gog,
"The Signaling (or Cueing) Principle in Multimedia Learning"** (in Mayer & Fiorella eds.,
*The Cambridge Handbook of Multimedia Learning*, 2nd ed., CUP 2021, ch. 11; verified from
the Cambridge Core chapter page — author/editors/publisher/year confirmed). The signaling
principle: cues that **guide attention to relevant elements** and **highlight the
organization** of material — explicitly including **text headings/emphasis** — improve
learning. A visually distinct (larger) title is exactly such a structural cue, so rewarding
a clear title→body step is grounded, not arbitrary. This is *direction-only* grounding,
parallel to #20 (Alley & Neeley → info_density direction) and #19 (Cohen-Or → color_harmony
templates).

**The exact 1.5× threshold stays HEURISTIC.** No empirical primary source measures the
precise title:body ratio for slide comprehension. 1.5 is the modular-scale "perfect fifth"
step — a *typographic convention* (Bringhurst, *The Elements of Typographic Style*, Hartley
& Marks 2004), not a measured value. I did NOT add Bringhurst as a verified reference: the
book's bibliographic details are confirmed, but its modular-scale/perfect-fifth passage was
only attested via secondary typography sources this session (not read in the primary text),
so it falls short of the project's primary-source bar. It is recorded as the **lead candidate
to verify** if/when the threshold is ever calibrated.

Decision: ADOPT #21 as the direction citation; **no metric behaviour change** (1.5× threshold
unchanged — grounding, not recalibration; big-number score held at 89.5). Updated
REFERENCES.md (#21, count 21/21), RESEARCH_TRACE.md (hierarchy row → "VERIFIED direction /
HEURISTIC band"; scoreboard now shows *no* sub-score with zero primary source; gap #2
narrowed to the threshold only), AESTHETICS.md (lineage + hierarchy design note), and the
`_hierarchy` code comment. Full suite green (325 passed / 47 skipped).

---

## 2026-06-26 — color_harmony 30° tolerance: Cohen-Or sector widths verified from the primary source

Continuing the integration focus (verify the remaining HEURISTIC constants), I pursued the
`color_harmony` 30° tolerance against its source, **ref #19 Cohen-Or et al., "Color
Harmonization" (SIGGRAPH 2006)**. Previously the RESEARCH_TRACE row cited the harmonic
templates as "fixed angular relationships" but carried **no published numbers**, and the 30°
tolerance was flagged HEURISTIC with no characterization of how far it sat from the paper.

**Verified from the primary source.** Extracted the paper's Appendix from the official PDF
(igl.ethz.ch/projects/color-harmonization/harmonization.pdf): the precise template sector
sizes are — small sectors (types i, L, I, Y) = 5% of the disk = **18°**; large sectors
(V, Y, X) = 26% = **93.6°**; the large sector of L = 22% = **79.2°**; type T = 50% = **180°**;
the centre-to-centre separation of the two sectors is **180°** (I, X, Y) and **90°** (L).

**Assessment vs slidekit's metric.** `_color_harmony` rewards a hue-difference near one of
{0, 30, 120, 150, 180}° with a linear falloff over a 30° window. Mapping onto Cohen-Or:
- The 30° falloff lies **within** the paper's 18°–93.6° sector range (between the small i-type
  and the large V-type), and the 180° complementary reward matches the I/X/Y centre
  separation — so 30° is **consistent with** Cohen-Or's published geometry.
- BUT **30° is not a value the paper states** (the published widths are 18 / 79.2 / 93.6 /
  180°), and slidekit's 120° (triadic) / 150° (split-comp) reward angles trace to the broader
  artist colour-wheel tradition (Itten, cited only as *background* in Cohen-Or), not to
  Cohen-Or's own template centre-separations (which are 90° and 180°).

Decision: **the 30° tolerance stays HEURISTIC** — but the trace moves from "templates exist at
fixed angular relationships (no numbers)" to "exact sector widths VERIFIED; 30° shown
consistent-with, not stated-by, the paper." **No metric behaviour change** (grounding, not
recalibration; big-number held at 89.5). I did NOT tighten the metric toward Cohen-Or's 18°
small-sector: that would change scores and is exactly the kind of recalibration that belongs
with the DEFERRED weight calibration (needs a labelled dataset), not an unprompted edit.
Updated REFERENCES.md (#19 annotation + integration log), RESEARCH_TRACE.md (color_harmony row
+ scoreboard), AESTHETICS.md (lineage note), and the `_color_harmony` code comment.

---

## 2026-06-27 — hierarchy 1.5× "perfect fifth" grounded (ref #22)

Continued the integration focus on the last unbounded HEURISTIC constants (build complete,
both startup intakes empty, sync clean). Closed the "lead candidate" the 2026-06-25 entry
named: the hierarchy 1.5× modular-scale step, previously attested only via secondary typography
sources (Bringhurst's *Elements of Typographic Style* not read in the primary text).

Verified a primary, freely-readable source instead — **Tim Brown, "More Meaningful Typography",
A List Apart, 2011** (fetched the article directly): it defines a modular scale by quoting
Bringhurst verbatim ("a prearranged set of harmonious proportions", crediting the "Shaping the
Page" section) and builds one by multiplying/dividing a base size by a chosen **harmonious
ratio**, the menu including the **perfect fifth (3:2 = 1.5)** and golden ratio (1.618). Added it
as **REFERENCES.md #22 (VERIFIED)**.

Assessment: slidekit's 1.5× full-credit threshold is the **perfect-fifth (3:2) member of an
established harmonious-ratio family** — the just perfect fifth is the 3:2 frequency ratio = 1.5
by definition — so it is **not arbitrary**. It **stays HEURISTIC** only because the source
prescribes a *menu* of ratios (1.25 major third, 1.414 √2, 1.5 perfect fifth, 1.618 golden…),
not a single title:body value; slidekit's *selection* of 1.5 is "consistent-with, not stated-by"
the source — directly parallel to the 2026-06-26 color_harmony (#19) grounding.

**No metric behaviour change** (grounding, not recalibration; big-number held at 89.5). Did NOT
re-pick the ratio or alter the band — that is recalibration and belongs with the DEFERRED weight
calibration (needs a labelled dataset), not an unprompted edit. Updated REFERENCES.md (#22 +
header count 22 + integration log), RESEARCH_TRACE.md (hierarchy row + scoreboard + open gap #2),
AESTHETICS.md (lineage note), the `_hierarchy` code comment, and the board (T-052, research, done).

---

## 2026-06-28 — info_density direction grounded with a controlled experiment (#23); bands stay HEURISTIC

Standing-research integration session (build complete; both startup intakes empty; all
generated artifacts re-rendered with zero drift). The 2026-06-27 next-step was to assess the
`info_density` words-per-slide / coverage bands against a primary source.

A web search of the cognitive-load slide literature established that the consistent guidance is
a **minimization principle** — "as few words as possible," fewer words → better comprehension —
**not** a single empirical words-per-slide maximum. So slidekit's 45-word full-credit / 130-word
zero-credit band (and the 0.45/0.85 coverage band) **stay HEURISTIC** — same honest outcome as
the #19 color_harmony 30° and #22 hierarchy 1.5× groundings: the *direction* is sourced, the
exact number is our design choice.

Added **REFERENCES.md #23 — Wecker, "Slide presentations as speech suppressors" (Computers &
Education 59(2):260–273, 2012; DOI 10.1016/j.compedu.2012.01.013)**, verified from the ERIC
record EJ966972 + DOI metadata. It is a **controlled experiment** (n=209; no-slides / regular /
concise conditions) finding a "speech suppression effect": text-dense slides reduce retention of
*orally-presented* information, via **attention misallocation** (not cognitive overload), an
effect avoided by concise slides. This backs info_density's direction more strongly than #20 (an
experiment vs design criteria) and adds a distinct mechanism. Genuinely-novel, high-quality
post-target addition that closes the info_density direction-grounding gap.

**No metric behaviour change** (grounding, not recalibration; big-number held at 89.5). Did NOT
move the bands — recalibration belongs with the DEFERRED weight calibration (needs a labelled
dataset). Updated REFERENCES.md (#23 + header count 23 + integration log), RESEARCH_TRACE.md
(info_density row + scoreboard), AESTHETICS.md (lineage note), the `_info_density` code comment,
and the board (T-053, research, done).

## Nightly schedule disabled to stop subscription-credit drain (2026-06-28)

Operator hit "no Claude credits this morning." Cause: `.github/workflows/nightly.yml` ran
daily on Opus (timeout 180m) authenticated with `CLAUDE_CODE_OAUTH_TOKEN` — the operator's
personal Claude subscription, the same usage pool used interactively — so each overnight run
drained the rolling usage window. (Also: the cron was `0 5 * * *` intending 22:00 PT, but
GitHub's scheduler consistently fired it ~08:15 UTC ≈ 01:15 PT.) Action: commented out the
`schedule:` block (kept `workflow_dispatch`), so the build is manual-only for now. Operator
may re-enable later — preferably after switching to an `ANTHROPIC_API_KEY` secret so the
nightly bills a separate API account instead of personal subscription credits. README updated.

## Statusline "compact?" warning at 100K context (2026-06-28)

Operator wanted a prompt to appear when the Claude Code context window nears/exceeds 100K
tokens. A CLAUDE.md rule can't do this reliably (the model never sees its own live token
count). The reliable mechanism is a **statusline**: Claude Code pipes a JSON blob with the
live count (`context_window.total_input_tokens`) to a statusline command on every render.
Added `.claude/statusline.sh` (shows `model · dir · ctx Nk/200k (P%)`, turns yellow
"approaching 100K" at 80K and red "⚠ COMPACT? (/compact)" at 100K) and committed
`.claude/settings.json` pointing `statusLine.command` at it. These are intentional dev-QoL
files — do not remove. (`.claude/settings.local.json` stays gitignored.) To make the warning
global across all repos, the operator copies the script to `~/.claude/statusline.sh` and sets
the same `statusLine` block in `~/.claude/settings.json`.

## Private feedback website replaces GitHub issue forms (2026-07-02)

Operator found the GitHub-issue feedback loop unpleasant and asked for a full website only
they can access. Built a password-gated Netlify site under `web/`:

- **Auth** (decided with operator): a single `SITE_PASSWORD` gate via a Netlify **edge
  function** (`netlify/edge-functions/auth.js`) — NOT Supabase. Supabase Auth is built for
  many users (sign-up, user table, per-user RLS); for one operator it's pure overhead. The
  edge function sets a signed HttpOnly cookie = `HMAC-SHA256(password, "slaides-v1")`; no
  session store. Free, stays 100% on Netlify, no third-party auth service.
- **Write path** (decided with operator): live commit via a Netlify **function**
  (`netlify/functions/submit-feedback.js`) that re-verifies the cookie (defence in depth)
  and commits each submission as JSON under `web/feedback-inbox/` using a fine-grained PAT
  (`GITHUB_TOKEN`, contents:write, this repo only).
- **No JS schema duplication**: the function writes raw submissions; a CI workflow
  (`.github/workflows/web-feedback-intake.yml`) runs `scripts/feedback_intake_web.py` to
  fold them into `FEEDBACK.yaml` via the tested `slidekit.feedback.store` (+ regenerate
  `FEEDBACK.md`), then deletes processed inbox files. Bare 👍 (no comment) is counted but
  not turned into an open task; 👎/note/any comment → `open` item.
- **Previews are geometry, not screenshots**: `scripts/build_web_previews.py` renders each
  of the 40 components' specimen through `load`→`resolve` and reuses `emit.html_preview`'s
  node renderer to emit `web/data/previews.json` (backgrounds included, so the dark `code`
  layout renders right). A `test_web` sync test keeps it locked to the catalog.

The GitHub issue-form path (`feedback-intake.yml` + `layout-feedback.yml`) is kept as a
fallback; both funnel into the same `FEEDBACK.yaml`. Deploy steps + token scope in
`web/README.md`. Not testable end-to-end here (no Netlify runtime); Python + JSON pieces are
unit-tested, JS is syntax-checked and reviewed.

## Root restructure (ops/), burst nightly, vision authorization (2026-07-02)

Operator session, three linked requests:

1. **Repo cleanup — "massive overhaul of the overall structure".** Root had 16 loose
   meta files. All agent-ops state moved into `ops/` (PLAN, NIGHTLY_PROMPT,
   BRAINSTORM_PROMPT, PROGRESS, NOTES, IDEAS, board.yaml/BOARD.md, FEEDBACK.yaml/.md,
   calibration_report.json) and `NIGHTLY_REPORTS/` → `ops/reports/`. Root now holds only
   README.md, SKILL.md, netlify.toml, pyproject.toml + the code dirs. Path constants
   updated in scripts/render_board.py, src/slidekit/feedback/store.py,
   src/slidekit/metrics/calibrate.py, both prompts, four workflows, and the two tests
   that read committed artifacts. PLAN.md content untouched (immutable) — the prompt's
   REPO RESTRUCTURE addendum carries the old→new path mapping. Suite green throughout.
   Deletion candidates were compiled for the operator but NOT acted on (their call).

2. **Burst nightly.** Schedule re-enabled as `0 */2 * * *` UNTIL 2026-07-02 15:00 UTC
   (8 AM Pacific — operator's "every two hours until tomorrow at 8 AM"); a guard step
   compares epoch time and past the deadline DISABLES the workflow via
   `gh api PUT .../actions/workflows/nightly.yml/disable` (needs `actions: write`).
   No file edit on disable — re-enable from the Actions tab. timeout-minutes 180 → 105
   so each session fits its 2-hour slot. Operator explicitly re-authorized subscription
   spend for this burst ("right now we have a lot of credits").

3. **Vision authorized — with a codification covenant.** Operator: "you are allowed to
   use vision in order to check things and improve things … just make sure that whatever
   is visualized is also codified." This SUPERSEDES Work Rule 4 ("never render for QA")
   via a dated prompt addendum: sessions may rasterise (pdftoppm on the native PDF;
   LibreOffice for pptx cross-checks — both now installed in the nightly runner) and
   LOOK at slides to find/confirm defects, but every visual finding must land as a
   deterministic check (lint rule, verify metric, constant fix, or golden) in the same
   session. The build pipeline itself stays vision-free; the linter remains the gate.
   Burst sessions' top priority: the open web-feedback items (FB-008…FB-017).
   FB-007 marked wontfix (duplicate of FB-008 from website testing).

## 2026-07-02 — web-preview descender clipping (FB-010/015/016) + swot latent defect
- ROOT CAUSE of the web-gallery descender clipping (FB-015 agenda, FB-016 quote-opener):
  the HTML preview emitter (`emit/html_preview._node_html`) gave each text node a fixed
  border-box height (a single-line row's `rect.h` == exactly one line box) but then set
  `padding:5px` top+bottom AND left `line-height` unset. The browser fell back to a
  font-dependent `normal` line-height and the 10px padding shrank the content below one
  line, so `overflow:hidden` chopped g/p/y. Fix: pin `line-height` to LINE_SPACING_SINGLE,
  zero the vertical padding (rect.h already carries the vertical space), and set
  `.node-text{overflow:visible}` (both the site CSS and the debug emitter). Codified by
  tests/test_web/test_web_previews.py::test_text_nodes_pin_line_height_and_never_clip_descenders.
- FB-010 (icon-text-rows "can't read the subtext") was a REAL geometry defect, not just a
  preview artifact: `_layout_icon_text_rows` split each row as heading-line + 0.3" gap +
  remainder, and the remainder body box came out SHORTER than one line (46.7px < 54.4px) →
  its single line clipped. Fixed by pairing heading+body on a 0.1" inner gap (matching
  feature-list) and flooring body_h at one line. Golden 03/10 regen.
- DISCOVERED (board T-064, not operator-reported): `_panel_items` (used by swot) does
  `item_h = min(slot_h, ...)`, which caps an item box below one line when a quadrant packs
  enough items (swot specimen: 43.2px < 54.4px). With overflow now visible the line spills
  into the 0.3" inter-item gap (no overlap) rather than clipping, so it is not a ship
  blocker, but the geometry is dishonest. Proper fix (adaptive item font or item cap in
  dense cells) is deferred to T-064; the web-preview geometry guard exempts `swot` with a
  pointer here until then.
- ASSESSMENT (2026-07-02 burst, kept deferred): quantified the budget. A swot quadrant's
  `items_h` is ~1.2" for the 2-item specimen, but two full leaded-line boxes
  (2×0.567") plus the mandatory 0.3" inter-item gap (E_GAP floor, and the per-item boxes
  carry distinct group_ids so the gap is enforced) need ~1.43" — the cell is genuinely too
  short to make both boxes ≥ one leaded line without triggering E_OVERFLOW/E_OVERLAP. So the
  `min(slot_h, …)` cap is not a bug to unpick in isolation; an honest fix is STRUCTURAL — a
  smaller swot item type-tier, an item cap, or taller cells (fewer stacked headings). The PDF
  render is clean at all times (vision-confirmed this session — descenders on
  "Opportunities"/"Partnerships" render fully; the emitter does not clip to the box). Keeping
  T-064 deferred as a structural task rather than shipping a risky mid-burst rework; the guard
  exemption + this note remain the codified record.
- RESOLVED (2026-07-02 session4, commit a729aeb): took the "smaller swot item type-tier"
  option from the assessment above. SWOT item text now renders at the **caption tier**
  (25pt, `is_caption=True`) instead of body (34pt), via a new `item_pt`/`is_caption` arg on
  `_panel_items` (only swot passes it; before-after / pros-cons / this-vs-that keep body).
  This is linter-legal: `E_MIN_BODY_SIZE` exempts caption-tier nodes (24-26pt), and swot
  items are genuinely dense-grid secondary content. At 25pt a leaded line is 0.417" and the
  cell gives each item a 0.45" box, so `item_h = min(slot_h, max(line_h, …))` now floors at a
  full line honestly — no clamp under one line, no content dropped, bold body headings still
  dominate the tier hierarchy. Codified by REMOVING the `swot` exemption from the web-preview
  geometry guard (tests/test_web) so the one-line-fits (c) invariant now covers swot too; the
  defect class would now be caught deterministically without vision. PDF render re-confirmed
  clean (all descenders full). Golden 36_swot + previews.json + swot PDF + combined snapshot regen.

## 2026-07-02 — FB-008/011/017 (remove tertiary muted lines): specimen-scoped fix
Three consistent operator notes asked to remove tertiary supporting text: title-slide
subtitle (FB-008), stat-callout subtext (FB-011), big-number context (FB-017) — all
optional muted lines, aligned with the repo's minimalism ethos. CONSERVATIVE CHOICE:
stripped these from the reviewed SPECIMEN decks (examples/01,04,14) so the gallery matches
the requested cleaner design, while KEEPING the optional IR fields (subtitle/subtext/context
remain available to real decks and are still demonstrated in the multi-slide showcases). This
is reversible and does not remove component capability. If the operator intended the fields
removed from the layout entirely, they can re-file; recorded here rather than assumed.

## 2026-07-02 — FB-009: two-column component RETIRED + two-column family reparented
Operator (web feedback FB-009): "delete this slide layout — redundant with comparison-columns."
INSPECTION FINDING (surfaced, not silently accepted): architecturally `two-column` was the
*general-purpose anchor* of the two-column family (free ContentSlots, arbitrary weights) and
`comparison-columns`, `image-half-bleed`, `chart-with-insight` all specialised FROM it — so the
"redundant" call actually inverts the base/specialisation relationship. BUT the operator's read
is content-accurate: the two-column specimen (02) was literally titled "Strengths vs Weaknesses",
i.e. a comparison, and reads as a duplicate of comparison-columns in the gallery. Operator
feedback needs no approval, so HONORED it.
DECISION: deleted the `two-column` component end-to-end (IR model + Union, layout handler +
dispatch, registry entry, scaffold template → bullet-list) and REPARENTED the family so
`comparison-columns` is now the anchor; `image-half-bleed`/`chart-with-insight` point `variant_of`
it. The family NAME stays "two-column" (the two-side-by-side skeleton is unchanged), so taxonomy
invariants (one anchor/family, variants→anchor) still hold.
SHOWCASE CONVERSIONS (conservative, reuse existing components, preserve text): 10_all_components
dropped its two-column demo slide (it demoed the removed component and held an icon slot);
demo-5 + agents-in-ai → bullet-list (both already contained comparison-columns, so no duplicate);
09_full_deck → comparison-columns (no comparison present; adds variety). NOTE the verify harness
caught that long comparison-columns items wrap past their one-line boxes (ink-outside-rects on
render) even though lint passed — items shortened to single lines; the harness is the deterministic
gate that covers this class, no new check needed.
FEEDBACK VALIDATOR side-effect: `slidekit.feedback.store` validates each comment's `component`
against the live catalog, so FB-009's `component: two-column` would no longer validate once the
component was gone. Retargeted FB-009's component to `comparison-columns` (the surviving family
member that absorbed its role) with the original intent preserved in the comment + notes. This is
the honest minimum; a general "retired-component" allowance in the feedback schema would be scope
creep and is NOT added.

## Operator-approved removals executed (2026-07-02)

Per operator ("remove the items you suggest I get rid of; keep or archive the ones you
think I should"): (1) vendored integrations/agency-agents pruned 300→11 files — kept the
slidekit-authored agents + two upstream files with slidekit edits in integrations/agents/
(+ upstream MIT license); (2) GitHub issue-form feedback channel fully removed (template,
workflow, generator, parser, tests) — the website is the sole channel; (3) pr-brainstorm
workflow + BRAINSTORM_PROMPT removed — IDEAS.md stays as operator-curated ledger; (4)
docs/yaml-vs-html-executive-summary.{md,pdf} deleted; (5) ops/reports/ older than
2026-06-18 archived to ops/reports/archive/. Kept: examples/pdf/combined/ snapshots,
calibration_report.json. Prompt gained a CHANNEL & TREE CLEANUP addendum so sessions
don't resurrect removed pieces.

## Website review workflow: approve/flag state + gallery + before/after (2026-07-02)

Operator requests: (a) a 👍 should remove a layout from the site's main page; (b) a
separate all-thumbnails page with click-to-zoom for reference; (c) a 👎 should later show
a before/after comparison on the main page so fixes can be verified visually.

Design: `web/data/state.json` (committed; written ONLY by scripts/feedback_intake_web.py)
maps component → {status: approved|flagged, date, comment, before}. 👍 → approved (hidden
from the review queue, ✓ chip in the gallery; clears any flag). 👎 → flagged + a snapshot
of the component's CURRENT previews.json fragment as `before`; when a fix regenerates
previews.json, the review queue renders before vs current side by side until the operator
approves; a repeat 👎 refreshes the snapshot. Notes (comment, no verdict) don't touch
state. Stale entries for deleted layouts are dropped on fold (two-column was deleted by a
burst session under FB-009). The main page (index/app.js) is now the review queue (flagged
first, then pending); gallery.html/gallery.js is the full thumbnail grid with a lightbox.
Seeded state.json with the 9 layouts flagged 2026-07-02 (before = previews at commit
c222d5c, pre-fix) so the operator can review tonight's burst fixes as comparisons.
Sessions MUST NOT edit state.json (prompt addendum "OPERATOR REVIEW STATE").

## Web feedback round 2: FB-018..FB-025 (2026-07-02, operator batch of 23 marks)

Root cause worth remembering: the HTML preview renderer (emit/html_preview.py) silently
DROPPED box nodes and per-node text colours, so the website showed slides without accent
bars, KPI rules, chart bars, the VS badge, or the code slide's syntax colours (dark text
on the dark code panel). Several flags (FB-021, FB-023) were really THIS bug. Fixed and
pinned by tests/test_emit/test_preview_fidelity.py — the preview must carry every node
type and colour/alignment attribute the emitters do.

New capability: ResolvedNode.align ("center" | None=left), honoured identically by the
pptx / pdf / html emitters. Geometry rects stay the contract; align only places glyphs
inside them.

Per-item outcomes (intent pinned by tests/test_layout/test_feedback_fixes.py):
- FB-018 title-slide: title(+subtitle) block vertically centred on the full content area,
  text stays left-aligned ("left-center").
- FB-019 big-number: value = 1.75x title tier (105pt default), whole stack centred, left
  accent bar replaced by a short centred accent rule under the value.
- FB-020 bullet-list specimen: 3 items.
- FB-021 code specimen: hello-world program (comment/code/terminal lines) so the colour
  roles are visible; plus the preview-colour fix above.
- FB-022: pros-cons DELETED; before-after RENAMED two-panel-list (left/right ListPanel,
  right = accented state) — one layout for any two-state contrast. YAML: left/right keys.
- FB-023 this-vs-that: badge 0.9"->0.75", "VS" caption-tier centred inside it on both
  axes, badge centred on the value+label block, columns centre-aligned.
- FB-024 kpi-grid: intra-tile gaps 0.3"->0.12" (tile shares a group_id so lint-exempt),
  rule centred under the value, tile text centre-aligned.
- FB-025: chart-slide DELETED; chart-with-insight is the surviving chart layout (the
  recommender now routes bare charts there).

Catalog is now 37 components / 25 distinct families. state.json migration was mechanical
only (dropped deleted layouts exactly as the fold script would; carried before-after's
approved status to its new name) — no review judgement was invented; the "sessions never
edit state.json" rule still stands for review VERDICTS.

## Web feedback round 3: FB-026..FB-029 (2026-07-03)

- GLOBAL STYLE RULE (operator, FB-026): **never use bullets.** Square list markers
  removed from every list layout (bullet-list, two-panel-list panels, swot quadrants,
  roadmap items); items are flush-left lines. Colour semantics + non-text mark now come
  from thin rules (accent under a list title; panel/quadrant-coloured under headings).
  Pinned by test_lists_have_no_bullet_markers — any future layout that emits a small
  square box beside list items fails it.
- FB-027: code layout speaks VS Code Dark+ — a deterministic regex tokenizer
  (_code_line_runs) colours keywords/declarations/strings/numbers/comments/function
  names/terminal $; each run is its own measured node placed by measuring the ACTUAL
  prefix substring (no cumulative rounding drift). Background #1E1E1E.
- FB-028 (supersedes FB-023's badge rework): this-vs-that is a bare typographic
  face-off — default text colour everywhere, no box around a muted "VS"; the component
  is exempted from W_TEXT_ONLY by operator decision.
- FB-029: testimonial deleted (too similar to pull-quote); quote+portrait recommends
  pull-quote now. Catalog: 36 components / 24 distinct families.

## Website: anchor-first family grouping (2026-07-03, operator picked option 2 of 3)

Both pages now surface the family/variant taxonomy (previews.json carries family/role/
variant_of/differs_by from the registry):
- Review queue: unreviewed layouts group anchor-first per family — one card per distinct
  skeleton, remaining pending variants behind a "▸ N variants" expander (cards show a
  "differs by: …" chip). Flagged cards are unchanged (always fully visible, before/after).
- Gallery: one tile per family (the anchor); a "+N" chip fans the variants out inline as
  dashed tiles ("Expand all variants" control above the grid). The +N chip turns red when
  a collapsed variant is flagged so nothing hides.
- CSS gotcha codified in a comment: class display rules (grid/block) silently defeat the
  [hidden] attribute — a global `[hidden]{display:none!important}` guard now prevents it.

## Web feedback round 4: FB-030..FB-042 (2026-07-04, 17 marks: 4 approvals + 13 flags)

Approved: kpi-grid (clears its FB-024 flag), chart-with-insight, funnel, pyramid.

- FB-030 bullet-list: the title accent rule (added as the FB-026 non-text mark) is gone
  — "drop the orange, ugly color line". bullet-list is now pure typography and joins the
  W_TEXT_ONLY exempt list. Lesson: a compensatory decoration added for a lint warning is
  still decoration; the operator notices.
- FB-031 code: background reverted to the original deep-teal #0C1A1C — Dark+ token
  colours stay. The operator liked HALF of FB-027; feedback applies per-property.
- FB-032 this-vs-that: VS caption→body tier; middle gutter 0.75"→1.0" so the bigger VS
  clears E_OVERFLOW with standard insets.
- FB-033 table-slide: header row hugs the accent rule (0.12" inner gap, shared group_id
  — same E_GAP-exempt pattern as the panel-heading rules).
- FB-034 metric-comparison root cause: each column vertically self-centred on its OWN
  wrapped-label height, so values drifted to different heights. All columns now share
  one rhythm (rows sized to the tallest label) and centre within their column.
- FB-035 process-steps REIMAGINED: filled chip badges → large accent numerals (01/02)
  over hairline rules + bold label + body. Motif borrowed from layouts the operator has
  approved (agenda numerals, kpi-grid rules) — precedent is the best design guide.
- FB-036 roadmap: _panel_items grew pack=True (stack at GAP_MIN instead of distributing
  across the lane) — even distribution of few items read as disconnected floating lines.
- FB-037 matrix-2x2 REIMAGINED: hairline MUTED cross, bold centred quadrant labels, new
  optional `highlight: <0-3>` puts accent on at most one quadrant.
- FB-038 swot: IR enforces exactly ONE statement per category (max_length=1); single
  item renders at full body tier (T-064 caption-density compromise retired).
- FB-039 comparison-matrix REIMAGINED + operator DESIGN RULE: **matrices highlight one
  or two ITEMS, never categories.** Category boxes removed (plain bold text + thin header
  rule); new `highlights: [[row, col], ...]` (≤2) renders winning cells as accent chips —
  the only colour in the matrix body. The rule also drove matrix-2x2's `highlight`.
- FB-040..042 deleted team-grid, image-full-bleed, image-grid ("delete this one" ×3).
  logo-wall becomes the labeled-image-grid anchor; recommender: people→card-grid,
  images→image-half-bleed. Catalog now **33 components / 22 distinct families**.
- Golden regen restored 21 files whose diff was node_id churn only; the 12 kept diffs are
  exactly the changed layouts + the two showcase decks that embed them.
