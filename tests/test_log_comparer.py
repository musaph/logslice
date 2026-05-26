"""Tests for logslice.log_comparer."""
import pytest

from logslice.log_comparer import (
    CompareResult,
    compare_logs,
    format_compare_result,
    similarity_percent,
)


def test_empty_inputs_return_zero_result():
    r = compare_logs([], [])
    assert r.total_a == 0
    assert r.total_b == 0
    assert r.common == 0
    assert r.jaccard == 0.0


def test_identical_streams_full_similarity():
    lines = ["alpha", "beta", "gamma"]
    r = compare_logs(lines, lines)
    assert r.common == 3
    assert r.jaccard == 1.0
    assert r.only_in_a == []
    assert r.only_in_b == []


def test_disjoint_streams_zero_similarity():
    r = compare_logs(["aaa"], ["bbb"])
    assert r.common == 0
    assert r.jaccard == 0.0


def test_partial_overlap():
    r = compare_logs(["a", "b", "c"], ["b", "c", "d"])
    assert r.common == 2
    assert "a" in r.only_in_a
    assert "d" in r.only_in_b


def test_jaccard_value_is_correct():
    # |A|=3, |B|=3, |A∩B|=2, |A∪B|=4 → 0.5
    r = compare_logs(["a", "b", "c"], ["b", "c", "d"])
    assert r.jaccard == 0.5


def test_trailing_newlines_stripped():
    r = compare_logs(["line1\n", "line2\n"], ["line1", "line2"])
    assert r.common == 2


def test_blank_lines_ignored():
    r = compare_logs(["", "   ", "real"], ["real"])
    assert r.total_a == 1
    assert r.common == 1


def test_only_in_a_sorted():
    r = compare_logs(["z", "a", "m"], [])
    assert r.only_in_a == sorted(r.only_in_a)


def test_only_in_b_sorted():
    r = compare_logs([], ["z", "a", "m"])
    assert r.only_in_b == sorted(r.only_in_b)


def test_similarity_percent_full():
    r = compare_logs(["x"], ["x"])
    assert similarity_percent(r) == 100.0


def test_similarity_percent_zero():
    r = compare_logs(["x"], ["y"])
    assert similarity_percent(r) == 0.0


def test_format_contains_all_labels():
    r = compare_logs(["a", "b"], ["b", "c"])
    out = format_compare_result(r)
    assert "Lines in A" in out
    assert "Lines in B" in out
    assert "Common lines" in out
    assert "Jaccard" in out
    assert "Similarity" in out


def test_format_shows_correct_numbers():
    r = compare_logs(["a", "b"], ["b", "c"])
    out = format_compare_result(r)
    assert "1" in out  # common
    assert "50.00%" in out
