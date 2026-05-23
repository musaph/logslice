"""Tests for logslice.field_extractor."""

import pytest

from logslice.field_extractor import (
    extract_field_column,
    extract_fields,
    filter_by_field,
    get_field,
)


# ---------------------------------------------------------------------------
# extract_fields
# ---------------------------------------------------------------------------

def test_extract_fields_json():
    line = '{"level": "info", "msg": "started", "pid": 42}'
    fields = extract_fields(line)
    assert fields["level"] == "info"
    assert fields["msg"] == "started"
    assert fields["pid"] == "42"


def test_extract_fields_logfmt():
    line = 'time=2024-01-01 level=warn msg="disk full" host=srv01'
    fields = extract_fields(line)
    assert fields["level"] == "warn"
    assert fields["msg"] == "disk full"
    assert fields["host"] == "srv01"


def test_extract_fields_plain_kv():
    line = "status=200 method=GET path=/health"
    fields = extract_fields(line)
    assert fields["status"] == "200"
    assert fields["method"] == "GET"
    assert fields["path"] == "/health"


def test_extract_fields_unstructured_returns_empty():
    line = "This is a plain unstructured log line with no fields"
    assert extract_fields(line) == {}


def test_extract_fields_invalid_json_falls_back_to_kv():
    line = '{broken json level=error msg=oops}'
    fields = extract_fields(line)
    assert fields.get("level") == "error"


# ---------------------------------------------------------------------------
# get_field
# ---------------------------------------------------------------------------

def test_get_field_present():
    assert get_field("level=debug msg=ok", "level") == "debug"


def test_get_field_absent_returns_none():
    assert get_field("level=debug msg=ok", "host") is None


def test_get_field_json_line():
    line = '{"service": "api", "code": 500}'
    assert get_field(line, "service") == "api"


# ---------------------------------------------------------------------------
# filter_by_field
# ---------------------------------------------------------------------------

def test_filter_by_field_keeps_matching_lines():
    lines = [
        "level=info msg=hello",
        "level=error msg=boom",
        "level=info msg=world",
    ]
    result = list(filter_by_field(lines, "level", "info"))
    assert len(result) == 2
    assert all("level=info" in r for r in result)


def test_filter_by_field_no_match_yields_nothing():
    lines = ["level=debug msg=x", "level=info msg=y"]
    result = list(filter_by_field(lines, "level", "error"))
    assert result == []


def test_filter_by_field_case_insensitive():
    lines = ["level=INFO msg=hi", "level=debug msg=lo"]
    result = list(filter_by_field(lines, "level", "info", case_sensitive=False))
    assert len(result) == 1


def test_filter_by_field_missing_field_skipped():
    lines = ["msg=no_level_here", "level=warn msg=yes"]
    result = list(filter_by_field(lines, "level", "warn"))
    assert result == ["level=warn msg=yes"]


# ---------------------------------------------------------------------------
# extract_field_column
# ---------------------------------------------------------------------------

def test_extract_field_column_all_present():
    lines = ["level=info", "level=warn", "level=error"]
    assert list(extract_field_column(lines, "level")) == ["info", "warn", "error"]


def test_extract_field_column_missing_uses_default():
    lines = ["level=info", "msg=no_level"]
    result = list(extract_field_column(lines, "level", default="unknown"))
    assert result == ["info", "unknown"]
