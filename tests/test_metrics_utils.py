import pytest

from loio_metrics import calc_counters_with_partial, Span
from loio_metrics.metrics_utils import Counters


def test_calc_counters_with_partial_trivials():
    actual = calc_counters_with_partial([], [])
    assert actual == Counters(0, 0, 0)

    actual = calc_counters_with_partial([Span(0, 1)], [Span(2, 3)])
    assert actual == Counters(tp=0, fp=1, fn=1)

    actual = calc_counters_with_partial([], [Span(2, 3)])
    assert actual == Counters(tp=0, fp=0, fn=1)

    actual = calc_counters_with_partial([Span(0, 1), Span(2, 3)], [])
    assert actual == Counters(tp=0, fp=2, fn=0)

    actual = calc_counters_with_partial([Span(0, 10)], [Span(0, 10)])
    assert actual == Counters(tp=1, fp=0, fn=0)


def test_calc_counters_with_partial_diagnostics_overlapping():
    with pytest.raises(ValueError):
        calc_counters_with_partial([Span(0, 4), Span(2, 3)], [])

    with pytest.raises(ValueError):
        calc_counters_with_partial([], [Span(0, 4), Span(2, 3)])

    with pytest.raises(ValueError):
        calc_counters_with_partial([Span(0, 4), Span(3, 4)], [])

    # But touching spans are the normal case:
    assert calc_counters_with_partial([Span(0, 4), Span(4, 5)], []) is not None


def test_calc_counters_with_partial_diagnostics_pos():
    with pytest.raises(ValueError):
        calc_counters_with_partial([Span(5, 3)], [])

    with pytest.raises(ValueError):
        calc_counters_with_partial([], [Span(0, 4), Span(9, 8)])
