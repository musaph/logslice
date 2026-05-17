"""Tests for logslice.highlighter."""
from __future__ import annotations

import pytest

from logslice.highlighter import (
    HighlightOptions,
    highlight_line,
    highlight_lines,
    line_matches,
)


def _opts(**kwargs) -> HighlightOptions:
    return HighlightOptions(**kwargs)


# ---------------------------------------------------------------------------
# line_matches
# ---------------------------------------------------------------------------

def test_line_matches_no_keywords_always_true():
    opts = _opts(keywords=[])
    assert line_matches("anything", opts) is True


def test_line_matches_found():
    opts = _opts(keywords=["ERROR"])
    assert line_matches("2024-01-01 ERROR something", opts) is True


def test_line_matches_not_found():
    opts = _opts(keywords=["ERROR"])
    assert line_matches("2024-01-01 INFO something", opts) is False


def test_line_matches_case_insensitive_default():
    opts = _opts(keywords=["error"])
    assert line_matches("ERROR occurred", opts) is True


def test_line_matches_case_sensitive():
    opts = _opts(keywords=["error"], case_sensitive=True)
    assert line_matches("ERROR occurred", opts) is False


# ---------------------------------------------------------------------------
# highlight_line
# ---------------------------------------------------------------------------

def test_highlight_line_wraps_keyword_with_ansi():
    opts = _opts(keywords=["ERROR"], ansi_color="\033[31m", ansi_reset="\033[0m")
    result = highlight_line("got ERROR here", opts)
    assert "\033[31mERROR\033[0m" in result


def test_highlight_line_no_keywords_unchanged():
    opts = _opts(keywords=[])
    line = "plain line"
    assert highlight_line(line, opts) == line


def test_highlight_line_use_ansi_false_unchanged():
    opts = _opts(keywords=["ERROR"], use_ansi=False)
    line = "got ERROR here"
    assert highlight_line(line, opts) == line


def test_highlight_line_multiple_occurrences():
    opts = _opts(keywords=["x"])
    result = highlight_line("x and x", opts)
    assert result.count(opts.ansi_color) == 2


# ---------------------------------------------------------------------------
# highlight_lines
# ---------------------------------------------------------------------------

def test_highlight_lines_yields_all_lines():
    opts = _opts(keywords=["ERR"])
    lines = ["INFO ok", "ERR bad", "DEBUG fine"]
    out = list(highlight_lines(lines, opts))
    assert len(out) == 3


def test_highlight_lines_non_matching_unchanged():
    opts = _opts(keywords=["ERR"])
    result = list(highlight_lines(["INFO ok"], opts))
    assert result[0] == "INFO ok"


def test_highlight_lines_no_ansi_adds_prefix():
    opts = _opts(keywords=["ERR"], use_ansi=False, mark_prefix=">>>")
    result = list(highlight_lines(["ERR bad"], opts))
    assert result[0].startswith(">>> ")


def test_highlight_lines_no_ansi_no_prefix_when_empty():
    opts = _opts(keywords=["ERR"], use_ansi=False, mark_prefix="")
    result = list(highlight_lines(["ERR bad"], opts))
    assert result[0] == "ERR bad"


def test_highlight_lines_empty_input():
    opts = _opts(keywords=["ERR"])
    assert list(highlight_lines([], opts)) == []
