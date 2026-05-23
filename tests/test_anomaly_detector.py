"""Tests for logslice.anomaly_detector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.anomaly_detector import (
    AnomalyResult,
    detect_anomalies,
    format_anomaly,
)


def _ts(epoch: int) -> str:
    """Return an ISO-8601 timestamp string for the given epoch second."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _make_lines(epoch: int, count: int, msg: str = "event") -> List[str]:
    return [f"{_ts(epoch)} {msg}" for _ in range(count)]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _collect(lines, **kwargs) -> List[AnomalyResult]:
    return list(detect_anomalies(lines, **kwargs))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _collect([]) == []


def test_single_bucket_yields_nothing():
    lines = _make_lines(0, 5)
    assert _collect(lines, bucket_seconds=60) == []


def test_uniform_rate_yields_nothing():
    # All buckets have the same count → stddev == 0 → no anomalies
    lines = _make_lines(0, 3) + _make_lines(120, 3) + _make_lines(240, 3)
    assert _collect(lines, bucket_seconds=60) == []


def test_spike_bucket_detected():
    # Two quiet buckets (1 event each) + one spike (50 events)
    lines = (
        _make_lines(0, 1, "quiet")
        + _make_lines(120, 1, "quiet")
        + _make_lines(240, 50, "spike")
    )
    results = _collect(lines, bucket_seconds=60, z_threshold=1.5)
    assert len(results) > 0
    assert all("spike" in r.line for r in results)


def test_results_are_anomaly_result_instances():
    lines = (
        _make_lines(0, 1)
        + _make_lines(120, 1)
        + _make_lines(240, 40)
    )
    results = _collect(lines, bucket_seconds=60, z_threshold=1.0)
    for r in results:
        assert isinstance(r, AnomalyResult)


def test_z_score_positive_for_spike():
    lines = (
        _make_lines(0, 1)
        + _make_lines(120, 1)
        + _make_lines(240, 40)
    )
    results = _collect(lines, bucket_seconds=60, z_threshold=1.0)
    assert all(r.z_score > 0 for r in results)


def test_line_numbers_are_one_based():
    lines = _make_lines(0, 1) + _make_lines(120, 1) + _make_lines(240, 30)
    results = _collect(lines, bucket_seconds=60, z_threshold=1.0)
    assert all(r.line_number >= 1 for r in results)


def test_lines_without_timestamps_are_skipped():
    lines = ["no timestamp here"] * 10
    assert _collect(lines) == []


def test_high_threshold_suppresses_anomalies():
    lines = (
        _make_lines(0, 1)
        + _make_lines(120, 1)
        + _make_lines(240, 10)
    )
    results = _collect(lines, bucket_seconds=60, z_threshold=99.0)
    assert results == []


def test_format_anomaly_contains_key_fields():
    lines = (
        _make_lines(0, 1)
        + _make_lines(120, 1)
        + _make_lines(240, 40)
    )
    results = _collect(lines, bucket_seconds=60, z_threshold=1.0)
    assert results, "expected at least one anomaly for format test"
    text = format_anomaly(results[0])
    assert "[ANOMALY]" in text
    assert "z=" in text
    assert "bucket=" in text
    assert "mean=" in text
