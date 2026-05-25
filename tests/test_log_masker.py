"""Tests for logslice.log_masker."""
from __future__ import annotations

import json

import pytest

from logslice.log_masker import (
    MaskOptions,
    MaskResult,
    compute_mask_result,
    mask_line,
    mask_lines,
)


def _opts(**kwargs) -> MaskOptions:
    return MaskOptions(**kwargs)


# ---------------------------------------------------------------------------
# mask_line – JSON
# ---------------------------------------------------------------------------

def test_json_field_masked():
    line = json.dumps({"user": "alice", "action": "login"})
    result = mask_line(line, _opts(fields=["user"]))
    assert json.loads(result.masked)["user"] == "***"


def test_json_non_target_field_unchanged():
    line = json.dumps({"user": "alice", "action": "login"})
    result = mask_line(line, _opts(fields=["user"]))
    assert json.loads(result.masked)["action"] == "login"


def test_json_case_insensitive_default():
    line = json.dumps({"User": "bob"})
    result = mask_line(line, _opts(fields=["user"]))
    assert json.loads(result.masked)["User"] == "***"


def test_json_case_sensitive_no_match():
    line = json.dumps({"User": "bob"})
    result = mask_line(line, _opts(fields=["user"], case_sensitive=True))
    assert json.loads(result.masked)["User"] == "bob"
    assert not result.changed


def test_json_custom_mask_token():
    line = json.dumps({"password": "secret"})
    result = mask_line(line, _opts(fields=["password"], mask="[REDACTED]"))
    assert json.loads(result.masked)["password"] == "[REDACTED]"


def test_json_no_fields_returns_unchanged():
    line = json.dumps({"x": "y"})
    result = mask_line(line, _opts())
    assert not result.changed
    assert result.masked == result.original


# ---------------------------------------------------------------------------
# mask_line – logfmt
# ---------------------------------------------------------------------------

def test_logfmt_field_masked():
    result = mask_line("level=info user=alice", _opts(fields=["user"]))
    assert "user=***" in result.masked


def test_logfmt_non_target_field_unchanged():
    result = mask_line("level=info user=alice", _opts(fields=["user"]))
    assert "level=info" in result.masked


def test_logfmt_case_insensitive_default():
    result = mask_line("Level=warn user=alice", _opts(fields=["level"]))
    assert "Level=***" in result.masked


def test_logfmt_quoted_value_masked():
    result = mask_line('msg="hello world" token=abc', _opts(fields=["token"]))
    assert "token=***" in result.masked
    assert 'msg="hello world"' in result.masked


def test_logfmt_no_match_unchanged():
    line = "level=info msg=ok"
    result = mask_line(line, _opts(fields=["user"]))
    assert not result.changed


# ---------------------------------------------------------------------------
# MaskResult attributes
# ---------------------------------------------------------------------------

def test_result_is_mask_result_instance():
    result = mask_line("level=info", _opts(fields=["level"]))
    assert isinstance(result, MaskResult)


def test_result_changed_true_when_masked():
    result = mask_line(json.dumps({"pw": "x"}), _opts(fields=["pw"]))
    assert result.changed


# ---------------------------------------------------------------------------
# mask_lines iterator
# ---------------------------------------------------------------------------

def test_mask_lines_yields_results():
    lines = [json.dumps({"a": "1"}), json.dumps({"a": "2"})]
    results = list(mask_lines(lines, _opts(fields=["a"])))
    assert len(results) == 2
    assert all(r.changed for r in results)


# ---------------------------------------------------------------------------
# compute_mask_result
# ---------------------------------------------------------------------------

def test_compute_mask_result_returns_lines_and_count():
    lines = [
        json.dumps({"token": "abc"}),
        json.dumps({"msg": "ok"}),
    ]
    out, count = compute_mask_result(lines, _opts(fields=["token"]))
    assert count == 1
    assert len(out) == 2


def test_compute_mask_result_zero_when_no_match():
    lines = ["plain text", "another line"]
    _, count = compute_mask_result(lines, _opts(fields=["secret"]))
    assert count == 0
