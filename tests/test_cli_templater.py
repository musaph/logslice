"""Tests for logslice.cli_templater."""
from __future__ import annotations

import io
import os
import tempfile

import pytest

from logslice.cli_templater import build_templater_parser, run_templater


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def json_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(
        '{"level": "INFO", "msg": "started", "service": "api"}\n'
        '{"level": "ERROR", "msg": "crashed", "service": "worker"}\n',
        encoding="utf-8",
    )
    return str(p)


def _run(argv, out=None, err=None):
    parser = build_templater_parser()
    args = parser.parse_args(argv)
    out = out or io.StringIO()
    err = err or io.StringIO()
    code = run_templater(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_run_returns_zero_on_success(json_log):
    code, _, _ = _run(["--template", "{level}", json_log])
    assert code == 0


def test_run_returns_one_on_missing_file():
    code, _, err = _run(["--template", "{level}", "/no/such/file.log"])
    assert code == 1
    assert "error" in err.lower()


def test_run_renders_json_fields(json_log):
    code, out, _ = _run(["--template", "{level}:{msg}", json_log])
    assert code == 0
    lines = out.strip().splitlines()
    assert lines[0] == "INFO:started"
    assert lines[1] == "ERROR:crashed"


def test_run_skip_unmatched_drops_plain_lines(tmp_path):
    p = tmp_path / "mixed.log"
    p.write_text(
        '{"level": "INFO", "msg": "ok"}\n'
        "plain line with no structure\n",
        encoding="utf-8",
    )
    code, out, _ = _run(["--template", "{level}", "--skip-unmatched", str(p)])
    assert code == 0
    lines = out.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "INFO"


def test_run_fallback_used_for_plain_lines(tmp_path):
    p = tmp_path / "mixed.log"
    p.write_text(
        '{"level": "DEBUG", "msg": "hi"}\n'
        "unstructured\n",
        encoding="utf-8",
    )
    code, out, _ = _run(["--template", "{level}", "--fallback", "N/A", str(p)])
    assert code == 0
    lines = out.strip().splitlines()
    assert "N/A" in lines


def test_run_stats_flag_writes_to_stderr(json_log):
    code, out, err = _run(["--template", "{level}", "--stats", json_log])
    assert code == 0
    assert "total" in err
    assert "rendered" in err


def test_run_stats_still_writes_rendered_lines(json_log):
    code, out, err = _run(["--template", "{level}", "--stats", json_log])
    assert code == 0
    assert out.strip() != ""
