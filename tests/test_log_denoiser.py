"""Tests for logslice.log_denoiser."""
from __future__ import annotations

from logslice.log_denoiser import (
    DenoiseResult,
    _normalise,
    compute_denoise_result,
    denoise,
    format_denoise_result,
)


def _collect(it):
    return list(it)


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------

def test_normalise_replaces_integers():
    assert _normalise("retried 3 times") == "retried <V> times"


def test_normalise_replaces_ip():
    assert _normalise("connected from 192.168.1.1") == "connected from <V>.<V>.<V>.<V>"


def test_normalise_replaces_uuid():
    line = "request id=550e8400-e29b-41d4-a716-446655440000 ok"
    result = _normalise(line)
    assert "<V>" in result
    assert "550e8400" not in result


def test_normalise_same_pattern_for_different_numbers():
    assert _normalise("error code 42") == _normalise("error code 99")


# ---------------------------------------------------------------------------
# denoise – basic filtering
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _collect(denoise([], threshold=3)) == []


def test_unique_lines_all_kept():
    lines = ["alpha", "beta", "gamma"]
    assert _collect(denoise(lines, threshold=2)) == lines


def test_lines_below_threshold_kept():
    lines = ["error 1", "error 2", "error 3"]
    result = _collect(denoise(lines, threshold=3))
    assert len(result) == 3


def test_lines_above_threshold_suppressed():
    lines = ["error 1"] * 10
    result = _collect(denoise(lines, threshold=3))
    assert len(result) == 3


def test_threshold_one_keeps_first_occurrence_only():
    lines = ["ping", "ping", "ping"]
    result = _collect(denoise(lines, threshold=1))
    assert result == ["ping"]


def test_different_patterns_tracked_independently():
    lines = ["error 1", "warn 1", "error 2", "warn 2", "error 3", "warn 3", "error 4"]
    result = _collect(denoise(lines, threshold=3))
    # error pattern: 4 occurrences → keep first 3; warn: 3 → keep all 3
    assert len(result) == 6


# ---------------------------------------------------------------------------
# denoise – summarise flag
# ---------------------------------------------------------------------------

def test_summarise_false_no_summary_lines():
    lines = ["x"] * 10
    result = _collect(denoise(lines, threshold=2, summarise=False))
    assert not any("[denoiser]" in r for r in result)


def test_summarise_true_emits_summary_after_stream():
    lines = ["x"] * 10
    result = _collect(denoise(lines, threshold=2, summarise=True))
    summary = [r for r in result if "[denoiser]" in r]
    assert len(summary) == 1
    assert "suppressed" in summary[0]


def test_summarise_reports_correct_suppressed_count():
    lines = ["x"] * 7
    result = _collect(denoise(lines, threshold=3, summarise=True))
    summary = [r for r in result if "[denoiser]" in r][0]
    assert "4" in summary  # 7 - 3 = 4 suppressed


# ---------------------------------------------------------------------------
# compute_denoise_result
# ---------------------------------------------------------------------------

def test_compute_result_total_lines():
    lines = ["a", "b", "c"]
    _, r = compute_denoise_result(lines, threshold=5)
    assert r.total_lines == 3


def test_compute_result_kept_lines():
    lines = ["x"] * 8
    _, r = compute_denoise_result(lines, threshold=3)
    assert r.kept_lines == 3


def test_compute_result_suppressed_lines():
    lines = ["x"] * 8
    _, r = compute_denoise_result(lines, threshold=3)
    assert r.suppressed_lines == 5


def test_compute_result_unique_patterns():
    lines = ["error 1", "warn 2", "error 3"]
    _, r = compute_denoise_result(lines, threshold=5)
    # both normalise to different patterns
    assert r.unique_patterns == 2


def test_suppression_rate_zero_when_nothing_suppressed():
    lines = ["a", "b", "c"]
    _, r = compute_denoise_result(lines, threshold=5)
    assert r.suppression_rate == 0.0


def test_suppression_rate_nonzero():
    lines = ["x"] * 10
    _, r = compute_denoise_result(lines, threshold=5)
    assert r.suppression_rate == 0.5


def test_suppression_rate_zero_when_no_lines():
    _, r = compute_denoise_result([], threshold=3)
    assert r.suppression_rate == 0.0


# ---------------------------------------------------------------------------
# format_denoise_result
# ---------------------------------------------------------------------------

def test_format_contains_all_fields():
    r = DenoiseResult(total_lines=100, kept_lines=80, suppressed_lines=20, unique_patterns=15)
    s = format_denoise_result(r)
    assert "total=100" in s
    assert "kept=80" in s
    assert "suppressed=20" in s
    assert "patterns=15" in s
    assert "suppression_rate=20.0%" in s
