"""The metadata registry must cover exactly the IR components, with coherent families."""

from typing import get_args

from slidekit.catalog.registry import catalog, distinct_families
from slidekit.ir.models import Slide


def _component_keys() -> set:
    keys = set()
    for model in get_args(get_args(Slide)[0]):
        keys.add(get_args(model.model_fields["component"].annotation)[0])
    return keys


def test_registry_covers_exactly_the_components():
    assert set(catalog().keys()) == _component_keys()


def test_every_entry_has_selection_metadata():
    for key, lo in catalog().items():
        assert lo.purpose and lo.use_when and lo.content_shape, key
        assert lo.family, key
        assert lo.role in ("anchor", "variant"), key


def test_variants_point_at_a_real_anchor_in_their_family():
    cat = catalog()
    anchors = {l.component: l for l in cat.values() if l.role == "anchor"}
    # exactly one anchor per family
    by_family: dict = {}
    for lo in cat.values():
        if lo.role == "anchor":
            by_family.setdefault(lo.family, []).append(lo.component)
    for fam, anch in by_family.items():
        assert len(anch) == 1, f"family {fam} has {len(anch)} anchors: {anch}"
    # each variant references its family's anchor
    for lo in cat.values():
        if lo.role == "variant":
            assert lo.variant_of in anchors, lo.component
            assert anchors[lo.variant_of].family == lo.family, lo.component
            assert lo.differs_by, lo.component


def test_distinct_count_is_smaller_than_component_count():
    cat = catalog()
    fams = distinct_families()
    # honest: fewer distinct skeletons than components
    assert len(fams) < len(cat)
    # anchors == families
    assert sum(1 for l in cat.values() if l.role == "anchor") == len(fams)


def test_required_fields_derived_from_schema():
    cat = catalog()
    # bullet-list requires title + items; title is required (not Optional)
    assert "items" in cat["bullet-list"].required_fields
    # two-column's title is optional
    assert "title" in cat["two-column"].optional_fields
