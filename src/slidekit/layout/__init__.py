"""Layout engine — resolves DeckIR to absolute EMU geometry."""

from slidekit.layout.engine import resolve
from slidekit.layout.models import Rect, ResolvedDeck, ResolvedNode, ResolvedSlide

__all__ = ["resolve", "Rect", "ResolvedDeck", "ResolvedNode", "ResolvedSlide"]
