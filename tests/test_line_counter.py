"""Tests for logslice.line_counter."""

from __future__ import annotations

from collections import Counter

import pytest

from logslice.line_counter import (
    CountResult,
    compute_count_result,
    count_by_level,
    count_by_minute,
    count_lines,
    format_count_result,
)


# ---------------------------------------------------------------------------
# count_lines
# ---------------------------------------------------------------------------

def test_count_lines_empty():
    assert count_lines([]) == 0


def test_count_lines_single():
    assert count_lines(["one line"]) == 1


def test_count_lines_multiple():
    assert count_lines(["a", "b", "c"]) == 3


# ---------------------------------------------------------------------------
# count_by_level
# ---------------------------------------------------------------------------

def test_count_by_level_known_levels():
    lines = [
        "2024-01-01T00:00:00 INFO  started",
        "2024-01-01T00:00:01 ERROR boom",
        "2024-01-01T00:00:02 INFO  ok",
    ]
    counts = count_by_level(lines)
    assert counts["INFO"] == 2
    assert counts["ERROR"] == 1


def test_count_by_level_unknown_fallback():
    lines = ["no level here", "also no level"]
    counts = count_by_level(lines)
    assert counts["UNKNOWN"] == 2


def test_count_by_level_empty():
    assert count_by_level([]) == Counter()


# ---------------------------------------------------------------------------
# count_by_minute
# ---------------------------------------------------------------------------

def test_count_by_minute_groups_correctly():
    lines = [
        "2024-06-01T10:01:05 INFO a",
        "2024-06-01T10:01:45 INFO b",
        "2024-06-01T10:02:10 INFO c",
    ]
    counts = count_by_minute(lines)
    assert counts["2024-06-01 10:01"] == 2
    assert counts["2024-06-01 10:02"] == 1


def test_count_by_minute_skips_unparseable():
    lines = ["no timestamp here", "2024-06-01T10:00:00 INFO ok"]
    counts = count_by_minute(lines)
    assert sum(counts.values()) == 1


# ---------------------------------------------------------------------------
# compute_count_result
# ---------------------------------------------------------------------------

def test_compute_count_result_totals():
    lines = [
        "2024-06-01T09:00:00 DEBUG x",
        "2024-06-01T09:00:30 INFO  y",
        "2024-06-01T09:01:00 ERROR z",
    ]
    result = compute_count_result(lines)
    assert result.total == 3
    assert result.by_level["DEBUG"] == 1
    assert result.by_level["INFO"] == 1
    assert result.by_level["ERROR"] == 1
    assert result.by_minute["2024-06-01 09:00"] == 2
    assert result.by_minute["2024-06-01 09:01"] == 1


def test_compute_count_result_empty():
    result = compute_count_result([])
    assert result.total == 0
    assert result.by_level == Counter()
    assert result.by_minute == Counter()


# ---------------------------------------------------------------------------
# format_count_result
# ---------------------------------------------------------------------------

def test_format_count_result_contains_total():
    result = CountResult(total=5)
    output = list(format_count_result(result))
    assert any("5" in line for line in output)


def test_format_count_result_lists_levels():
    result = CountResult(total=2, by_level=Counter({"INFO": 1, "ERROR": 1}))
    output = "\n".join(format_count_result(result))
    assert "INFO" in output
    assert "ERROR" in output
