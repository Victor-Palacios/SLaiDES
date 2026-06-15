"""Phase 10 — deterministic aesthetic scoring over the ResolvedDeck.

Advisory (not a build gate). Computes geometry/colour sub-scores from source — no
rendering, no vision — exactly like the linter proves correctness. See
docs/AESTHETICS.md. This is a first cut: balance, whitespace, alignment,
non-overlap, hierarchy, and contrast. Colour-harmony and cross-slide consistency
are TODO (documented).
"""

from slidekit.aesthetics.score import (
    AestheticReport,
    SlideScore,
    DEFAULT_WEIGHTS,
    score_deck,
)

__all__ = ["AestheticReport", "SlideScore", "DEFAULT_WEIGHTS", "score_deck"]
