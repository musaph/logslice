"""Tests for logslice.stats module."""

from datetime import datetime

import pytest

from logslice.stats import LogStats, compute_stats, format_stats


SAMPLE_LINES = [
    "2024-01-01T10:00:00 INFO  server started",
    "2024-01-01T10:01:30 DEBUG received request",
    "2024-01-01T10:02:00 ERROR connection refused",
    "no timestamp here just plain text",
    "2024-01-01T10:05:00 INFO  server stopped",
]


def test_total_lines():
    stats = compute_stats(SAMPLE_LINES)
    assert stats.total_lines == 5


def test_lines_with_timestamp():
    stats = compute_stats(SAMPLE_LINES)
    assert stats.lines_with_timestamp == 4


def test_timestamp_coverage():
    stats = compute_stats(SAMPLE_LINES)
    assert abs(stats.timestamp_coverage - 0.8) < 1e-9


def test_earliest_and_latest():
    stats = compute_stats(SAMPLE_LINES)
    assert stats.earliest == datetime(2024, 1, 1, 10, 0, 0)
    assert stats.latest == datetime(2024, 1, 1, 10, 5, 0)


def test_span_seconds():
    stats = compute_stats(SAMPLE_LINES)
    assert stats.span_seconds == 300.0


def test_span_seconds_none_when_no_timestamps():
    stats = compute_stats(["no ts", "also no ts"])
    assert stats.span_seconds is None


def test_empty_input():
    stats = compute_stats([])
    assert stats.total_lines == 0
    assert stats.lines_with_timestamp == 0
    assert stats.timestamp_coverage == 0.0
    assert stats.earliest is None
    assert stats.latest is None
    assert stats.span_seconds is None


def test_keyword_matches_case_insensitive():
    stats = compute_stats(SAMPLE_LINES, keywords=["error", "INFO"])
    # ERROR line + two INFO lines = 3
    assert stats.keyword_matches == 3
    assert stats.keywords == ["error", "INFO"]


def test_no_keywords_gives_zero_matches():
    stats = compute_stats(SAMPLE_LINES)
    assert stats.keyword_matches == 0
    assert stats.keywords == []


def test_format_stats_contains_key_fields():
    stats = compute_stats(SAMPLE_LINES, keywords=["error"])
    output = format_stats(stats)
    assert "Total lines" in output
    assert "5" in output
    assert "80.0%" in output
    assert "error" in output
    assert "300" in output


def test_format_stats_no_keywords_omits_keyword_line():
    stats = compute_stats(SAMPLE_LINES)
    output = format_stats(stats)
    assert "Keyword" not in output


def test_logstats_defaults():
    s = LogStats()
    assert s.total_lines == 0
    assert s.keywords == []
    assert s.timestamp_coverage == 0.0
