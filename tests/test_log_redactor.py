"""Tests for logslice.log_redactor."""
import json
import pytest

from logslice.log_redactor import (
    RedactOptions,
    redact_line,
    redact_lines,
    count_redacted,
)


def _opts(**kwargs) -> RedactOptions:
    return RedactOptions(**kwargs)


# ---------------------------------------------------------------------------
# redact_line – JSON
# ---------------------------------------------------------------------------

def test_json_field_redacted():
    line = json.dumps({"user": "alice", "msg": "login"})
    result = redact_line(line, _opts(fields=["user"]))
    assert json.loads(result)["user"] == "***REDACTED***"


def test_json_non_target_field_unchanged():
    line = json.dumps({"user": "alice", "msg": "login"})
    result = redact_line(line, _opts(fields=["user"]))
    assert json.loads(result)["msg"] == "login"


def test_json_field_case_insensitive_default():
    line = json.dumps({"Password": "secret"})
    result = redact_line(line, _opts(fields=["password"]))
    assert json.loads(result)["Password"] == "***REDACTED***"


def test_json_field_case_sensitive_no_match():
    line = json.dumps({"Password": "secret"})
    result = redact_line(line, _opts(fields=["password"], case_sensitive=True))
    assert json.loads(result)["Password"] == "secret"


def test_json_custom_mask():
    line = json.dumps({"token": "abc123"})
    result = redact_line(line, _opts(fields=["token"], mask="[HIDDEN]"))
    assert json.loads(result)["token"] == "[HIDDEN]"


# ---------------------------------------------------------------------------
# redact_line – logfmt
# ---------------------------------------------------------------------------

def test_logfmt_field_redacted():
    line = "level=info user=alice msg=login"
    result = redact_line(line, _opts(fields=["user"]))
    assert "user=***REDACTED***" in result


def test_logfmt_non_target_unchanged():
    line = "level=info user=alice msg=login"
    result = redact_line(line, _opts(fields=["user"]))
    assert "level=info" in result


def test_logfmt_quoted_value_redacted():
    line = 'level=info user="alice smith" msg=login'
    result = redact_line(line, _opts(fields=["user"]))
    assert "user=***REDACTED***" in result


# ---------------------------------------------------------------------------
# redact_line – pattern redaction
# ---------------------------------------------------------------------------

def test_pattern_redacts_ip_address():
    line = "Connected from 192.168.1.1 ok"
    result = redact_line(line, _opts(patterns=[r"\d{1,3}(?:\.\d{1,3}){3}"]))
    assert "192.168.1.1" not in result
    assert "***REDACTED***" in result


def test_pattern_case_insensitive_default():
    line = "Token: BEARER abc123"
    result = redact_line(line, _opts(patterns=[r"bearer \S+"]))
    assert "BEARER abc123" not in result


def test_no_opts_returns_line_unchanged():
    line = "plain log line"
    assert redact_line(line) == line


# ---------------------------------------------------------------------------
# redact_lines
# ---------------------------------------------------------------------------

def test_redact_lines_generator():
    lines = [
        json.dumps({"user": "bob", "action": "read"}),
        json.dumps({"user": "eve", "action": "write"}),
    ]
    opts = _opts(fields=["user"])
    results = list(redact_lines(lines, opts))
    assert all(json.loads(r)["user"] == "***REDACTED***" for r in results)


def test_redact_lines_empty_input():
    assert list(redact_lines([], _opts(fields=["x"]))) == []


# ---------------------------------------------------------------------------
# count_redacted
# ---------------------------------------------------------------------------

def test_count_redacted_counts_altered_lines():
    lines = [
        json.dumps({"password": "s3cr3t"}),
        json.dumps({"msg": "hello"}),
        json.dumps({"password": "another"}),
    ]
    assert count_redacted(lines, _opts(fields=["password"])) == 2


def test_count_redacted_zero_when_no_match():
    lines = ["plain line", "another line"]
    assert count_redacted(lines, _opts(fields=["token"])) == 0
