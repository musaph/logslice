"""Tests for logslice.log_profiler."""
import time
from logslice.log_profiler import (
    ProfileResult,
    profile_lines,
    format_profile,
)


# ---------------------------------------------------------------------------
# ProfileResult properties
# ---------------------------------------------------------------------------

def test_timestamp_density_zero_when_no_lines():
    r = ProfileResult()
    assert r.timestamp_density == 0.0


def test_field_density_zero_when_no_lines():
    r = ProfileResult()
    assert r.field_density == 0.0


def test_avg_fields_per_line_zero_when_no_structured_lines():
    r = ProfileResult(total_lines=5, lines_with_fields=0, total_fields=0)
    assert r.avg_fields_per_line == 0.0


def test_lines_per_second_zero_when_no_elapsed():
    r = ProfileResult(total_lines=100, elapsed_seconds=0.0)
    assert r.lines_per_second == 0.0


# ---------------------------------------------------------------------------
# profile_lines
# ---------------------------------------------------------------------------

def test_empty_input_returns_zero_result():
    r = profile_lines([])
    assert r.total_lines == 0
    assert r.lines_with_timestamp == 0
    assert r.lines_with_fields == 0


def test_counts_total_lines():
    lines = ["hello", "world", "foo"]
    r = profile_lines(lines)
    assert r.total_lines == 3


def test_detects_timestamp_in_iso8601_line():
    lines = ["2024-01-15T10:30:00 some event"]
    r = profile_lines(lines)
    assert r.lines_with_timestamp == 1


def test_plain_line_has_no_timestamp():
    lines = ["no timestamp here"]
    r = profile_lines(lines)
    assert r.lines_with_timestamp == 0


def test_detects_json_fields():
    lines = ['{"level": "info", "msg": "ok"}']
    r = profile_lines(lines)
    assert r.lines_with_fields == 1
    assert r.total_fields >= 2


def test_unique_field_names_collected():
    lines = ['{"level": "info", "msg": "ok"}', '{"level": "warn", "host": "srv1"}']
    r = profile_lines(lines)
    assert "level" in r.unique_field_names
    assert "msg" in r.unique_field_names
    assert "host" in r.unique_field_names


def test_elapsed_seconds_is_positive():
    lines = ["line"] * 10
    r = profile_lines(lines)
    assert r.elapsed_seconds >= 0.0


def test_timestamp_density_calculation():
    lines = ["2024-01-15T10:30:00 event", "plain line", "another plain"]
    r = profile_lines(lines)
    assert abs(r.timestamp_density - 1 / 3) < 1e-9


# ---------------------------------------------------------------------------
# format_profile
# ---------------------------------------------------------------------------

def test_format_profile_yields_strings():
    r = profile_lines(["hello"])
    output = list(format_profile(r))
    assert all(isinstance(line, str) for line in output)


def test_format_profile_contains_total_lines():
    r = ProfileResult(total_lines=42)
    text = "\n".join(format_profile(r))
    assert "42" in text


def test_format_profile_shows_field_names_when_present():
    r = ProfileResult(unique_field_names={"level", "msg"})
    text = "\n".join(format_profile(r))
    assert "field_names" in text


def test_format_profile_omits_field_names_line_when_empty():
    r = ProfileResult()
    lines = list(format_profile(r))
    assert not any("field_names" in l for l in lines)
