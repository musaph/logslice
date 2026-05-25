"""Tests for logslice.log_correlator."""
import pytest

from logslice.log_correlator import (
    CorrelationGroup,
    CorrelationResult,
    correlate,
    format_correlation_summary,
    iter_correlated_lines,
)

_JSON_A = '{"request_id": "abc", "msg": "start"}'
_JSON_B = '{"request_id": "abc", "msg": "end"}'
_JSON_C = '{"request_id": "xyz", "msg": "only"}'
_PLAIN = "no fields here"


def _lines(*args: str):
    return list(args)


def test_empty_input_returns_empty_result():
    result = correlate([], "request_id")
    assert result.total_groups == 0
    assert result.total_matched == 0
    assert result.unmatched == []


def test_lines_without_field_go_to_unmatched():
    result = correlate([_PLAIN], "request_id")
    assert result.unmatched == [_PLAIN]
    assert result.total_groups == 0


def test_matching_lines_grouped_by_field():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id")
    assert result.total_groups == 2
    keys = {g.key for g in result.groups}
    assert "abc" in keys
    assert "xyz" in keys


def test_group_contains_correct_lines():
    result = correlate([_JSON_A, _JSON_B], "request_id")
    assert result.total_groups == 1
    group = result.groups[0]
    assert group.key == "abc"
    assert _JSON_A in group.lines
    assert _JSON_B in group.lines


def test_groups_sorted_largest_first():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id")
    assert result.groups[0].key == "abc"
    assert result.groups[0].count == 2


def test_min_group_size_moves_small_groups_to_unmatched():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id", min_group_size=2)
    assert result.total_groups == 1
    assert result.groups[0].key == "abc"
    assert _JSON_C in result.unmatched


def test_total_matched_counts_all_group_lines():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id")
    assert result.total_matched == 3


def test_iter_correlated_lines_yields_all_matched():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id")
    yielded = list(iter_correlated_lines(result))
    assert len(yielded) == 3
    assert set(yielded) == {_JSON_A, _JSON_B, _JSON_C}


def test_iter_correlated_lines_largest_group_first():
    result = correlate([_JSON_A, _JSON_B, _JSON_C], "request_id")
    yielded = list(iter_correlated_lines(result))
    # first two lines should belong to 'abc' group
    assert _JSON_A in yielded[:2]
    assert _JSON_B in yielded[:2]


def test_format_summary_contains_counts():
    result = correlate([_JSON_A, _JSON_B, _JSON_C, _PLAIN], "request_id")
    summary = format_correlation_summary(result)
    assert "groups=2" in summary
    assert "matched=3" in summary
    assert "unmatched=1" in summary


def test_format_summary_lists_group_keys():
    result = correlate([_JSON_A, _JSON_B], "request_id")
    summary = format_correlation_summary(result)
    assert "abc" in summary


def test_correlation_group_count_property():
    g = CorrelationGroup(key="k", lines=["a", "b", "c"])
    assert g.count == 3
