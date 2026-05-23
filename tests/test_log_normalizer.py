"""Tests for logslice.log_normalizer."""
import json
import pytest

from logslice.log_normalizer import (
    NormalizeOptions,
    normalize_line,
    normalize_lines,
    _to_logfmt,
)


def _collect(lines):
    return list(normalize_lines(lines))


# ---------------------------------------------------------------------------
# _to_logfmt
# ---------------------------------------------------------------------------

def test_to_logfmt_simple_values():
    result = _to_logfmt({"level": "info", "msg": "hello"})
    assert "level=info" in result
    assert "msg=hello" in result


def test_to_logfmt_quotes_values_with_spaces():
    result = _to_logfmt({"msg": "hello world"})
    assert 'msg="hello world"' in result


# ---------------------------------------------------------------------------
# normalize_line — JSON output (default)
# ---------------------------------------------------------------------------

def test_normalize_plain_line_returns_json_string():
    result = normalize_line("something happened")
    assert result is not None
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_normalize_plain_line_has_message_key():
    result = normalize_line("something happened")
    parsed = json.loads(result)
    assert parsed["msg"] == "something happened"


def test_normalize_json_line_preserves_existing_fields():
    raw = json.dumps({"level": "error", "msg": "oops", "code": 42})
    result = normalize_line(raw)
    parsed = json.loads(result)
    assert parsed["code"] == 42


def test_normalize_detects_level_from_plain_line():
    result = normalize_line("2024-01-01T00:00:00 ERROR something failed")
    parsed = json.loads(result)
    assert parsed.get("level") == "ERROR"


def test_normalize_empty_line_returns_none_by_default():
    assert normalize_line("   ") is None


def test_normalize_empty_line_kept_when_drop_empty_false():
    opts = NormalizeOptions(drop_empty=False)
    result = normalize_line("   ", opts)
    assert result is not None


def test_normalize_extra_fields_added():
    opts = NormalizeOptions(extra_fields={"host": "srv1"})
    result = normalize_line("hello", opts)
    parsed = json.loads(result)
    assert parsed["host"] == "srv1"


def test_normalize_extra_fields_do_not_overwrite_existing():
    raw = json.dumps({"host": "original"})
    opts = NormalizeOptions(extra_fields={"host": "override"})
    result = normalize_line(raw, opts)
    parsed = json.loads(result)
    assert parsed["host"] == "original"


# ---------------------------------------------------------------------------
# normalize_line — logfmt output
# ---------------------------------------------------------------------------

def test_normalize_logfmt_output_format():
    opts = NormalizeOptions(output_format="logfmt")
    result = normalize_line("hello world", opts)
    assert result is not None
    assert "=" in result
    assert "{" not in result


# ---------------------------------------------------------------------------
# normalize_lines
# ---------------------------------------------------------------------------

def test_normalize_lines_skips_empty():
    lines = ["info message", "", "  ", "another message"]
    results = _collect(lines)
    assert len(results) == 2


def test_normalize_lines_all_valid():
    lines = ["line one", "line two", "line three"]
    results = _collect(lines)
    assert len(results) == 3


def test_normalize_lines_empty_input_yields_nothing():
    assert _collect([]) == []
