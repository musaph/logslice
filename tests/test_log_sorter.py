"""Tests for logslice.log_sorter."""

from __future__ import annotations

from typing import List

import pytest

from logslice.log_sorter import (
    SortedChunk,
    format_sort_summary,
    sort_into_chunk,
    sort_lines,
)


def _collect(iterable) -> List[str]:
    return list(iterable)


# ---------------------------------------------------------------------------
# sort_lines
# ---------------------------------------------------------------------------


def test_sort_empty_input_yields_nothing():
    assert _collect(sort_lines([])) == []


def test_sort_single_line_passes_through():
    line = "2024-01-01T00:00:00 hello"
    assert _collect(sort_lines([line])) == [line]


def test_sort_ascending_order():
    lines = [
        "2024-01-01T00:00:03 third",
        "2024-01-01T00:00:01 first",
        "2024-01-01T00:00:02 second",
    ]
    result = _collect(sort_lines(lines))
    assert "first" in result[0]
    assert "second" in result[1]
    assert "third" in result[2]


def test_sort_descending_order():
    lines = [
        "2024-01-01T00:00:01 first",
        "2024-01-01T00:00:03 third",
        "2024-01-01T00:00:02 second",
    ]
    result = _collect(sort_lines(lines, reverse=True))
    assert "third" in result[0]
    assert "second" in result[1]
    assert "first" in result[2]


def test_lines_without_timestamp_go_to_end():
    lines = [
        "2024-01-01T00:00:02 second",
        "no timestamp here",
        "2024-01-01T00:00:01 first",
    ]
    result = _collect(sort_lines(lines))
    assert result[-1] == "no timestamp here"


def test_multiple_no_timestamp_lines_all_at_end():
    lines = [
        "plain line A",
        "2024-01-01T00:00:01 ts",
        "plain line B",
    ]
    result = _collect(sort_lines(lines))
    assert result[0] == "2024-01-01T00:00:01 ts"
    assert set(result[1:]) == {"plain line A", "plain line B"}


# ---------------------------------------------------------------------------
# sort_into_chunk
# ---------------------------------------------------------------------------


def test_chunk_sorted_count():
    lines = [
        "2024-01-01T00:00:01 a",
        "no ts",
        "2024-01-01T00:00:02 b",
    ]
    chunk = sort_into_chunk(lines)
    assert chunk.sorted_count == 2
    assert chunk.unsorted_count == 1


def test_chunk_total_lines_preserved():
    lines = ["2024-01-01T00:00:0{} x".format(i) for i in range(5)]
    chunk = sort_into_chunk(lines)
    assert len(chunk.lines) == 5


def test_chunk_is_sorted_chunk_instance():
    chunk = sort_into_chunk(["2024-01-01T00:00:00 x"])
    assert isinstance(chunk, SortedChunk)


# ---------------------------------------------------------------------------
# format_sort_summary
# ---------------------------------------------------------------------------


def test_format_sort_summary_contains_counts():
    chunk = SortedChunk(lines=["a", "b", "c"], sorted_count=2, unsorted_count=1)
    summary = format_sort_summary(chunk)
    assert "3" in summary
    assert "2" in summary
    assert "1" in summary


def test_format_sort_summary_is_string():
    chunk = SortedChunk(lines=[], sorted_count=0, unsorted_count=0)
    assert isinstance(format_sort_summary(chunk), str)
