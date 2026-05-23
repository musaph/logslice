"""Tests for logslice.level_filter."""

from __future__ import annotations

import pytest

from logslice.level_filter import (
    count_by_level,
    detect_level,
    filter_by_level,
)


LINES = [
    "2024-01-01 DEBUG starting up",
    "2024-01-01 INFO  server ready",
    "2024-01-01 WARNING disk usage high",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 CRITICAL out of memory",
    "2024-01-01 no level here",
]


# ---------------------------------------------------------------------------
# detect_level
# ---------------------------------------------------------------------------

def test_detect_level_debug():
    assert detect_level("DEBUG something") == "DEBUG"


def test_detect_level_warn_normalised():
    assert detect_level("WARN something") == "WARNING"


def test_detect_level_fatal_normalised():
    assert detect_level("FATAL crash") == "CRITICAL"


def test_detect_level_case_insensitive():
    assert detect_level("error: file not found") == "ERROR"


def test_detect_level_none_when_absent():
    assert detect_level("nothing to see here") is None


def test_detect_level_returns_first_match():
    # Only the first match is returned
    result = detect_level("DEBUG INFO both present")
    assert result == "DEBUG"


# ---------------------------------------------------------------------------
# filter_by_level — min_level
# ---------------------------------------------------------------------------

def test_min_level_warning_excludes_debug_and_info():
    result = list(filter_by_level(LINES, min_level="WARNING"))
    levels = [detect_level(l) for l in result]
    assert "DEBUG" not in levels
    assert "INFO" not in levels
    assert "WARNING" in levels
    assert "ERROR" in levels
    assert "CRITICAL" in levels


def test_min_level_debug_yields_all_levelled_lines():
    result = list(filter_by_level(LINES, min_level="DEBUG"))
    assert len(result) == 5  # excludes the no-level line


def test_lines_without_level_are_always_excluded():
    result = list(filter_by_level(LINES))
    for line in result:
        assert detect_level(line) is not None


# ---------------------------------------------------------------------------
# filter_by_level — max_level
# ---------------------------------------------------------------------------

def test_max_level_info_excludes_warning_and_above():
    result = list(filter_by_level(LINES, max_level="INFO"))
    levels = [detect_level(l) for l in result]
    assert "WARNING" not in levels
    assert "ERROR" not in levels
    assert "DEBUG" in levels
    assert "INFO" in levels


# ---------------------------------------------------------------------------
# filter_by_level — exact_level
# ---------------------------------------------------------------------------

def test_exact_level_only_yields_matching_lines():
    result = list(filter_by_level(LINES, exact_level="ERROR"))
    assert len(result) == 1
    assert "connection refused" in result[0]


def test_exact_level_warn_alias_matches_warning_lines():
    result = list(filter_by_level(LINES, exact_level="WARN"))
    assert len(result) == 1
    assert "disk usage high" in result[0]


# ---------------------------------------------------------------------------
# count_by_level
# ---------------------------------------------------------------------------

def test_count_by_level_returns_correct_counts():
    counts = count_by_level(LINES)
    assert counts["DEBUG"] == 1
    assert counts["INFO"] == 1
    assert counts["WARNING"] == 1
    assert counts["ERROR"] == 1
    assert counts["CRITICAL"] == 1
    assert "WARNING" in counts  # WARN normalised


def test_count_by_level_empty_input():
    assert count_by_level([]) == {}


def test_count_by_level_ignores_no_level_lines():
    counts = count_by_level(["no level here", "also nothing"])
    assert counts == {}
