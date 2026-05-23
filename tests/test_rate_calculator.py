"""Tests for logslice.rate_calculator."""
from datetime import datetime, timedelta

import pytest

from logslice.rate_calculator import RateStats, compute_rate, format_rate


def _line(dt: datetime, msg: str = "event") -> str:
    return f"{dt.isoformat()} {msg}"


def _dt(offset_seconds: float) -> datetime:
    base = datetime(2024, 1, 1, 12, 0, 0)
    return base + timedelta(seconds=offset_seconds)


# ---------------------------------------------------------------------------
# compute_rate
# ---------------------------------------------------------------------------

def test_empty_input_returns_zero_stats():
    stats = compute_rate([])
    assert stats.total_events == 0
    assert stats.span_seconds == 0.0
    assert stats.events_per_second == 0.0
    assert stats.earliest is None
    assert stats.latest is None


def test_single_line_no_span():
    stats = compute_rate([_line(_dt(0))])
    assert stats.total_events == 1
    assert stats.span_seconds == 0.0
    assert stats.events_per_second == 0.0


def test_two_events_one_second_apart():
    lines = [_line(_dt(0)), _line(_dt(1))]
    stats = compute_rate(lines)
    assert stats.total_events == 2
    assert stats.span_seconds == pytest.approx(1.0)
    assert stats.events_per_second == pytest.approx(2.0)


def test_events_per_minute_derived_from_per_second():
    lines = [_line(_dt(0)), _line(_dt(1))]
    stats = compute_rate(lines)
    assert stats.events_per_minute == pytest.approx(stats.events_per_second * 60)


def test_events_per_hour_derived_from_per_second():
    lines = [_line(_dt(0)), _line(_dt(1))]
    stats = compute_rate(lines)
    assert stats.events_per_hour == pytest.approx(stats.events_per_second * 3600)


def test_lines_without_timestamps_counted_but_not_timed():
    lines = [_line(_dt(0)), "no timestamp here", _line(_dt(10))]
    stats = compute_rate(lines)
    assert stats.total_events == 3
    assert stats.span_seconds == pytest.approx(10.0)
    # 3 events over 10 s
    assert stats.events_per_second == pytest.approx(0.3)


def test_only_lines_without_timestamps():
    lines = ["plain line", "another plain line"]
    stats = compute_rate(lines)
    assert stats.total_events == 2
    assert stats.span_seconds == 0.0
    assert stats.earliest is None


def test_earliest_and_latest_set_correctly():
    t0, t1 = _dt(0), _dt(5)
    lines = [_line(t1), _line(t0)]  # intentionally unordered
    stats = compute_rate(lines)
    assert stats.earliest == t0
    assert stats.latest == t1


def test_returns_rate_stats_instance():
    stats = compute_rate([_line(_dt(0))])
    assert isinstance(stats, RateStats)


# ---------------------------------------------------------------------------
# format_rate
# ---------------------------------------------------------------------------

def test_format_rate_contains_total_events():
    stats = compute_rate([_line(_dt(0)), _line(_dt(60))])
    output = format_rate(stats)
    assert "Total events" in output
    assert "2" in output


def test_format_rate_contains_span():
    stats = compute_rate([_line(_dt(0)), _line(_dt(60))])
    output = format_rate(stats)
    assert "Span" in output
    assert "60.0" in output


def test_format_rate_contains_earliest_and_latest():
    stats = compute_rate([_line(_dt(0)), _line(_dt(60))])
    output = format_rate(stats)
    assert "Earliest" in output
    assert "Latest" in output


def test_format_rate_no_timestamps_omits_earliest_latest():
    stats = compute_rate(["no ts", "also no ts"])
    output = format_rate(stats)
    assert "Earliest" not in output
    assert "Latest" not in output
