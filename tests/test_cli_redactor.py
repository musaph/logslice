"""Tests for logslice.cli_redactor."""
import io
import json
import os
import tempfile

import pytest

from logslice.cli_redactor import build_redactor_parser, run_redactor


@pytest.fixture()
def plain_log(tmp_path):
    lines = [
        json.dumps({"user": "alice", "msg": "login"}) + "\n",
        json.dumps({"user": "bob", "msg": "logout"}) + "\n",
        "plain line without structure\n",
    ]
    p = tmp_path / "sample.log"
    p.write_text("".join(lines))
    return str(p)


def _run(argv, **kwargs):
    parser = build_redactor_parser()
    args = parser.parse_args(argv)
    out = io.StringIO()
    err = io.StringIO()
    rc = run_redactor(args, out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(plain_log):
    rc, _, _ = _run([plain_log, "--field", "user"])
    assert rc == 0


def test_run_returns_one_on_missing_file():
    rc, _, err = _run(["nonexistent_file.log", "--field", "user"])
    assert rc == 1
    assert "error" in err.lower()


def test_run_redacts_json_field(plain_log):
    rc, out, _ = _run([plain_log, "--field", "user"])
    for line in out.strip().splitlines():
        if line.startswith("{"):
            assert json.loads(line)["user"] == "***REDACTED***"


def test_run_custom_mask(plain_log):
    rc, out, _ = _run([plain_log, "--field", "user", "--mask", "[GONE]"])
    for line in out.strip().splitlines():
        if line.startswith("{"):
            assert json.loads(line)["user"] == "[GONE]"


def test_run_count_flag(plain_log):
    rc, out, _ = _run([plain_log, "--field", "user", "--count"])
    assert rc == 0
    assert out.strip().isdigit()
    assert int(out.strip()) == 2


def test_run_pattern_redaction(plain_log):
    rc, out, _ = _run([plain_log, "--pattern", r"\b\w+@\w+\.\w+\b"])
    assert rc == 0


def test_run_no_fields_passes_lines_through(plain_log):
    rc, out, _ = _run([plain_log])
    assert rc == 0
    assert "alice" in out


def test_run_case_sensitive_does_not_redact_mismatched_case(plain_log):
    # fields stored as lowercase "user" in JSON; we search for "User" case-sensitively
    rc, out, _ = _run([plain_log, "--field", "User", "--case-sensitive"])
    assert rc == 0
    for line in out.strip().splitlines():
        if line.startswith("{"):
            assert json.loads(line)["user"] != "***REDACTED***"
