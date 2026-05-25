"""Tests for logslice.log_formatter."""
from __future__ import annotations

import json
import pytest

from logslice.log_formatter import (
    FormatResult,
    compute_format_result,
    reformat_line,
    reformat_lines,
)


# ---------------------------------------------------------------------------
# reformat_line — JSON input
# ---------------------------------------------------------------------------

def test_json_to_logfmt():
    line = '{"level":"info","msg":"started"}'
    result = reformat_line(line, "logfmt")
    assert "level=info" in result
    assert "msg=started" in result


def test_json_to_plain():
    line = '{"level":"error","msg":"boom"}'
    result = reformat_line(line, "plain")
    assert "error" in result
    assert "boom" in result


def test_json_to_json_round_trips():
    data = {"level": "debug", "msg": "ok"}
    line = json.dumps(data)
    result = reformat_line(line, "json")
    assert json.loads(result) == data


# ---------------------------------------------------------------------------
# reformat_line — logfmt input
# ---------------------------------------------------------------------------

def test_logfmt_to_json():
    line = "level=warn msg=timeout"
    result = reformat_line(line, "json")
    parsed = json.loads(result)
    assert parsed["level"] == "warn"
    assert parsed["msg"] == "timeout"


def test_logfmt_to_plain():
    line = "level=info msg=ready"
    result = reformat_line(line, "plain")
    assert "info" in result
    assert "ready" in result


def test_logfmt_quoted_value_preserved():
    line = 'level=info msg="hello world"'
    result = reformat_line(line, "json")
    parsed = json.loads(result)
    assert parsed["msg"] == "hello world"


# ---------------------------------------------------------------------------
# reformat_line — plain / unparseable input
# ---------------------------------------------------------------------------

def test_plain_line_returned_unchanged_for_json():
    line = "this is a plain log line"
    assert reformat_line(line, "json") == line


def test_plain_line_returned_unchanged_for_logfmt():
    line = "no key-value pairs here"
    assert reformat_line(line, "logfmt") == line


def test_trailing_newline_stripped_for_plain_line():
    line = "plain text\n"
    assert reformat_line(line, "json") == "plain text"


# ---------------------------------------------------------------------------
# reformat_lines
# ---------------------------------------------------------------------------

def test_reformat_lines_yields_all():
    lines = ['{"a":"1"}', '{"b":"2"}']
    results = list(reformat_lines(lines, "logfmt"))
    assert len(results) == 2


def test_reformat_lines_mixed_input():
    lines = ['{"level":"info"}', "plain text"]
    results = list(reformat_lines(lines, "logfmt"))
    assert "level=info" in results[0]
    assert results[1] == "plain text"


# ---------------------------------------------------------------------------
# compute_format_result
# ---------------------------------------------------------------------------

def test_compute_result_total():
    lines = ['{"a":"1"}', "plain", "level=x msg=y"]
    r = compute_format_result(lines, "json")
    assert r.total == 3


def test_compute_result_converted_count():
    lines = ['{"a":"1"}', "plain", "level=x msg=y"]
    r = compute_format_result(lines, "json")
    assert r.converted == 2
    assert r.unchanged == 1


def test_compute_result_conversion_rate():
    lines = ['{"a":"1"}', '{"b":"2"}']
    r = compute_format_result(lines, "logfmt")
    assert r.conversion_rate == pytest.approx(1.0)


def test_compute_result_empty_input():
    r = compute_format_result([], "json")
    assert r.total == 0
    assert r.conversion_rate == 0.0


def test_format_result_is_frozen():
    r = FormatResult(total=5, converted=3, unchanged=2)
    with pytest.raises(Exception):
        r.total = 99  # type: ignore[misc]
