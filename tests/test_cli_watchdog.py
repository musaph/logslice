"""Tests for logslice.cli_watchdog."""
import gzip
import io
import os
import tempfile

import pytest

from logslice.cli_watchdog import build_watchdog_parser, run_watchdog


LOG_LINES = [
    "2024-01-01 INFO  service started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 WARN  high memory\n",
    "2024-01-01 ERROR connection refused\n",
]


@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("".join(LOG_LINES))
    return str(p)


def _run(argv, out=None, err=None):
    if out is None:
        out = io.StringIO()
    if err is None:
        err = io.StringIO()
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)
    rc = run_watchdog(args, out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(plain_log):
    rc, _, _ = _run([plain_log, "-p", "ERROR"])
    assert rc == 0


def test_run_returns_one_on_missing_file():
    rc, _, err = _run(["/no/such/file.log", "-p", "ERROR"])
    assert rc == 1
    assert "error" in err.lower()


def test_run_prints_alerts(plain_log):
    rc, out, _ = _run([plain_log, "-p", "ERROR"])
    assert out.count("[ALERT]") == 2


def test_run_no_patterns_no_output(plain_log):
    rc, out, _ = _run([plain_log])
    assert rc == 0
    assert out == ""


def test_run_summary_flag(plain_log):
    rc, out, _ = _run([plain_log, "-p", "ERROR", "--summary"])
    assert "lines_scanned=" in out
    assert "alerts=" in out


def test_run_stop_on_first(plain_log):
    rc, out, _ = _run([plain_log, "-p", "ERROR", "--stop-on-first"])
    assert out.count("[ALERT]") == 1


def test_run_max_alerts(plain_log):
    rc, out, _ = _run([plain_log, "-p", "ERROR", "--max-alerts", "1"])
    assert out.count("[ALERT]") == 1


def test_run_case_sensitive_no_match(plain_log):
    rc, out, _ = _run([plain_log, "-p", "error", "--case-sensitive"])
    assert out == ""


def test_run_multiple_patterns(plain_log):
    rc, out, _ = _run([plain_log, "-p", "ERROR", "-p", "WARN"])
    assert out.count("[ALERT]") == 3
