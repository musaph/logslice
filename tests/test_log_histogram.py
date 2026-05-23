"""Tests for logslice.log_histogram."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.log_histogram import (
    HistogramBucket,
    Histogram,
    compute_histogram,
    format_histogram,
)


def _iso(dt_str: str) -> str:
    """Return a log line containing an ISO-8601 timestamp."""
    return f"{dt_str} INFO some event"


# ---------------------------------------------------------------------------
# compute_histogram
# ---------------------------------------------------------------------------

def test_empty_input_returns_empty_histogram():
    hist = compute_histogram([])
    assert hist.buckets == []
    assert hist.total_lines == 0
    assert hist.unparsed_lines == 0


def test_unparsed_lines_counted():
    lines = ["no timestamp here", "also no timestamp"]
    hist = compute_histogram(lines)
    assert hist.total_lines == 2
    assert hist.unparsed_lines == 2
    assert hist.buckets == []


def test_single_line_single_bucket():
    hist = compute_histogram([_iso("2024-01-15 10:05:30")])
    assert len(hist.buckets) == 1
    assert hist.buckets[0].count == 1


def test_two_lines_same_minute_one_bucket():
    lines = [
        _iso("2024-01-15 10:05:01"),
        _iso("2024-01-15 10:05:59"),
    ]
    hist = compute_histogram(lines, interval="minute")
    assert len(hist.buckets) == 1
    assert hist.buckets[0].count == 2


def test_two_lines_different_minutes_two_buckets():
    lines = [
        _iso("2024-01-15 10:05:00"),
        _iso("2024-01-15 10:06:00"),
    ]
    hist = compute_histogram(lines, interval="minute")
    assert len(hist.buckets) == 2


def test_buckets_sorted_chronologically():
    lines = [
        _iso("2024-01-15 10:07:00"),
        _iso("2024-01-15 10:05:00"),
        _iso("2024-01-15 10:06:00"),
    ]
    hist = compute_histogram(lines, interval="minute")
    labels = [b.label for b in hist.buckets]
    assert labels == sorted(labels)


def test_interval_hour_groups_by_hour():
    lines = [
        _iso("2024-01-15 10:05:00"),
        _iso("2024-01-15 10:55:00"),
        _iso("2024-01-15 11:05:00"),
    ]
    hist = compute_histogram(lines, interval="hour")
    assert len(hist.buckets) == 2
    assert hist.buckets[0].count == 2
    assert hist.buckets[1].count == 1


def test_total_lines_includes_unparsed():
    lines = [_iso("2024-01-15 10:05:00"), "no ts"]
    hist = compute_histogram(lines)
    assert hist.total_lines == 2
    assert hist.unparsed_lines == 1


# ---------------------------------------------------------------------------
# format_histogram
# ---------------------------------------------------------------------------

def test_format_empty_histogram_yields_notice():
    hist = Histogram()
    output = list(format_histogram(hist))
    assert any("no timestamped" in line for line in output)


def test_format_contains_label_and_count():
    lines = [_iso("2024-01-15 10:05:00"), _iso("2024-01-15 10:05:30")]
    hist = compute_histogram(lines, interval="minute")
    output = list(format_histogram(hist))
    combined = "\n".join(output)
    assert "2024-01-15 10:05" in combined
    assert "2" in combined


def test_format_summary_lines_present():
    lines = [_iso("2024-01-15 10:05:00"), "no ts"]
    hist = compute_histogram(lines)
    output = "\n".join(format_histogram(hist))
    assert "total lines" in output
    assert "unparsed" in output
