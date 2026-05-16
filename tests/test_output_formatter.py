"""Tests for logslice.output_formatter."""

import pytest
from logslice.output_formatter import FormatOptions, format_lines, lines_to_string


SAMPLE_LINES = [
    "2024-01-01 INFO  server started\n",
    "2024-01-01 DEBUG request received\n",
    "2024-01-01 ERROR connection failed\n",
]


def _collect(lines, **kwargs):
    opts = FormatOptions(**kwargs) if kwargs else None
    return list(format_lines(lines, opts))


def test_plain_output_strips_newline():
    result = _collect(["hello\n"])
    assert result == ["hello"]


def test_plain_output_multiple_lines():
    result = _collect(SAMPLE_LINES)
    assert len(result) == 3
    assert result[0] == "2024-01-01 INFO  server started"


def test_line_numbers_prepended():
    result = _collect(SAMPLE_LINES, show_line_numbers=True)
    assert result[0].startswith("     1: ")
    assert result[2].startswith("     3: ")


def test_line_numbers_custom_start():
    opts = FormatOptions(show_line_numbers=True)
    result = list(format_lines(SAMPLE_LINES, opts, start_line=10))
    assert result[0].startswith("    10: ")
    assert result[1].startswith("    11: ")


def test_highlight_keyword_no_color():
    lines = ["ERROR connection failed\n"]
    result = _collect(lines, highlight_keyword="ERROR")
    assert "[ERROR]" in result[0]


def test_highlight_keyword_with_color():
    lines = ["ERROR something bad\n"]
    opts = FormatOptions(highlight_keyword="ERROR", color=True)
    result = list(format_lines(lines, opts))
    assert "\033[33m" in result[0]
    assert "\033[0m" in result[0]


def test_highlight_keyword_not_present():
    lines = ["INFO all good\n"]
    result = _collect(lines, highlight_keyword="ERROR")
    assert result[0] == "INFO all good"


def test_prefix_prepended():
    result = _collect(SAMPLE_LINES, prefix=">> ")
    assert all(r.startswith(">> ") for r in result)


def test_prefix_and_line_numbers_combined():
    opts = FormatOptions(show_line_numbers=True, prefix="LOG ")
    result = list(format_lines(["hello\n"], opts))
    assert result[0].startswith("LOG      1: ")


def test_lines_to_string_joins_with_newline():
    output = lines_to_string(["line1\n", "line2\n"])
    assert output == "line1\nline2"


def test_empty_input_yields_nothing():
    result = _collect([])
    assert result == []


def test_default_options_used_when_none_passed():
    result = list(format_lines(["test\n"], None))
    assert result == ["test"]
