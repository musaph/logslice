"""Tests for logslice.log_splitter."""
from __future__ import annotations

import pytest

from logslice.log_splitter import (
    LogSegment,
    format_segment_summary,
    split_by_delimiter,
    split_by_line_count,
)


def _collect(it):
    return list(it)


# ---------------------------------------------------------------------------
# split_by_delimiter
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _collect(split_by_delimiter([], r"---")) == []


def test_no_match_yields_single_segment():
    lines = ["hello", "world"]
    segs = _collect(split_by_delimiter(lines, r"---"))
    assert len(segs) == 1
    assert segs[0].lines == ["hello", "world"]


def test_delimiter_starts_new_segment():
    lines = ["a", "--- break ---", "b", "c"]
    segs = _collect(split_by_delimiter(lines, r"---"))
    assert len(segs) == 2
    assert segs[0].lines == ["a"]
    assert segs[1].lines == ["--- break ---", "b", "c"]


def test_include_delimiter_false_omits_delimiter_line():
    lines = ["a", "=== SECTION ===", "b"]
    segs = _collect(split_by_delimiter(lines, r"===", include_delimiter=False))
    assert segs[0].lines == ["a"]
    assert segs[1].lines == ["b"]


def test_segment_names_are_sequential():
    lines = ["x", "--- s1", "y", "--- s2", "z"]
    segs = _collect(split_by_delimiter(lines, r"---"))
    assert [s.name for s in segs] == ["segment-0", "segment-1", "segment-2"]


def test_custom_default_name():
    lines = ["a", "BREAK", "b"]
    segs = _collect(split_by_delimiter(lines, r"BREAK", default_name="part"))
    assert segs[0].name == "part-0"
    assert segs[1].name == "part-1"


def test_case_insensitive_match_by_default():
    lines = ["a", "break", "b"]
    segs = _collect(split_by_delimiter(lines, r"BREAK"))
    assert len(segs) == 2


def test_case_sensitive_no_match():
    lines = ["a", "break", "b"]
    segs = _collect(split_by_delimiter(lines, r"BREAK", case_sensitive=True))
    assert len(segs) == 1


def test_consecutive_delimiters():
    lines = ["---", "---", "data"]
    segs = _collect(split_by_delimiter(lines, r"---"))
    # first delimiter starts segment-0 (empty before it), second starts segment-1
    assert len(segs) == 2
    assert segs[-1].lines[-1] == "data"


# ---------------------------------------------------------------------------
# split_by_line_count
# ---------------------------------------------------------------------------

def test_split_by_line_count_empty_yields_nothing():
    assert _collect(split_by_line_count([], 5)) == []


def test_split_by_line_count_exact_multiple():
    lines = ["a", "b", "c", "d"]
    segs = _collect(split_by_line_count(lines, 2))
    assert len(segs) == 2
    assert segs[0].lines == ["a", "b"]
    assert segs[1].lines == ["c", "d"]


def test_split_by_line_count_remainder():
    lines = ["a", "b", "c"]
    segs = _collect(split_by_line_count(lines, 2))
    assert len(segs) == 2
    assert segs[1].lines == ["c"]


def test_split_by_line_count_chunk_larger_than_input():
    lines = ["a", "b"]
    segs = _collect(split_by_line_count(lines, 10))
    assert len(segs) == 1
    assert segs[0].lines == ["a", "b"]


def test_split_by_line_count_invalid_chunk_raises():
    with pytest.raises(ValueError):
        _collect(split_by_line_count(["a"], 0))


# ---------------------------------------------------------------------------
# LogSegment helpers
# ---------------------------------------------------------------------------

def test_line_count_property():
    seg = LogSegment(name="s", lines=["a", "b", "c"])
    assert seg.line_count == 3


# ---------------------------------------------------------------------------
# format_segment_summary
# ---------------------------------------------------------------------------

def test_format_summary_no_segments():
    assert format_segment_summary([]) == "No segments."


def test_format_summary_contains_segment_names():
    segs = [LogSegment("seg-0", ["a", "b"]), LogSegment("seg-1", ["c"])]
    out = format_segment_summary(segs)
    assert "seg-0" in out
    assert "seg-1" in out


def test_format_summary_total_line_count():
    segs = [LogSegment("s0", ["a", "b"]), LogSegment("s1", ["c", "d", "e"])]
    out = format_segment_summary(segs)
    assert "5" in out
