"""Tests for logslice.cli_correlator."""
import io
import json
import os
import tempfile

import pytest

from logslice.cli_correlator import build_correlator_parser, run_correlator


def _write_plain(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for line in lines:
        f.write(line + "\n")
    f.close()
    return f.name


@pytest.fixture()
def json_log(tmp_path):
    path = tmp_path / "test.log"
    entries = [
        {"request_id": "aaa", "msg": "start"},
        {"request_id": "aaa", "msg": "end"},
        {"request_id": "bbb", "msg": "only"},
        {"msg": "no id here"},
    ]
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return str(path)


def _run(argv, **kwargs):
    parser = build_correlator_parser()
    args = parser.parse_args(argv)
    out = io.StringIO()
    err = io.StringIO()
    rc = run_correlator(args, out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(json_log):
    rc, _, _ = _run([json_log, "--field", "request_id"])
    assert rc == 0


def test_run_returns_one_on_missing_file():
    rc, _, err = _run(["nonexistent.log", "--field", "request_id"])
    assert rc == 1
    assert "error" in err


def test_run_outputs_matched_lines(json_log):
    rc, out, _ = _run([json_log, "--field", "request_id"])
    assert rc == 0
    output_lines = [l for l in out.splitlines() if l]
    # 3 matched lines (aaa x2, bbb x1)
    assert len(output_lines) == 3


def test_run_summary_flag_prints_summary(json_log):
    rc, out, _ = _run([json_log, "--field", "request_id", "--summary"])
    assert rc == 0
    assert "groups=" in out
    assert "matched=" in out
    assert "unmatched=" in out


def test_run_unmatched_flag_prints_unmatched_lines(json_log):
    rc, out, _ = _run([json_log, "--field", "request_id", "--unmatched"])
    assert rc == 0
    lines = [l for l in out.splitlines() if l]
    assert len(lines) == 1
    assert "no id here" in lines[0]


def test_run_min_group_filters_small_groups(json_log):
    rc, out, _ = _run([json_log, "--field", "request_id", "--min-group", "2"])
    assert rc == 0
    lines = [l for l in out.splitlines() if l]
    # only 'aaa' group has 2 lines
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert data["request_id"] == "aaa"


def test_run_summary_group_count(json_log):
    _, out, _ = _run([json_log, "--field", "request_id", "--summary"])
    assert "groups=2" in out
