import pytest

from loio_metrics import calc_counters_with_partial, Span, parse_ltf
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


def test_calc_counters_with_partial_diagnostics_s_factor():
    with pytest.raises(ValueError):
        calc_counters_with_partial([], [], partial_stimulation=-0.1)

    with pytest.raises(ValueError):
        calc_counters_with_partial([], [], partial_stimulation=1.1)

    assert calc_counters_with_partial([], [], partial_stimulation=0) is not None
    assert calc_counters_with_partial([], [], partial_stimulation=1) is not None
    assert calc_counters_with_partial([], [], partial_stimulation=0.5) is not None


def metrics_for_ltf(expected, actual, partial_stimulation=0.75):
    expected_txt, expected_spans = parse_ltf(expected)
    actual_txt, actual_spans = parse_ltf(actual)
    # We should work with the same text
    assert expected_txt == actual_txt
    return calc_counters_with_partial(actual_spans, expected_spans, partial_stimulation)


def test_calc_counters_1():
    expected = '<body>To <e>be or not to be</e>.</body>'
    actual = '<body>To be or <e>not</e> <e>to</e> <e>be</e>.</body>'
    counters = metrics_for_ltf(expected, actual, 1)
    assert counters.tp == 0.2


def test_calc_counters_2():
    expected = '<body>To be or <e>not</e> <e>to</e> <e>be</e>.</body>'
    actual = '<body>To <e>be or not to be</e>.</body>'
    counters = metrics_for_ltf(expected, actual, 1)
    assert counters.tp == 0.2


def test_calc_counters_productivity():
    expected = [Span(i * 10, i * 10 + 6) for i in range(100000)]
    actual = [Span(s.start + 3, s.finish + 3) for s in expected]
    counters = calc_counters_with_partial(expected, actual, 1)
    assert counters.tp == len(expected)*0.5


def test_calc_counters_productivity2():
    expected = [Span(i * 10, i * 10 + 6) for i in range(100000)]
    actual = [Span(i * 12, i * 12 + 6) for i in range(100000)]
    counters = calc_counters_with_partial(expected, actual, 1)
    assert counters.tp > 0
