#!/usr/bin/env python3
"""Build `docs/research/summary/top-5-related-papers.pdf`.

A focused companion to the consolidated `research-paper-summaries.pdf`: the FIVE
references from `docs/REFERENCES.md` most tightly coupled to this repo's goals and
code (the no-render, geometry-only layout / aesthetic scorer in
`src/slidekit/aesthetics/score.py`, the linter, and the layout engine), each with
SEVEN main points about the paper itself (not its relationship to slidekit).

Selection rationale (see docs/RESEARCH_TRACE.md, which maps each scorer decision to
a reference): these five are the primary sources behind the core layout metrics —
verifiable rewards / whitespace / overlap / balance (AeSlides), closed-form
alignment + overlap over bounding boxes (Kikuchi et al.), the 14 closed-form
aesthetic measures (Ngo/Teo/Byrne), the non-linear aggregation of geometric
measures actually shipped as the `harrington` combine mode (Harrington et al.), and
the energy-based layout model with learned weights (O'Donovan et al.).

Usage:
  python scripts/build_top5_papers_pdf.py
"""
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "research" / "summary" / "top-5-related-papers.pdf"

INK = HexColor("#1a1d24")
MUTED = HexColor("#5b6270")
ACCENT = HexColor("#1e5aa8")
RULE = HexColor("#c9cfda")

