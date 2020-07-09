import sys
from dataclasses import dataclass
from typing import List, Tuple

from .span import Span

EMPTY_LABEL = 0
ENTITY_LABEL = 1


@dataclass
class Counters:
    tp: float = 0
    fp: float = 0
    fn: float = 0


def sort_and_glue_overlapped(spans: List[Span]) -> Tuple[List[Span], bool]:
    """
    Function sorts spans and glue overlapped together.
    @param spans: spans to process
    @return: tuple of sorted spans and flag if some of them were glued.
    """
    sorted_spans = sorted(spans, key=lambda span: span.start)
    prev_span_end = -1
    has_overlapped = False
    filtered = []
    for s in sorted_spans:
        if prev_span_end > s.start:
            has_overlapped = True
            prev_span_end = max(filtered[-1].finish, s.finish)
            filtered[-1].finish = prev_span_end  # continue previous spans if it's needed
        else:
            filtered.append(s)
            prev_span_end = s.finish
    return filtered, has_overlapped


def _sort_and_check_spans(spans: List[Span], arg_label: str) -> List[Span]:
    res = sorted(spans, key=lambda x: x.start)
    for s in res:
        if s.start > s.finish:
            raise ValueError(f"Span with finish before start is found in argument {arg_label}: {s}")
    if len(res) > 1:
        for s1, s2 in zip(res, res[1:]):
            if s1.finish > s2.start:
                raise ValueError(f"Overlapped spans are found in argument {arg_label}: {s1} and {s2}")
    return res


def calc_counters_with_partial(actual_spans: List[Span], expected_spans: List[Span],
                               partial_stimulation: float = 0.75) -> Counters:
    """
    Function calculates TP, FP & FN counters using span-level. Partial matches add to the TP as part
    of intersection multiple by the partial_penalty factor.
    @param actual_spans: Spans found by recognizer. It is assumed that spans are non-overlapping.
    @param expected_spans: Gold Standard spans. It is assumed that spans are non-overlapping.
    @param partial_stimulation: stimulation factor for partial matched spans [0.0...1.0]
    @return: Counters instance with filled fields.
    """

    if not 0.0 <= partial_stimulation <= 1.0:
        raise ValueError(f"partial_stimulation must be between 0.0 and 1.0, got {partial_stimulation} instead.")
    if len(actual_spans) == 0 and len(expected_spans) == 0:
        return Counters(0, 0, 0)
    actual_spans = _sort_and_check_spans(actual_spans, "actual_spans")
    expected_spans = _sort_and_check_spans(expected_spans, "expected_spans")
    total_actual = len(actual_spans)
    total_expected = len(expected_spans)

    # Calculate exact matches
    expected_dict = {s.start: s for s in expected_spans}
    missing_actual = []
    for a in actual_spans:
        if a.start in expected_dict and a.finish == expected_dict[a.start].finish:
            del expected_dict[a.start]
        else:
            if a.start < a.finish:  # skip zero-length spans
                missing_actual.append(a)

    # Calculate partial matches
    missing_actual = sorted(missing_actual, key=lambda x: x.start)
    exactly_matched = total_actual - len(missing_actual)
    # Add pseudo Span far from the last symbol, so we always have at least one expected element at the end.
    expected_unmatched = sorted(list(expected_dict.values())+[Span(sys.maxsize, sys.maxsize)], key=lambda x: x.start)
    expected_unmatched_pos = 0
    tpp = 0.0
    for ma in missing_actual:
        while True:
            current_expected = expected_unmatched[expected_unmatched_pos]
            if current_expected.finish <= ma.start:
                expected_unmatched_pos += 1
            else:
                break
        if ma.finish <= expected_unmatched[expected_unmatched_pos].start:
            # this missed actual is not match with any unaccounted expected
            continue
        ma_len = ma.finish-ma.start
        ex_len = current_expected.finish-current_expected.start
        overlapped_len = min(current_expected.finish, ma.finish) - max(current_expected.start, ma.start)
        tpp += overlapped_len / max(ma_len, ex_len)
        expected_unmatched_pos += 1
    tp = exactly_matched + tpp * partial_stimulation
    fp = total_actual - tp
    fn = total_expected - tp
    return Counters(tp=tp, fp=fp, fn=fn)

