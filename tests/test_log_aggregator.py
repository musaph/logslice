"""Tests for logslice.log_aggregator."""
from __future__ import annotations

import pytest

from logslice.log_aggregator import (
    AggregateGroup,
    AggregateResult,
    aggregate_by_field,
    aggregate_by_minute,
    format_aggregate_result,
)


_JSON_LINES = [
    '{"level": "info", "msg": "started"}',
    '{"level": "error", "msg": "failed"}',
    '{"level": "info", "msg": "done"}',
    '{"level": "debug", "msg": "trace"}',
    '{"level": "error", "msg": "timeout"}',
]

_PLAIN_LINES = ["just a plain line", "another plain line"]


def test_aggregate_by_field_groups_correctly():
    result = aggregate_by_field(_JSON_LINES, "level")
    keys = {g.key for g in result.groups}
    assert keys == {"info", "error", "debug"}


def test_aggregate_by_field_counts_are_correct():
    result = aggregate_by_field(_JSON_LINES, "level")
    counts = {g.key: g.count for g in result.groups}
    assert counts["info"] == 2
    assert counts["error"] == 2
    assert counts["debug"] == 1


def test_aggregate_by_field_total_lines():
    result = aggregate_by_field(_JSON_LINES, "level")
    assert result.total_lines == 5


def test_aggregate_by_field_unmatched_plain_lines():
    result = aggregate_by_field(_PLAIN_LINES, "level")
    assert result.unmatched == 2
    assert result.total_lines == 2


def test_aggregate_by_field_unmatched_group_present():
    result = aggregate_by_field(_PLAIN_LINES, "level")
    keys = {g.key for g in result.groups}
    assert "<unmatched>" in keys


def test_aggregate_by_field_keep_lines_false_default():
    result = aggregate_by_field(_JSON_LINES, "level")
    for g in result.groups:
        assert g.lines == []


def test_aggregate_by_field_keep_lines_true():
    result = aggregate_by_field(_JSON_LINES, "level", keep_lines=True)
    info_group = next(g for g in result.groups if g.key == "info")
    assert len(info_group.lines) == 2


def test_aggregate_by_field_case_insensitive_default():
    lines = ['{"Level": "INFO"}', '{"level": "info"}']
    result = aggregate_by_field(lines, "level")
    assert result.unmatched == 0


def test_aggregate_total_groups():
    result = aggregate_by_field(_JSON_LINES, "level")
    assert result.total_groups == 3


def test_aggregate_by_minute_groups_timestamped_lines():
    lines = [
        "2024-01-15T10:01:00 first",
        "2024-01-15T10:01:30 second",
        "2024-01-15T10:02:00 third",
    ]
    result = aggregate_by_minute(lines)
    assert result.total_groups == 2


def test_aggregate_by_minute_unmatched_when_no_timestamp():
    result = aggregate_by_minute(["no timestamp here"])
    assert result.unmatched == 1


def test_aggregate_by_minute_counts():
    lines = [
        "2024-01-15T10:01:00 a",
        "2024-01-15T10:01:45 b",
        "2024-01-15T10:03:00 c",
    ]
    result = aggregate_by_minute(lines)
    counts = {g.key: g.count for g in result.groups}
    assert counts["2024-01-15 10:01"] == 2
    assert counts["2024-01-15 10:03"] == 1


def test_format_aggregate_result_contains_keys():
    result = aggregate_by_field(_JSON_LINES, "level")
    output = format_aggregate_result(result)
    assert "info" in output
    assert "error" in output
    assert "debug" in output


def test_format_aggregate_result_contains_total():
    result = aggregate_by_field(_JSON_LINES, "level")
    output = format_aggregate_result(result)
    assert "Total" in output
    assert "5" in output


def test_empty_input_returns_empty_result():
    result = aggregate_by_field([], "level")
    assert result.total_lines == 0
    assert result.total_groups == 0
    assert result.unmatched == 0
