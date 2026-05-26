"""Tests for logslice.log_tracer."""
import pytest

from logslice.log_tracer import (
    TraceEntry,
    TraceResult,
    compute_trace_result,
    format_trace_result,
    trace_lines,
)


def _json(request_id: str, msg: str) -> str:
    return f'{{"request_id": "{request_id}", "msg": "{msg}"}}'


LINES = [
    _json("abc-123", "start"),
    _json("xyz-999", "other"),
    _json("abc-123", "processing"),
    _json("abc-123", "done"),
    "plain line without fields",
]


def _collect(it):
    return list(it)


def test_empty_input_yields_nothing():
    assert _collect(trace_lines([], "request_id", "abc-123")) == []


def test_matching_lines_returned():
    entries = _collect(trace_lines(LINES, "request_id", "abc-123"))
    assert len(entries) == 3


def test_non_matching_lines_excluded():
    entries = _collect(trace_lines(LINES, "request_id", "xyz-999"))
    assert len(entries) == 1
    assert entries[0].trace_value == "xyz-999"


def test_plain_lines_without_field_skipped():
    entries = _collect(trace_lines(LINES, "request_id", "abc-123"))
    # plain line has no request_id
    for e in entries:
        assert "plain" not in e.line


def test_entry_line_numbers_are_one_based():
    entries = _collect(trace_lines(LINES, "request_id", "abc-123"))
    assert entries[0].line_number == 1
    assert entries[1].line_number == 3
    assert entries[2].line_number == 4


def test_entry_is_trace_entry_instance():
    entries = _collect(trace_lines(LINES, "request_id", "abc-123"))
    assert all(isinstance(e, TraceEntry) for e in entries)


def test_entry_fields_populated():
    entries = _collect(trace_lines(LINES, "request_id", "abc-123"))
    assert entries[0].fields["msg"] == "start"


def test_case_insensitive_default():
    lines = [_json("ABC-123", "upper")]
    entries = _collect(trace_lines(lines, "request_id", "abc-123"))
    assert len(entries) == 1


def test_case_sensitive_no_match():
    lines = [_json("ABC-123", "upper")]
    entries = _collect(trace_lines(lines, "request_id", "abc-123", case_sensitive=True))
    assert entries == []


def test_compute_trace_result_returns_trace_result():
    result = compute_trace_result(LINES, "request_id", "abc-123")
    assert isinstance(result, TraceResult)


def test_compute_trace_result_count():
    result = compute_trace_result(LINES, "request_id", "abc-123")
    assert result.count == 3


def test_compute_trace_result_stores_field_and_value():
    result = compute_trace_result(LINES, "request_id", "abc-123")
    assert result.trace_field == "request_id"
    assert result.trace_value == "abc-123"


def test_format_trace_result_contains_header():
    result = compute_trace_result(LINES, "request_id", "abc-123")
    text = format_trace_result(result)
    assert "trace_field=request_id" in text
    assert "matches=3" in text


def test_format_trace_result_contains_lines():
    result = compute_trace_result(LINES, "request_id", "abc-123")
    text = format_trace_result(result)
    assert "start" in text
    assert "processing" in text
    assert "done" in text


def test_missing_field_entirely_yields_nothing():
    entries = _collect(trace_lines(LINES, "nonexistent_field", "abc-123"))
    assert entries == []
