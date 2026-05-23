"""Tests for logslice.pattern_filter."""
import pytest

from logslice.pattern_filter import (
    count_pattern_matches,
    extract_pattern_groups,
    filter_by_pattern,
    first_match,
)

LINES = [
    "2024-01-01 INFO  service started",
    "2024-01-01 DEBUG loop iteration 1",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 INFO  request received",
    "2024-01-01 WARN  slow query detected",
]


def _collect(it):
    return list(it)


# --- filter_by_pattern ---

def test_filter_returns_matching_lines():
    result = _collect(filter_by_pattern(LINES, r"INFO"))
    assert len(result) == 2
    assert all("INFO" in l for l in result)


def test_filter_case_insensitive_default():
    result = _collect(filter_by_pattern(LINES, r"error"))
    assert len(result) == 1
    assert "ERROR" in result[0]


def test_filter_case_sensitive():
    result = _collect(filter_by_pattern(LINES, r"error", ignore_case=False))
    assert result == []


def test_filter_invert_excludes_matches():
    result = _collect(filter_by_pattern(LINES, r"INFO", invert=True))
    assert all("INFO" not in l for l in result)
    assert len(result) == 3


def test_filter_empty_input_yields_nothing():
    assert _collect(filter_by_pattern([], r"INFO")) == []


def test_filter_no_match_yields_nothing():
    assert _collect(filter_by_pattern(LINES, r"CRITICAL")) == []


def test_filter_pattern_with_groups():
    result = _collect(filter_by_pattern(LINES, r"(INFO|WARN)"))
    assert len(result) == 3


# --- count_pattern_matches ---

def test_count_returns_correct_number():
    assert count_pattern_matches(LINES, r"INFO") == 2


def test_count_zero_when_no_match():
    assert count_pattern_matches(LINES, r"CRITICAL") == 0


def test_count_all_lines_match_dot_star():
    assert count_pattern_matches(LINES, r".") == len(LINES)


# --- extract_pattern_groups ---

def test_extract_groups_returns_captured_parts():
    lines = ["level=INFO msg=started", "level=ERROR msg=failed"]
    groups = _collect(extract_pattern_groups(lines, r"level=(\w+) msg=(\w+)"))
    assert groups == [["INFO", "started"], ["ERROR", "failed"]]


def test_extract_groups_skips_non_matching():
    lines = ["no match here", "level=DEBUG msg=ok"]
    groups = _collect(extract_pattern_groups(lines, r"level=(\w+)"))
    assert groups == [["DEBUG"]]


def test_extract_groups_empty_groups_list_when_no_capture():
    groups = _collect(extract_pattern_groups(LINES, r"INFO"))
    assert groups == [[], []]


# --- first_match ---

def test_first_match_returns_first_matching_line():
    result = first_match(LINES, r"ERROR")
    assert result is not None
    assert "ERROR" in result


def test_first_match_returns_none_when_no_match():
    assert first_match(LINES, r"CRITICAL") is None


def test_first_match_empty_input_returns_none():
    assert first_match([], r"INFO") is None