# ---------------------------------------------------------------------------
# Content: the five papers, each with metadata and SEVEN main points about the
# paper itself. Ordered by how central the work is to slidekit's goals/code.
# ---------------------------------------------------------------------------
PAPERS = [
    {
        "rank": 1,
        "title": "AeSlides: Incentivizing Aesthetic Layout in LLM-Based Slide "
        "Generation via Verifiable Rewards",
        "authors": "Yiming Pan, Chengwei Hu, Xuancheng Huang, Can Huang, Mingming "
        "Zhao, Yuean Bi, Xiaohan Zhang, Aohan Zeng, Linmei Hu",
        "year": "2026",
        "venue": "Preprint",
        "ids": "arXiv:2604.22840 · code: github.com/ympan0508/aeslides",
        "gist": "Trains an LLM slide generator with reinforcement learning against "
        "cheap, checkable layout metrics instead of costly visual inspection.",
        "points": [
            "Motivating problem: LLM slide generation is a text-in / text-out "
            "process, yet the quality that matters to a viewer is visual and "
            "spatial — so optimizing the text objective alone leaves layout "
            "aesthetics unaddressed.",
            "Prior remedies are expensive or indirect: vision-based “reflection” "
            "loops that render and critique each draft, or fine-tuning on aesthetic "
            "labels that only indirectly touches layout. AeSlides argues for a "
            "direct, quantitative reward instead.",
            "Method: a GRPO-style reinforcement-learning setup where the reward is "
            "computed from verifiable layout metrics — described as accurate, "
            "efficient, and low-cost — rather than from a learned reward model or "
            "human/vision feedback.",
            "Defines four layout-quality signals it can check automatically: "
            "aspect-ratio compliance, whitespace distribution, element "
            "collision / overlap, and visual imbalance.",
            "The metrics are evaluated on the rendered slide (a browser/Playwright "
            "render of the generated layout), turning each into a scalar reward term "
            "with no separate reward network in the loop.",
            "Results: training on 5,000 prompts with GLM-4.7-Flash lifted "
            "aspect-ratio compliance from 36% to 85%, cut whitespace problems ~44%, "
            "element collisions ~43%, and visual imbalance ~28%.",
            "Human evaluation rose from 3.31 to 3.56 (+7.6%), and the verifiable-"
            "reward approach beat both model-based reward optimization and "
            "reflection baselines — evidence that deterministic, checkable layout "
            "metrics are a viable training signal.",
        ],
    },
    {
        "rank": 2,
        "title": "Constrained Graphic Layout Generation via Latent Optimization",
        "authors": "Kotaro Kikuchi, Edgar Simo-Serra, Mayu Otani, Kota Yamaguchi",
        "year": "2021",
        "venue": "ACM Multimedia 2021 (pp. 88–96)",
        "ids": "DOI:10.1145/3474085.3475497 · arXiv:2108.00871 · "
        "code: github.com/ktrk115/const_layout",
        "gist": "Generates design layouts that satisfy alignment / non-overlap / "
        "relational constraints by optimizing in a generative model's latent space.",
        "points": [
            "Addresses automatic graphic-design layout — arranging labeled "
            "bounding boxes (text, image, button…) on a canvas — in a way that "
            "obeys the design constraints a real designer would impose.",
            "Core idea (“latent optimization”): keep a pretrained generative "
            "layout model fixed and, at test time, search its latent space so the "
            "output satisfies constraints — avoiding a separate retraining for "
            "every new constraint type.",
            "The generator is a Transformer-based model that produces a layout as a "
            "sequence of elements, each with a category label and a bounding box.",
            "One model covers many tasks: unconstrained generation, generation with "
            "some elements fixed, size/position relationships between elements, and "
            "“beautification” of a rough layout.",
            "Constraints (alignment, overlap avoidance, and user-specified relations "
            "among elements) are expressed as differentiable objectives that steer "
            "the latent search while keeping outputs realistic.",
            "Uses the now-standard closed-form layout metrics computed purely from "
            "bounding boxes: Overlap (average pairwise overlapping area between "
            "elements) and Alignment (each element's minimal edge/center "
            "misalignment to the others), both normalized by element count.",
            "Evaluated on public layout datasets (e.g. Rico, PubLayNet, Magazine); "
            "improves constraint satisfaction and layout quality over baselines, with "
            "code released for reproduction.",
        ],
    },
    {
        "rank": 3,
        "title": "Modelling Interface Aesthetics",
        "authors": "David Chek Ling Ngo, Lian Seng Teo, John G. Byrne",
        "year": "2003",
        "venue": "Information Sciences 152:25–46",
        "ids": "DOI:10.1016/S0020-0255(02)00404-8",
        "gist": "Proposes 14 closed-form measures that quantify the aesthetics of a "
        "screen layout directly from the geometry of its objects.",
        "points": [
            "Advances a quantitative theory of interface aesthetics: the visual "
            "appeal of a screen layout can be measured mathematically from the "
            "positions and sizes of its objects, not just judged subjectively.",
            "Defines fourteen aesthetic measures, each a closed-form function of the "
            "objects' bounding boxes and each scaled to roughly [0, 1] so layouts "
            "can be compared numerically.",
            "The fourteen measures: balance, equilibrium, symmetry, sequence, "
            "cohesion, unity, proportion, simplicity, density, regularity, economy, "
            "homogeneity, rhythm, and order-and-complexity.",
            "Balance is the distribution of “optical weight” (element area) about "
            "the vertical and horizontal axes; equilibrium places the center of "
            "mass near the layout center; symmetry scores axial mirroring of "
            "elements.",
            "Other measures encode distinct design/Gestalt ideas: cohesion "
            "(consistency of element aspect ratios), economy (few distinct sizes), "
            "regularity (consistent spacing and alignment), and rhythm (regular "
            "repetition across the layout).",
            "The authors score real interface layouts with the measures and show "
            "they distinguish well-organized arrangements from poor ones, giving "
            "worked numeric examples.",
            "It became a foundational, heavily-cited reference for computational "
            "aesthetics: reproducible formulas that let automated-layout and "
            "evaluation systems treat beauty as a computed quantity.",
        ],
    },
    {
        "rank": 4,
        "title": "Aesthetic Measures for Automated Document Layout",
        "authors": "Steven J. Harrington, J. Fernando Naveda, Rhys Price Jones, "
        "Paul Roetling, Nishant Thakkar",
        "year": "2004",
        "venue": "ACM Symposium on Document Engineering (DocEng '04)",
        "ids": "DOI:10.1145/1030397.1030419",
        "gist": "Gives an automated layout system a computable aesthetic objective, "
        "combining geometric measures non-linearly so one flaw dominates the score.",
        "points": [
            "Goal: equip an automatic document-layout engine with a computable "
            "aesthetic objective so it can rank and choose among candidate page "
            "layouts without a human in the loop.",
            "Defines heuristic, closed-form measures for the attributes that degrade "
            "layout quality: alignment, regularity, separation, balance, white-space "
            "fraction, white-space free-flow, proportion, uniformity, and page "
            "security.",
            "Each measure is normalized so 1 is ideal and lower is worse — e.g. "
            "alignment from a histogram of element edge positions, white-space "
            "fraction from the proportion of empty page area.",
            "Central methodological claim: the individual measures must be combined "
            "NON-linearly, not by a plain weighted average that lets a good feature "
            "mask a bad one.",
            "The proposed aggregation V = [&Sigma; w<sub>i</sub> "
            "(d + V<sub>i</sub>)<super>&minus;p</super>]<super>&minus;1/p</super> "
            "&minus; d is a weighted power-mean with a small offset d, so a single "
            "very bad sub-measure drags the whole score down toward failure.",
            "The weights w<sub>i</sub> set the relative importance of each rule, "
            "and the exponent p tunes how aggressively the worst feature dominates "
            "the combined value.",
            "Demonstrated on automated page layout, the paper contributes both a "
            "concrete measure set and the enduring argument — adopted by many later "
            "systems — that aesthetic aggregation should be non-linear.",
        ],
    },
    {
        "rank": 5,
        "title": "Learning Layouts for Single-Page Graphic Designs",
        "authors": "Peter O'Donovan, Aseem Agarwala, Aaron Hertzmann",
        "year": "2014",
        "venue": "IEEE Transactions on Visualization and Computer Graphics "
        "20(8):1200–1213",
        "ids": "DOI:10.1109/TVCG.2014.48 · project: dgp.toronto.edu/~donovan/layout/",
        "gist": "An energy-based model of single-page layout whose geometric terms "
        "are weighted by parameters learned from a few example designs.",
        "points": [
            "Presents an energy-based model for single-page graphic-design layouts "
            "built from established graphic-design principles.",
            "The energy is a weighted sum of terms that are functions of element "
            "bounding boxes — alignment, overlap, symmetry, and white space / "
            "uniform spacing — plus terms for predicted importance and reading "
            "flow.",
            "Contributes supporting analysis algorithms: prediction of an element's "
            "perceived importance, automatic alignment detection, and hierarchical "
            "(multi-scale) segmentation of a design.",
            "Rather than hand-tuning the term weights, it learns them from a small "
            "set of example layouts via Nonlinear Inverse Optimization (NIO).",
            "New layouts are produced by optimizing (minimizing) the learned energy, "
            "yielding arrangements consistent with the design preferences the "
            "examples encode.",
            "Demonstrated applications: synthesizing layouts in different styles, "
            "retargeting a design to a new page size or aspect ratio, and improving "
            "or refining an existing layout.",
            "An influential demonstration that design judgment can be captured as a "
            "learnable, weighted combination of geometric energy terms and then "
            "optimized — linking heuristic aesthetic measures to data-driven design.",
        ],
    },
]


