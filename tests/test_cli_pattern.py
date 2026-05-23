"""Tests for logslice.cli_pattern."""
import gzip
import os
import textwrap
from pathlib import Path

import pytest

from logslice.cli_pattern import run_pattern

LOG_CONTENT = textwrap.dedent("""\
    2024-01-01 INFO  service started
    2024-01-01 DEBUG loop iteration 1
    2024-01-01 ERROR connection refused
    2024-01-01 INFO  request received
    2024-01-01 WARN  slow query detected
""")


@pytest.fixture()
def plain_log(tmp_path: Path) -> str:
    p = tmp_path / "app.log"
    p.write_text(LOG_CONTENT)
    return str(p)


def test_run_returns_zero_on_match(plain_log, capsys):
    rc = run_pattern(["INFO", plain_log])
    assert rc == 0
    out = capsys.readouterr().out
    assert "INFO" in out


def test_run_filters_matching_lines(plain_log, capsys):
    run_pattern(["ERROR", plain_log])
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
    assert "ERROR" in out[0]


def test_run_invert_excludes_matching(plain_log, capsys):
    run_pattern(["--invert", "INFO", plain_log])
    out = capsys.readouterr().out
    assert "INFO" not in out
    assert "ERROR" in out


def test_run_count_prints_number(plain_log, capsys):
    run_pattern(["--count", "INFO", plain_log])
    out = capsys.readouterr().out.strip()
    assert out == "2"


def test_run_case_insensitive_default(plain_log, capsys):
    run_pattern(["error", plain_log])
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_run_case_sensitive_no_match(plain_log, capsys):
    run_pattern(["--case-sensitive", "error", plain_log])
    out = capsys.readouterr().out.strip()
    assert out == ""


def test_run_returns_one_on_missing_file(capsys):
    rc = run_pattern(["INFO", "/nonexistent/file.log"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_run_count_zero_for_no_match(plain_log, capsys):
    run_pattern(["--count", "CRITICAL", plain_log])
    out = capsys.readouterr().out.strip()
    assert out == "0"


def test_run_pattern_with_regex(plain_log, capsys):
    run_pattern([r"(INFO|WARN)", plain_log])
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 3
