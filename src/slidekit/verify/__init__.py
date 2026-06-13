"""Phase 6 verification harness — CI-only renderer drift detector.

This package renders emitted .pptx decks through LibreOffice + poppler and runs
cheap, deterministic pixel heuristics (no LLM, no human) against the geometry the
layout engine computed. Its job is to catch *systematic drift* between our text
measurement / box math and a real renderer, NOT to QA individual decks.

It is explicitly **not** part of deck generation. The build/lint/emit loop never
touches this code; only CI does, on layout/metrics changes. If this harness ever
disagrees with the linter, the fix goes into metrics/layout/slack constants —
never into a per-deck visual loop.
"""

from slidekit.verify.harness import (
    DeckVerifyResult,
    SlideVerifyResult,
    VerifyConfig,
    tools_available,
    verify_deck_yaml,
)

__all__ = [
    "DeckVerifyResult",
    "SlideVerifyResult",
    "VerifyConfig",
    "tools_available",
    "verify_deck_yaml",
]
