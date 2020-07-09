from dataclasses import dataclass
from itertools import chain
from typing import List, Tuple

import numpy as np

from .span import Span

EMPTY_LABEL = 0
ENTITY_LABEL = 1


@dataclass
class Counters:
    tp: float = 0
    fp: float = 0
    fn: float = 0


def fill_map_entity(text_length: int, spans: List[Span]) -> np.ndarray:
    """
    Fills a characters-level map with ENTITY_LABEL marks
    @param text_length: max text length to contain all the spans.
    @param spans: list of spans.
    @return: map of characters where non-marked characters are equal to EMPTY_LABEL (0)
    and parts of spans are equal to ENTITY_LABEL.
    """
    res = np.zeros(text_length, dtype=np.uint8)
    for s in spans:
        if s.finish - s.start > 0:
            res[s.start:s.finish] = ENTITY_LABEL
    return res


def calc_text_length(actual_spans: List[Span], expected_spans: List[Span]) -> int:
    res = 0
    res = max(chain([res], (s.finish for s in actual_spans), (s.finish for s in expected_spans)))
    return res


def calc_expected_span_len(expected_unmatched_map: np.ndarray, actual: Span) -> int:
    # it's assumed, that all actual span is placed inside expected
    res = actual.finish - actual.start
    for c_pos in range(actual.start - 1, -1, -1):
        if expected_unmatched_map[c_pos]:
            res += 1
        else:
            break
    for c_pos in range(actual.finish, expected_unmatched_map.shape[0]):
        if expected_unmatched_map[c_pos]:
            res += 1
        else:
            break
    return res


def _calc_span_len(map: np.ndarray, start_pos: int) -> int:
    res = 0
    if map[start_pos]:
        for c_pos in range(start_pos - 1, -1, -1):
            if map[c_pos]:
                res += 1
            else:
                break
        for c_pos in range(start_pos, map.shape[0]):
            if map[c_pos]:
                res += 1
            else:
                break
    return res


def _calc_longest_span(expected_unmatched_map: np.ndarray, actual: Span) -> int:
    # Try to find the longest span on the bounds of the actual span.
    actual_len = actual.finish - actual.start
    left_expected_len = _calc_span_len(expected_unmatched_map, actual.start)
    right_expected_len = _calc_span_len(expected_unmatched_map, actual.finish - 1)
    return max(actual_len, left_expected_len, right_expected_len)


def _sort_and_check_spans(spans: List[Span], arg_label: str) -> List[Span]:
    res = sorted(spans, key=lambda x: x.start)
    for s in res:
        if s.start>s.finish:
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
    text_length = calc_text_length(actual_spans, expected_spans)
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
    expected_unmatched = list(expected_dict.values())
    expected_unmatched_map = fill_map_entity(text_length, expected_unmatched)
    tpp = 0.0
    for ma in missing_actual:
        overlapped_chars = np.count_nonzero(expected_unmatched_map[ma.start:ma.finish])
        if overlapped_chars > 0:
            ma_len = ma.finish - ma.start
            divisor = calc_expected_span_len(expected_unmatched_map, ma) if ma_len == overlapped_chars else \
                _calc_longest_span(expected_unmatched_map, ma)

            tpp += overlapped_chars / divisor
            # clear map to prevent consequent found on one ground truth span many short actual spans.
            # Spans are sorted, so don't need to look behind, only forwards.
            last_pos = ma.finish - 1
            if expected_unmatched_map[ma.finish - 1]:
                for c_pos in range(ma.finish, text_length):
                    if expected_unmatched_map[c_pos]:
                        last_pos = c_pos
                    else:
                        break
            expected_unmatched_map[ma.start:last_pos + 1] = 0
    tp = exactly_matched + tpp * partial_stimulation
    fp = total_actual - tp
    fn = total_expected - tp
    return Counters(tp=tp, fp=fp, fn=fn)


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
