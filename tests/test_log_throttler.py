"""Tests for logslice.log_throttler."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.log_throttler import (
    ThrottleOptions,
    ThrottleResult,
    _window_start,
    throttle_lines,
    compute_throttle_result,
    format_throttle_result,
)


def _iso(ts: str, msg: str) -> str:
    return f"{ts} {msg}"


def _collect(lines, opts=None) -> List[str]:
    return list(throttle_lines(lines, opts))


# ---------------------------------------------------------------------------
# _window_start
# ---------------------------------------------------------------------------

def test_window_start_floors_to_second():
    ts = datetime(2024, 1, 1, 12, 0, 0, 500_000, tzinfo=timezone.utc)
    ws = _window_start(ts, 1.0)
    assert ws.microsecond == 0


def test_window_start_groups_same_second():
    a = datetime(2024, 1, 1, 12, 0, 0, 100_000, tzinfo=timezone.utc)
    b = datetime(2024, 1, 1, 12, 0, 0, 900_000, tzinfo=timezone.utc)
    assert _window_start(a, 1.0) == _window_start(b, 1.0)


def test_window_start_separates_different_seconds():
    a = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    b = datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc)
    assert _window_start(a, 1.0) != _window_start(b, 1.0)


# ---------------------------------------------------------------------------
# throttle_lines
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _collect([]) == []


def test_lines_without_timestamp_always_pass():
    lines = ["no timestamp here", "another plain line"]
    assert _collect(lines) == lines


def test_lines_within_limit_all_pass():
    lines = [
        _iso("2024-01-01T00:00:00", "msg1"),
        _iso("2024-01-01T00:00:00", "msg2"),
    ]
    opts = ThrottleOptions(max_lines=5, window_seconds=1.0)
    assert len(_collect(lines, opts)) == 2


def test_lines_exceeding_limit_suppressed():
    lines = [_iso("2024-01-01T00:00:00", f"msg{i}") for i in range(10)]
    opts = ThrottleOptions(max_lines=3, window_seconds=1.0)
    result = _collect(lines, opts)
    assert len(result) == 3


def test_new_window_resets_counter():
    lines = [
        _iso("2024-01-01T00:00:00", "a"),
        _iso("2024-01-01T00:00:00", "b"),
        _iso("2024-01-01T00:00:01", "c"),  # new second
        _iso("2024-01-01T00:00:01", "d"),
    ]
    opts = ThrottleOptions(max_lines=1, window_seconds=1.0)
    result = _collect(lines, opts)
    assert len(result) == 2
    assert "a" in result[0]
    assert "c" in result[1]


def test_drop_message_emitted_when_set():
    lines = [_iso("2024-01-01T00:00:00", f"msg{i}") for i in range(5)]
    opts = ThrottleOptions(max_lines=2, window_seconds=1.0, drop_message="[throttled]")
    result = _collect(lines, opts)
    assert "[throttled]" in result
    assert result.count("[throttled]") == 3


def test_drop_message_none_silently_drops():
    lines = [_iso("2024-01-01T00:00:00", f"msg{i}") for i in range(5)]
    opts = ThrottleOptions(max_lines=2, window_seconds=1.0, drop_message=None)
    result = _collect(lines, opts)
    assert "[throttled]" not in str(result)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# format_throttle_result
# ---------------------------------------------------------------------------

def test_format_throttle_result_contains_fields():
    r = ThrottleResult(total=10, emitted=7, suppressed=3)
    out = format_throttle_result(r)
    assert "total=10" in out
    assert "emitted=7" in out
    assert "suppressed=3" in out
    assert "suppression_rate=" in out


def test_suppression_rate_zero_when_no_lines():
    r = ThrottleResult()
    assert r.suppression_rate == 0.0


def test_suppression_rate_calculated_correctly():
    r = ThrottleResult(total=4, emitted=1, suppressed=3)
    assert r.suppression_rate == pytest.approx(0.75)
