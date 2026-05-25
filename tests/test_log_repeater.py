"""Tests for logslice.log_repeater."""
from __future__ import annotations

import pytest

from logslice.log_repeater import (
    RepeatGroup,
    RepeatResult,
    collapse_repeats,
    compute_repeat_result,
    detect_repeats,
    format_repeat_summary,
    suppression_rate,
)


def _collect(it):
    return list(it)


# ---------------------------------------------------------------------------
# detect_repeats
# ---------------------------------------------------------------------------

def test_detect_repeats_empty_input_yields_nothing():
    assert _collect(detect_repeats([])) == []


def test_detect_repeats_no_run_yields_nothing():
    lines = ["a", "b", "c"]
    assert _collect(detect_repeats(lines)) == []


def test_detect_repeats_single_run():
    lines = ["x", "x", "x", "y"]
    groups = _collect(detect_repeats(lines))
    assert len(groups) == 1
    assert groups[0].line == "x"
    assert groups[0].count == 3
    assert groups[0].first_lineno == 1


def test_detect_repeats_run_at_end():
    lines = ["a", "b", "b", "b"]
    groups = _collect(detect_repeats(lines))
    assert len(groups) == 1
    assert groups[0].count == 3
    assert groups[0].first_lineno == 2


def test_detect_repeats_two_separate_runs():
    lines = ["a", "a", "b", "c", "c"]
    groups = _collect(detect_repeats(lines))
    assert len(groups) == 2
    assert groups[0].line == "a"
    assert groups[1].line == "c"


def test_detect_repeats_min_repeat_three():
    lines = ["a", "a", "b", "b", "b"]
    groups = _collect(detect_repeats(lines, min_repeat=3))
    assert len(groups) == 1
    assert groups[0].line == "b"


def test_detect_repeats_strips_trailing_newline():
    lines = ["hello\n", "hello\n", "hello\n"]
    groups = _collect(detect_repeats(lines))
    assert groups[0].line == "hello"


# ---------------------------------------------------------------------------
# collapse_repeats
# ---------------------------------------------------------------------------

def test_collapse_repeats_unique_lines_unchanged():
    lines = ["a", "b", "c"]
    assert _collect(collapse_repeats(lines)) == ["a", "b", "c"]


def test_collapse_repeats_inserts_marker():
    lines = ["err", "err", "err", "ok"]
    result = _collect(collapse_repeats(lines))
    assert result == ["err", "[repeated 3 times]", "ok"]


def test_collapse_repeats_custom_marker():
    lines = ["x", "x"]
    result = _collect(collapse_repeats(lines, marker="(x{n})"))
    assert "(x2)" in result


def test_collapse_repeats_run_below_min_not_collapsed():
    lines = ["a", "a", "b"]  # run of 2, min_repeat=3
    result = _collect(collapse_repeats(lines, min_repeat=3))
    assert result == ["a", "b"]  # no marker, but still deduplicated to first


# ---------------------------------------------------------------------------
# compute_repeat_result
# ---------------------------------------------------------------------------

def test_compute_repeat_result_total_lines():
    lines = ["a", "b", "b", "c"]
    r = compute_repeat_result(lines)
    assert r.total_lines == 4


def test_compute_repeat_result_suppressed_count():
    lines = ["x", "x", "x"]  # run of 3 → 2 suppressed
    r = compute_repeat_result(lines)
    assert r.suppressed_lines == 2


def test_compute_repeat_result_no_repeats_zero_suppressed():
    lines = ["a", "b", "c"]
    r = compute_repeat_result(lines)
    assert r.suppressed_lines == 0
    assert r.groups == []


# ---------------------------------------------------------------------------
# suppression_rate
# ---------------------------------------------------------------------------

def test_suppression_rate_zero_when_no_lines():
    assert suppression_rate(RepeatResult()) == 0.0


def test_suppression_rate_correct_fraction():
    r = RepeatResult(total_lines=10, suppressed_lines=4)
    assert suppression_rate(r) == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# format_repeat_summary
# ---------------------------------------------------------------------------

def test_format_repeat_summary_contains_total_lines():
    r = compute_repeat_result(["a", "a", "b"])
    summary = format_repeat_summary(r)
    assert "total lines" in summary
    assert "3" in summary


def test_format_repeat_summary_lists_group_info():
    r = compute_repeat_result(["err", "err", "err"])
    summary = format_repeat_summary(r)
    assert "3x" in summary
    assert "err" in summary
