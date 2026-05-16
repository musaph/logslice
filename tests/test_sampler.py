"""Tests for logslice.sampler."""

from __future__ import annotations

import pytest

from logslice.sampler import sample_every_nth, sample_head, sample_tail


LINES = [f"line {i}" for i in range(1, 11)]  # 10 lines


# ---------------------------------------------------------------------------
# sample_every_nth
# ---------------------------------------------------------------------------

def test_nth_n1_yields_all_lines():
    assert list(sample_every_nth(LINES, 1)) == LINES


def test_nth_n2_yields_every_second_line():
    result = list(sample_every_nth(LINES, 2))
    assert result == ["line 1", "line 3", "line 5", "line 7", "line 9"]


def test_nth_n10_yields_first_line_only():
    result = list(sample_every_nth(LINES, 10))
    assert result == ["line 1"]


def test_nth_larger_than_length_yields_first_line():
    result = list(sample_every_nth(LINES, 100))
    assert result == ["line 1"]


def test_nth_empty_input_yields_nothing():
    assert list(sample_every_nth([], 3)) == []


def test_nth_raises_on_zero():
    with pytest.raises(ValueError):
        list(sample_every_nth(LINES, 0))


def test_nth_raises_on_negative():
    with pytest.raises(ValueError):
        list(sample_every_nth(LINES, -1))


# ---------------------------------------------------------------------------
# sample_head
# ---------------------------------------------------------------------------

def test_head_returns_first_n_lines():
    assert list(sample_head(LINES, 3)) == ["line 1", "line 2", "line 3"]


def test_head_zero_yields_nothing():
    assert list(sample_head(LINES, 0)) == []


def test_head_larger_than_length_yields_all():
    assert list(sample_head(LINES, 100)) == LINES


def test_head_raises_on_negative():
    with pytest.raises(ValueError):
        list(sample_head(LINES, -1))


def test_head_empty_input():
    assert list(sample_head([], 5)) == []


# ---------------------------------------------------------------------------
# sample_tail
# ---------------------------------------------------------------------------

def test_tail_returns_last_n_lines():
    assert sample_tail(LINES, 3) == ["line 8", "line 9", "line 10"]


def test_tail_zero_returns_empty_list():
    assert sample_tail(LINES, 0) == []


def test_tail_larger_than_length_returns_all():
    assert sample_tail(LINES, 100) == LINES


def test_tail_raises_on_negative():
    with pytest.raises(ValueError):
        sample_tail(LINES, -1)


def test_tail_empty_input():
    assert sample_tail([], 5) == []


def test_tail_returns_list_not_iterator():
    result = sample_tail(LINES, 2)
    assert isinstance(result, list)
