"""Component catalog: the single source of truth for layout metadata.

Powers the honest layout taxonomy (docs/LAYOUT_TAXONOMY.md), the LLM-facing selection
catalog/guide (`slidekit catalog`, docs/LAYOUT_SELECTION_GUIDE.md), and the deterministic
recommender. See registry.py.
"""

from slidekit.catalog.registry import Layout, catalog, distinct_families

__all__ = ["Layout", "catalog", "distinct_families"]
