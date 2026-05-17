"""Tests for logslice.context_window."""
from __future__ import annotations

import pytest

from logslice.context_window import ContextMatch, extract_context, format_context_match


LINES = [
    "line one",
    "line two",
    "ERROR happened here",
    "line four",
    "line five",
    "ERROR again",
    "line seven",
]


def _pred(kw: str):
    return lambda line: kw.lower() in line.lower()


# ---------------------------------------------------------------------------
# extract_context basics
# ---------------------------------------------------------------------------

def test_no_matches_yields_nothing():
    result = list(extract_context(LINES, _pred("CRITICAL")))
    assert result == []


def test_returns_context_match_instances():
    result = list(extract_context(LINES, _pred("ERROR")))
    assert all(isinstance(m, ContextMatch) for m in result)


def test_correct_number_of_matches():
    result = list(extract_context(LINES, _pred("ERROR")))
    assert len(result) == 2


def test_match_line_number_is_one_based():
    result = list(extract_context(LINES, _pred("ERROR")))
    assert result[0].line_number == 3
    assert result[1].line_number == 6


def test_match_line_text():
    result = list(extract_context(LINES, _pred("ERROR")))
    assert result[0].line == "ERROR happened here"


def test_before_context_default():
    result = list(extract_context(LINES, _pred("ERROR")))
    before_texts = [t for _, t in result[0].before]
    assert "line one" in before_texts
    assert "line two" in before_texts


def test_after_context_default():
    result = list(extract_context(LINES, _pred("ERROR")))
    after_texts = [t for _, t in result[0].after]
    assert "line four" in after_texts
    assert "line five" in after_texts


def test_before_zero_gives_empty_before():
    result = list(extract_context(LINES, _pred("ERROR"), before=0))
    assert result[0].before == []


def test_after_zero_gives_empty_after():
    result = list(extract_context(LINES, _pred("ERROR"), after=0))
    assert result[0].after == []


def test_context_clipped_at_start_of_file():
    result = list(extract_context(["ERROR first", "second"], _pred("ERROR"), before=3))
    assert result[0].before == []


def test_context_clipped_at_end_of_file():
    result = list(extract_context(["first", "ERROR last"], _pred("ERROR"), after=3))
    assert result[0].after == []


def test_negative_before_raises():
    with pytest.raises(ValueError):
        list(extract_context(LINES, _pred("ERROR"), before=-1))


def test_negative_after_raises():
    with pytest.raises(ValueError):
        list(extract_context(LINES, _pred("ERROR"), after=-1))


def test_empty_input_yields_nothing():
    assert list(extract_context([], _pred("ERROR"))) == []


# ---------------------------------------------------------------------------
# format_context_match
# ---------------------------------------------------------------------------

def test_format_includes_match_line():
    result = list(extract_context(LINES, _pred("ERROR")))
    formatted = format_context_match(result[0])
    assert any("ERROR happened here" in l for l in formatted)


def test_format_line_numbers_present():
    result = list(extract_context(LINES, _pred("ERROR")))
    formatted = format_context_match(result[0])
    assert formatted[0].startswith("1:")


def test_format_separator_appended():
    result = list(extract_context(LINES, _pred("ERROR")))
    formatted = format_context_match(result[0], separator="---")
    assert formatted[-1] == "---"


def test_format_no_separator():
    result = list(extract_context(LINES, _pred("ERROR")))
    formatted = format_context_match(result[0], separator="")
    assert not any(l == "" for l in formatted)
