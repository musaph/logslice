"""Tests for logslice.log_slicer."""
from __future__ import annotations

import pytest

from logslice.log_slicer import (
    SliceResult,
    compute_slice_result,
    format_slice_result,
    slice_lines,
)


def _collect(source, start, end=None, *, step=1):
    return list(slice_lines(iter(source), start, end, step=step))


LINES = [f"line{i}" for i in range(10)]  # line0 … line9


def test_slice_from_zero_no_end_returns_all():
    assert _collect(LINES, 0) == LINES


def test_slice_start_trims_head():
    assert _collect(LINES, 3) == LINES[3:]


def test_slice_end_trims_tail():
    assert _collect(LINES, 0, 5) == LINES[:5]


def test_slice_start_and_end_window():
    assert _collect(LINES, 2, 6) == LINES[2:6]


def test_slice_step_2_every_other():
    result = _collect(LINES, 0, step=2)
    assert result == LINES[::2]


def test_slice_step_with_window():
    result = _collect(LINES, 2, 8, step=3)
    # indices 2,3,4,5,6,7 → keep match_count 0,1,2,3,4,5 → step=3 → 0,3
    assert result == [LINES[2], LINES[5]]


def test_slice_empty_source_yields_nothing():
    assert _collect([], 0) == []


def test_slice_start_beyond_length_yields_nothing():
    assert _collect(LINES, 20) == []


def test_slice_end_beyond_length_clamps_gracefully():
    assert _collect(LINES, 0, 999) == LINES


def test_negative_start_raises():
    with pytest.raises(ValueError, match="start"):
        _collect(LINES, -1)


def test_zero_step_raises():
    with pytest.raises(ValueError, match="step"):
        _collect(LINES, 0, step=0)


def test_end_not_greater_than_start_raises():
    with pytest.raises(ValueError, match="end"):
        _collect(LINES, 5, 5)


def test_compute_slice_result_returns_slice_result_instance():
    result = compute_slice_result(LINES, 1, 4)
    assert isinstance(result, SliceResult)


def test_compute_slice_result_correct_lines():
    result = compute_slice_result(LINES, 1, 4)
    assert result.lines == LINES[1:4]


def test_compute_slice_result_total_seen():
    result = compute_slice_result(LINES, 0, 3)
    assert result.total_seen == len(LINES)


def test_compute_slice_result_count_property():
    result = compute_slice_result(LINES, 0, 5)
    assert result.count == 5


def test_compute_slice_result_end_index_clamped():
    result = compute_slice_result(LINES, 0, 999)
    assert result.end_index == len(LINES)


def test_format_slice_result_contains_counts():
    result = compute_slice_result(LINES, 2, 5)
    summary = format_slice_result(result)
    assert "3" in summary
    assert str(len(LINES)) in summary
