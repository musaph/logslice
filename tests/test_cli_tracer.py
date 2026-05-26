"""Tests for logslice.cli_tracer."""
import io
import json
import os
import tempfile

import pytest

from logslice.cli_tracer import run_tracer


def _write_plain(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    f.writelines(lines)
    f.close()
    return f.name


@pytest.fixture()
def json_log(tmp_path):
    path = tmp_path / "trace.log"
    entries = [
        {"request_id": "abc-123", "msg": "start"},
        {"request_id": "xyz-999", "msg": "other"},
        {"request_id": "abc-123", "msg": "done"},
    ]
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return str(path)


def _run(argv, **kwargs):
    out = io.StringIO()
    rc = run_tracer(argv, out=out)
    return rc, out.getvalue()


def test_run_returns_zero_on_success(json_log):
    rc, _ = _run([json_log, "--field", "request_id", "--value", "abc-123"])
    assert rc == 0


def test_run_returns_one_on_missing_file():
    rc, _ = _run(["no_such_file.log", "--field", "request_id", "--value", "abc-123"])
    assert rc == 1


def test_run_output_contains_matching_lines(json_log):
    _, out = _run([json_log, "--field", "request_id", "--value", "abc-123"])
    assert "start" in out
    assert "done" in out


def test_run_output_excludes_non_matching_lines(json_log):
    _, out = _run([json_log, "--field", "request_id", "--value", "abc-123"])
    assert "other" not in out


def test_run_count_flag_prints_integer(json_log):
    _, out = _run(
        [json_log, "--field", "request_id", "--value", "abc-123", "--count"]
    )
    assert out.strip() == "2"


def test_run_case_insensitive_default(tmp_path):
    path = tmp_path / "ci.log"
    path.write_text('{"request_id": "ABC-123", "msg": "hi"}\n')
    _, out = _run([str(path), "--field", "request_id", "--value", "abc-123"])
    assert "hi" in out


def test_run_case_sensitive_no_match(tmp_path):
    path = tmp_path / "cs.log"
    path.write_text('{"request_id": "ABC-123", "msg": "hi"}\n')
    _, out = _run(
        [
            str(path),
            "--field",
            "request_id",
            "--value",
            "abc-123",
            "--case-sensitive",
        ]
    )
    assert "matches=0" in out
