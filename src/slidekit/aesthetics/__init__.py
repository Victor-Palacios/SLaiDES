"""Phase 10 — deterministic aesthetic scoring over the ResolvedDeck.

Advisory (not a build gate). Computes geometry/colour sub-scores from source — no
rendering, no vision — exactly like the linter proves correctness. See
docs/AESTHETICS.md. Sub-scores: balance, whitespace, alignment, non-overlap,
hierarchy, contrast (size-aware WCAG targets), richness (visual engagement), and
colour-harmony; the deck score is modulated by cross-slide consistency.
"""

from slidekit.aesthetics.score import (
    AestheticReport,
    AestheticWarning,
    SlideScore,
    DEFAULT_WEIGHTS,
    ADVISORY_THRESHOLDS,
    score_deck,
)

__all__ = [
    "AestheticReport",
    "AestheticWarning",
    "SlideScore",
    "DEFAULT_WEIGHTS",
    "ADVISORY_THRESHOLDS",
    "score_deck",
]
