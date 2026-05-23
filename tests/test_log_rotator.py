"""Tests for logslice.log_rotator."""

from __future__ import annotations

import pytest

from logslice.log_rotator import (
    LogChunk,
    format_chunk_summary,
    split_by_bytes,
    split_by_lines,
)


def _collect(it):
    return list(it)


# ---------------------------------------------------------------------------
# split_by_lines
# ---------------------------------------------------------------------------

def test_split_by_lines_empty_input_yields_nothing():
    assert _collect(split_by_lines([], chunk_size=5)) == []


def test_split_by_lines_exact_multiple():
    lines = ["a", "b", "c", "d"]
    chunks = _collect(split_by_lines(lines, chunk_size=2))
    assert len(chunks) == 2
    assert chunks[0].lines == ["a", "b"]
    assert chunks[1].lines == ["c", "d"]


def test_split_by_lines_remainder_in_final_chunk():
    lines = ["a", "b", "c"]
    chunks = _collect(split_by_lines(lines, chunk_size=2))
    assert len(chunks) == 2
    assert chunks[-1].lines == ["c"]


def test_split_by_lines_chunk_size_larger_than_input():
    lines = ["x", "y"]
    chunks = _collect(split_by_lines(lines, chunk_size=100))
    assert len(chunks) == 1
    assert chunks[0].lines == ["x", "y"]


def test_split_by_lines_chunk_size_one():
    lines = ["a", "b", "c"]
    chunks = _collect(split_by_lines(lines, chunk_size=1))
    assert len(chunks) == 3
    assert all(c.line_count == 1 for c in chunks)


def test_split_by_lines_indices_are_sequential():
    chunks = _collect(split_by_lines(list("abcdef"), chunk_size=2))
    assert [c.index for c in chunks] == [0, 1, 2]


def test_split_by_lines_invalid_chunk_size_raises():
    with pytest.raises(ValueError):
        _collect(split_by_lines(["a"], chunk_size=0))


# ---------------------------------------------------------------------------
# split_by_bytes
# ---------------------------------------------------------------------------

def test_split_by_bytes_empty_input_yields_nothing():
    assert _collect(split_by_bytes([], max_bytes=64)) == []


def test_split_by_bytes_single_chunk_when_small_enough():
    lines = ["hello", "world"]
    chunks = _collect(split_by_bytes(lines, max_bytes=1024))
    assert len(chunks) == 1
    assert chunks[0].lines == lines


def test_split_by_bytes_splits_when_limit_exceeded():
    # Each line is 5 bytes; limit is 8 → max 1 line per chunk after first
    lines = ["aaaaa", "bbbbb", "ccccc"]
    chunks = _collect(split_by_bytes(lines, max_bytes=8))
    assert len(chunks) == 3


def test_split_by_bytes_oversized_line_gets_own_chunk():
    big = "x" * 200
    lines = ["small", big, "small2"]
    chunks = _collect(split_by_bytes(lines, max_bytes=10))
    # 'small' fits; big oversized → own chunk; 'small2' fits in new chunk
    assert any(big in c.lines for c in chunks)
    oversized = [c for c in chunks if big in c.lines]
    assert len(oversized) == 1


def test_split_by_bytes_byte_size_property():
    lines = ["ab", "cd"]  # 2 + 2 = 4 bytes
    chunks = _collect(split_by_bytes(lines, max_bytes=1024))
    assert chunks[0].byte_size == 4


def test_split_by_bytes_invalid_max_bytes_raises():
    with pytest.raises(ValueError):
        _collect(split_by_bytes(["a"], max_bytes=0))


# ---------------------------------------------------------------------------
# format_chunk_summary
# ---------------------------------------------------------------------------

def test_format_chunk_summary_contains_index_and_counts():
    chunk = LogChunk(index=3, lines=["hello", "world"])
    summary = format_chunk_summary(chunk)
    assert "3" in summary
    assert "2" in summary  # line count
    assert "bytes" in summary
