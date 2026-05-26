"""Tests for logslice.log_joiner."""
from __future__ import annotations

import json
from typing import Dict, List

import pytest

from logslice.log_joiner import (
    JoinedLine,
    JoinResult,
    format_join_result,
    join_logs,
    total_joined,
    total_unmatched,
)


def _json(req_id: str, msg: str) -> str:
    return json.dumps({"request_id": req_id, "msg": msg})


# ---------------------------------------------------------------------------
# join_logs
# ---------------------------------------------------------------------------

def test_empty_sources_return_empty_result():
    result = join_logs({}, join_field="request_id")
    assert result.joined == []
    assert result.unmatched == {}


def test_single_source_all_unmatched():
    lines = [_json("abc", "start"), _json("def", "end")]
    result = join_logs({"a": iter(lines)}, join_field="request_id")
    assert result.joined == []
    assert len(result.unmatched["a"]) == 2


def test_two_sources_matching_key_produces_joined_entry():
    a = [_json("req-1", "from-a")]
    b = [_json("req-1", "from-b")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert len(result.joined) == 1
    jl = result.joined[0]
    assert jl.key == "req-1"
    assert "a" in jl.sources
    assert "b" in jl.sources


def test_non_matching_keys_go_to_unmatched():
    a = [_json("req-1", "from-a")]
    b = [_json("req-2", "from-b")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert result.joined == []
    assert len(result.unmatched["a"]) == 1
    assert len(result.unmatched["b"]) == 1


def test_plain_lines_without_field_go_to_unmatched():
    a = ["plain log line without any field"]
    b = [_json("req-1", "structured")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert "plain log line without any field" in result.unmatched["a"]


def test_case_insensitive_join():
    a = [_json("REQ-1", "upper")]
    b = [_json("req-1", "lower")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id", case_sensitive=False)
    assert len(result.joined) == 1


def test_case_sensitive_join_does_not_merge_different_cases():
    a = [_json("REQ-1", "upper")]
    b = [_json("req-1", "lower")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id", case_sensitive=True)
    assert result.joined == []


def test_multiple_keys_some_matching():
    a = [_json("req-1", "a1"), _json("req-2", "a2")]
    b = [_json("req-1", "b1"), _json("req-3", "b3")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert len(result.joined) == 1
    assert result.joined[0].key == "req-1"
    assert total_unmatched(result) == 2  # req-2 from a, req-3 from b


# ---------------------------------------------------------------------------
# total_joined / total_unmatched
# ---------------------------------------------------------------------------

def test_total_joined_counts_multi_source_groups():
    a = [_json("k1", "x")]
    b = [_json("k1", "y")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert total_joined(result) == 1


def test_total_unmatched_sums_all_sources():
    a = ["line1", "line2"]
    b = ["line3"]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    assert total_unmatched(result) == 3


# ---------------------------------------------------------------------------
# format_join_result
# ---------------------------------------------------------------------------

def test_format_join_result_yields_lines():
    a = [_json("req-1", "from-a")]
    b = [_json("req-1", "from-b")]
    result = join_logs({"a": iter(a), "b": iter(b)}, join_field="request_id")
    lines = list(format_join_result(result))
    assert len(lines) == 1
    assert "req-1" in lines[0]
    assert "[a]" in lines[0]
    assert "[b]" in lines[0]


def test_format_join_result_empty_yields_nothing():
    result = JoinResult()
    assert list(format_join_result(result)) == []
