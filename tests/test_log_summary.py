"""Tests for logslice.log_summary."""
import datetime
import pytest

from logslice.log_summary import summarise, format_summary, LogSummary


def _iso(ts: str) -> str:
    return f"{ts} INFO hello world"


LINES = [
    "2024-01-01T10:00:00 INFO  service started",
    "2024-01-01T10:00:05 DEBUG checking config",
    "2024-01-01T10:00:10 ERROR connection refused",
    "2024-01-01T10:00:15 WARN  retrying",
    "no timestamp here, just plain text",
]


def test_total_lines():
    s = summarise(LINES)
    assert s.total_lines == 5


def test_lines_with_timestamp():
    s = summarise(LINES)
    assert s.lines_with_timestamp == 4


def test_lines_with_level():
    s = summarise(LINES)
    assert s.lines_with_level == 4


def test_level_counts():
    s = summarise(LINES)
    assert s.level_counts["INFO"] == 1
    assert s.level_counts["DEBUG"] == 1
    assert s.level_counts["ERROR"] == 1
    assert s.level_counts["WARN"] == 1


def test_earliest_and_latest():
    s = summarise(LINES)
    assert s.earliest == datetime.datetime(2024, 1, 1, 10, 0, 0)
    assert s.latest == datetime.datetime(2024, 1, 1, 10, 0, 15)


def test_span_seconds():
    s = summarise(LINES)
    assert s.span_seconds == pytest.approx(15.0)


def test_lines_per_second():
    s = summarise(LINES)
    assert s.lines_per_second == pytest.approx(5 / 15, rel=1e-3)


def test_empty_input():
    s = summarise([])
    assert s.total_lines == 0
    assert s.earliest is None
    assert s.span_seconds is None
    assert s.lines_per_second is None


def test_single_line_no_span():
    s = summarise(["2024-01-01T12:00:00 INFO only"])
    assert s.span_seconds == pytest.approx(0.0)
    assert s.lines_per_second is None  # zero span → no rate


def test_format_summary_returns_strings():
    s = summarise(LINES)
    rows = format_summary(s)
    assert isinstance(rows, list)
    assert all(isinstance(r, str) for r in rows)


def test_format_summary_contains_total():
    s = summarise(LINES)
    rows = format_summary(s)
    joined = "\n".join(rows)
    assert "5" in joined
    assert "span" in joined


def test_format_summary_no_timestamps():
    s = summarise(["plain line", "another plain line"])
    rows = format_summary(s)
    joined = "\n".join(rows)
    assert "earliest" not in joined
    assert "span" not in joined
