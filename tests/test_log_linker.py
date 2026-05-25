"""Tests for logslice.log_linker."""
from __future__ import annotations

import json
from typing import List

import pytest

from logslice.log_linker import LinkedGroup, LinkResult, format_link_result, link_logs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _json(trace_id: str, msg: str) -> str:
    return json.dumps({"trace_id": trace_id, "msg": msg})


def _logfmt(trace_id: str, msg: str) -> str:
    return f'trace_id={trace_id} msg="{msg}"'


def _src(label: str, *lines: str):
    return (label, list(lines))


def _collect(it) -> List[str]:
    return list(it)


# ---------------------------------------------------------------------------
# link_logs
# ---------------------------------------------------------------------------

def test_empty_sources_return_empty_result():
    result = link_logs([], link_field="trace_id")
    assert result.total_groups() == 0
    assert result.total_unmatched() == 0


def test_single_source_single_group():
    src = _src("app", _json("abc", "start"), _json("abc", "end"))
    result = link_logs([src], link_field="trace_id")
    assert result.total_groups() == 1
    assert result.groups[0].key == "abc"
    assert result.groups[0].line_count() == 2


def test_two_sources_merged_by_field():
    s1 = _src("svc-a", _json("x1", "req"))
    s2 = _src("svc-b", _json("x1", "resp"))
    result = link_logs([s1, s2], link_field="trace_id")
    assert result.total_groups() == 1
    grp = result.groups[0]
    assert grp.line_count() == 2
    assert set(grp.unique_sources()) == {"svc-a", "svc-b"}


def test_lines_without_field_go_to_unmatched():
    src = _src("app", "plain log line without fields", _json("t1", "ok"))
    result = link_logs([src], link_field="trace_id")
    assert result.total_unmatched() == 1
    assert result.total_matched() == 1


def test_multiple_groups_created():
    src = _src(
        "app",
        _json("aaa", "one"),
        _json("bbb", "two"),
        _json("aaa", "three"),
    )
    result = link_logs([src], link_field="trace_id")
    assert result.total_groups() == 2
    keys = {g.key for g in result.groups}
    assert keys == {"aaa", "bbb"}


def test_case_insensitive_field_name_default():
    src = _src("app", '{"Trace_ID": "z9", "msg": "hi"}')
    result = link_logs([src], link_field="trace_id")
    assert result.total_groups() == 1


def test_case_sensitive_field_name_no_match():
    src = _src("app", '{"Trace_ID": "z9", "msg": "hi"}')
    result = link_logs([src], link_field="trace_id", case_sensitive=True)
    assert result.total_groups() == 0
    assert result.total_unmatched() == 1


def test_logfmt_lines_linked():
    src = _src("app", _logfmt("r1", "a"), _logfmt("r1", "b"), _logfmt("r2", "c"))
    result = link_logs([src], link_field="trace_id")
    assert result.total_groups() == 2


def test_total_matched_counts_all_grouped_lines():
    src = _src("app", _json("t", "a"), _json("t", "b"), _json("t", "c"))
    result = link_logs([src], link_field="trace_id")
    assert result.total_matched() == 3


# ---------------------------------------------------------------------------
# format_link_result
# ---------------------------------------------------------------------------

def test_format_shows_group_key():
    src = _src("app", _json("mykey", "hello"))
    result = link_logs([src], link_field="trace_id")
    output = _collect(format_link_result(result))
    assert any("mykey" in line for line in output)


def test_format_unmatched_hidden_by_default():
    src = _src("app", "plain line")
    result = link_logs([src], link_field="trace_id")
    output = _collect(format_link_result(result, show_unmatched=False))
    assert not any("unmatched" in line for line in output)


def test_format_unmatched_shown_when_requested():
    src = _src("app", "plain line")
    result = link_logs([src], link_field="trace_id")
    output = _collect(format_link_result(result, show_unmatched=True))
    assert any("unmatched" in line for line in output)
