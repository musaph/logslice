"""Tests for logslice.cli_profiler."""
import io
import json
import gzip
import os
import tempfile
import pytest

from logslice.cli_profiler import build_profiler_parser, run_profiler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(
        '2024-01-15T10:00:00 {"level":"info","msg":"started"}\n'
        '2024-01-15T10:00:01 {"level":"warn","msg":"slow"}\n'
        "plain line without timestamp\n",
        encoding="utf-8",
    )
    return str(p)


def _run(argv, out=None, err=None):
    if out is None:
        out = io.StringIO()
    if err is None:
        err = io.StringIO()
    parser = build_profiler_parser()
    args = parser.parse_args(argv)
    code = run_profiler(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_returns_zero_on_success(plain_log):
    code, _, _ = _run([plain_log])
    assert code == 0


def test_run_returns_one_on_missing_file():
    code, _, err = _run(["no_such_file.log"])
    assert code == 1
    assert "error" in err


def test_run_plain_output_contains_total_lines(plain_log):
    _, out, _ = _run([plain_log])
    assert "total_lines" in out
    assert "3" in out


def test_run_plain_output_contains_timestamp_density(plain_log):
    _, out, _ = _run([plain_log])
    assert "lines_with_timestamp" in out


def test_run_json_flag_emits_valid_json(plain_log):
    _, out, _ = _run([plain_log, "--json"])
    data = json.loads(out)
    assert isinstance(data, dict)


def test_run_json_has_expected_keys(plain_log):
    _, out, _ = _run([plain_log, "--json"])
    data = json.loads(out)
    for key in ("total_lines", "lines_with_timestamp", "timestamp_density",
                "lines_with_fields", "field_density", "unique_field_names",
                "avg_fields_per_line", "elapsed_seconds", "lines_per_second"):
        assert key in data, f"missing key: {key}"


def test_run_json_total_lines_correct(plain_log):
    _, out, _ = _run([plain_log, "--json"])
    data = json.loads(out)
    assert data["total_lines"] == 3


def test_run_json_timestamp_density_between_zero_and_one(plain_log):
    _, out, _ = _run([plain_log, "--json"])
    data = json.loads(out)
    assert 0.0 <= data["timestamp_density"] <= 1.0


def test_run_json_unique_field_names_is_list(plain_log):
    _, out, _ = _run([plain_log, "--json"])
    data = json.loads(out)
    assert isinstance(data["unique_field_names"], list)
