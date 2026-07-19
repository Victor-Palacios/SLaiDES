# Research paper consolidated summary

The previous per-paper PDFs in this directory have been replaced by one consolidated PDF:

- `research-paper-summaries.pdf` — includes each verified reference from `docs/REFERENCES.md`, its publication year, a GitHub repository link when one is identified for the paper, the paper abstract, and 10 bullet points summarizing distinctive aspects of the work.
- `top-5-related-papers.pdf` — a focused companion covering the **five** references most tightly coupled to this repo's goals and code (the no-render, geometry-only layout/aesthetic scorer in `src/slidekit/aesthetics/score.py`, the linter, and the layout engine), with **seven main points about each paper itself** (not its relationship to slidekit). Regenerate with `python scripts/build_top5_papers_pdf.py`. Selection follows `docs/RESEARCH_TRACE.md`: AeSlides (verifiable layout rewards), Kikuchi et al. (closed-form alignment/overlap metrics), Ngo/Teo/Byrne (14 geometric aesthetic measures), Harrington et al. (non-linear aggregation, shipped as the `harrington` combine mode), and O'Donovan et al. (energy-based layout with learned weights).