def build() -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5,
        leading=15, textColor=INK, alignment=TA_JUSTIFY,
    )
    h_title = ParagraphStyle(
        "h_title", fontName="Helvetica-Bold", fontSize=24, leading=28,
        textColor=INK, spaceAfter=6,
    )
    h_sub = ParagraphStyle(
        "h_sub", fontName="Helvetica", fontSize=12, leading=16, textColor=MUTED,
    )
    paper_title = ParagraphStyle(
        "paper_title", fontName="Helvetica-Bold", fontSize=14.5, leading=18,
        textColor=ACCENT, spaceBefore=4, spaceAfter=3,
    )
    meta = ParagraphStyle(
        "meta", fontName="Helvetica", fontSize=9.5, leading=13, textColor=MUTED,
    )
    gist = ParagraphStyle(
        "gist", parent=body, fontName="Helvetica-Oblique", textColor=INK,
        spaceBefore=4, spaceAfter=4, alignment=TA_LEFT,
    )
    rank_label = ParagraphStyle(
        "rank_label", fontName="Helvetica-Bold", fontSize=10, leading=12,
        textColor=ACCENT, spaceBefore=2,
    )
    section = ParagraphStyle(
        "section", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=INK, spaceBefore=6, spaceAfter=2,
    )
    intro = ParagraphStyle(
        "intro", parent=body, spaceAfter=8,
    )

    story = []

    # --- Title block ---
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Top 5 Related Research Papers", h_title))
    story.append(
        Paragraph(
            "The works most central to slidekit&rsquo;s goals and code &mdash; "
            "with seven main points on each paper", h_sub
        )
    )
    story.append(Spacer(1, 0.12 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=RULE))
    story.append(Spacer(1, 0.16 * inch))

    story.append(
        Paragraph(
            "<b>How these five were chosen.</b> slidekit is an agent-first slide "
            "builder whose distinctive claim is that layout and aesthetic quality "
            "are <i>provable from source</i>: a deterministic engine resolves "
            "element geometry, and a scorer computes metrics directly over that "
            "geometry (element bounding boxes) with no rendering and no vision "
            "model. Against the repository&rsquo;s bibliography of 23 verified "
            "references and its research trace (which maps every scorer decision to "
            "a citation), the five papers below are the ones most tightly coupled to "
            "those goals and to the actual code &mdash; the primary sources behind "
            "verifiable layout rewards, closed-form alignment and overlap metrics, "
            "the fourteen geometric aesthetic measures, the non-linear aggregation "
            "shipped in the scorer, and the energy-based layout model with learned "
            "weights.", intro,
        )
    )
    story.append(
        Paragraph(
            "<b>Note on scope.</b> Each summary describes the paper on its own "
            "terms &mdash; its problem, method, and findings &mdash; not its "
            "relationship to slidekit.", intro,
        )
    )
    story.append(Spacer(1, 0.05 * inch))

    bullet_style = ParagraphStyle(
        "bullet", parent=body, alignment=TA_JUSTIFY, spaceAfter=3,
    )

    for i, p in enumerate(PAPERS):
        if i == 0:
            story.append(Spacer(1, 0.05 * inch))
        else:
            story.append(Spacer(1, 0.22 * inch))
            story.append(HRFlowable(width="100%", thickness=0.75, color=RULE))
            story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph(f"PAPER {p['rank']} OF 5", rank_label))
        story.append(Paragraph(p["title"], paper_title))
        story.append(Paragraph(p["authors"], meta))
        story.append(
            Paragraph(f"{p['year']} &nbsp;&middot;&nbsp; {p['venue']}", meta)
        )
        story.append(Paragraph(p["ids"], meta))
        story.append(Paragraph(p["gist"], gist))
        story.append(Paragraph("Seven main points", section))

        items = [
            ListItem(Paragraph(pt, bullet_style), leftIndent=6, value=n + 1)
            for n, pt in enumerate(p["points"])
        ]
        story.append(
            ListFlowable(
                items, bulletType="1", bulletFontName="Helvetica-Bold",
                bulletFontSize=10.5, bulletColor=ACCENT, leftIndent=22,
                bulletFormat="%s.",
            )
        )

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(
            0.9 * inch, 0.55 * inch,
            "slidekit · docs/research/summary/top-5-related-papers.pdf",
        )
        canvas.drawRightString(
            LETTER[0] - 0.9 * inch, 0.55 * inch, f"Page {doc.page}"
        )
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(OUT), pagesize=LETTER,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.85 * inch,
        title="Top 5 Related Research Papers",
        author="slidekit",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
