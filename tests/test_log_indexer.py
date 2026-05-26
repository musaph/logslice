"""Tests for logslice.log_indexer."""
from __future__ import annotations

import pytest

from logslice.log_indexer import (
    IndexEntry,
    LogIndex,
    build_index,
    iter_index_report,
    lookup,
)


LINES = [
    "INFO  server started on port 8080",
    "DEBUG request received from 127.0.0.1",
    "ERROR failed to connect to database",
    "INFO  health check passed",
    "ERROR timeout waiting for response",
]


def test_build_index_returns_log_index():
    idx = build_index(LINES, ["ERROR"])
    assert isinstance(idx, LogIndex)


def test_single_keyword_correct_line_numbers():
    idx = build_index(LINES, ["ERROR"])
    assert lookup(idx, "ERROR") == [3, 5]


def test_multiple_keywords_tracked_independently():
    idx = build_index(LINES, ["INFO", "ERROR"])
    assert lookup(idx, "INFO") == [1, 4]
    assert lookup(idx, "ERROR") == [3, 5]


def test_case_insensitive_default():
    idx = build_index(LINES, ["error"])
    assert lookup(idx, "error") == [3, 5]


def test_case_sensitive_no_match_on_wrong_case():
    idx = build_index(LINES, ["error"], case_sensitive=True)
    assert lookup(idx, "error", case_sensitive=True) == []


def test_case_sensitive_matches_exact_case():
    idx = build_index(LINES, ["ERROR"], case_sensitive=True)
    assert lookup(idx, "ERROR", case_sensitive=True) == [3, 5]


def test_keyword_not_present_returns_empty():
    idx = build_index(LINES, ["CRITICAL"])
    assert lookup(idx, "CRITICAL") == []


def test_lookup_unknown_keyword_returns_empty():
    idx = build_index(LINES, ["INFO"])
    assert lookup(idx, "MISSING") == []


def test_empty_lines_yields_empty_index():
    idx = build_index([], ["ERROR"])
    assert idx.entries["ERROR"].hit_count == 0


def test_empty_keywords_yields_empty_index():
    idx = build_index(LINES, [])
    assert idx.total_keywords == 0


def test_total_keywords():
    idx = build_index(LINES, ["INFO", "ERROR", "DEBUG"])
    assert idx.total_keywords == 3


def test_total_hits():
    idx = build_index(LINES, ["INFO", "ERROR"])
    # INFO on lines 1,4  ERROR on lines 3,5 => 4 total
    assert idx.total_hits == 4


def test_hit_count_property():
    idx = build_index(LINES, ["ERROR"])
    assert idx.entries["ERROR"].hit_count == 2


def test_iter_index_report_yields_strings():
    idx = build_index(LINES, ["INFO", "ERROR"])
    report = list(iter_index_report(idx))
    assert len(report) == 2
    assert all(isinstance(r, str) for r in report)


def test_iter_index_report_contains_keyword():
    idx = build_index(LINES, ["ERROR"])
    report = list(iter_index_report(idx))
    assert "ERROR" in report[0]


def test_iter_index_report_truncates_long_lists():
    many_lines = ["error hit"] * 10
    idx = build_index(many_lines, ["error"])
    report = list(iter_index_report(idx))
    assert "..." in report[0]
