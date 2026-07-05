"""The deterministic recommender maps content shapes to the right component."""

from slidekit.catalog.registry import catalog
from slidekit.select.recommend import ContentFeatures, recommend


def _top(**kw):
    return recommend(ContentFeatures(**kw))[0].component


def test_single_value_to_big_number():
    assert _top(single_value=True) == "big-number"


def test_ordered_narrowing_to_funnel_widening_to_pyramid():
    assert _top(ordered=True, items=4, trend="narrowing") == "funnel"
    assert _top(ordered=True, items=4, trend="widening") == "pyramid"


def test_ordered_steps_orientation():
    assert _top(ordered=True, items=4) == "numbered-steps"
    assert _top(ordered=True, items=4, horizontal=True) == "process-steps"


def test_two_groups_vs_and_default():
    assert _top(groups=2, vs=True) == "this-vs-that"
    assert _top(groups=2, items=6) == "comparison-columns"


def test_quote_variants():
    assert _top(quote=True, portrait=True) == "pull-quote"  # testimonial retired (FB-029)
    assert _top(quote=True) == "pull-quote"


def test_chart_and_insight():
    assert _top(chart=True) == "chart-with-insight"  # bare chart-slide retired (FB-025)
    assert _top(chart=True, insight=True) == "chart-with-insight"


def test_metrics_shapes():
    assert _top(metrics=3, grid=True) == "kpi-grid"
    assert _top(metrics=3, deltas=True) == "metric-comparison"
    assert _top(metrics=3) == "stat-callout"


def test_matrices_and_tables():
    assert _top(swot=True) == "swot"
    assert _top(axes=True) == "card-grid"  # matrix-2x2 retired (FB-044)
    assert _top(options_criteria=True) == "comparison-matrix"
    assert _top(table=True) == "table-slide"


def test_image_and_people():
    # team-grid / image-full-bleed / image-grid retired (FB-040..FB-042): people
    # fall back to card-grid cards; any image count routes to image-half-bleed.
    assert _top(people=4) == "card-grid"
    assert _top(logos=6) == "card-grid"  # logo-wall retired (FB-046)
    assert _top(images=1) == "image-half-bleed"
    assert _top(images=4) == "image-half-bleed"


def test_code_and_plain_list():
    assert _top(code=True) == "code"
    assert _top(items=5) == "bullet-list"


def test_determinism_and_validity():
    f = ContentFeatures(groups=2, items=6)
    assert recommend(f) == recommend(f)  # stable
    for s in recommend(f, top=3):
        assert s.component in catalog()


def test_always_returns_something():
    assert recommend(ContentFeatures())  # empty -> catch-all
