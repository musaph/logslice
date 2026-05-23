"""Tests for logslice.cli_diff."""
import gzip
import io
import os
import tempfile

import pytest

from logslice.cli_diff import build_diff_parser, run_diff


def _write_plain(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    f.writelines(lines)
    f.close()
    return f.name


@pytest.fixture()
def baseline_file():
    path = _write_plain(["alpha\n", "beta\n", "gamma\n"])
    yield path
    os.unlink(path)


@pytest.fixture()
def current_file():
    path = _write_plain(["beta\n", "gamma\n", "delta\n"])
    yield path
    os.unlink(path)


def _run(baseline, current, extra_args=None):
    parser = build_diff_parser()
    argv = [baseline, current] + (extra_args or [])
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    code = run_diff(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(baseline_file, current_file):
    code, _, _ = _run(baseline_file, current_file)
    assert code == 0


def test_summary_contains_added_count(baseline_file, current_file):
    _, out, _ = _run(baseline_file, current_file)
    assert "Added  : 1" in out


def test_summary_contains_removed_count(baseline_file, current_file):
    _, out, _ = _run(baseline_file, current_file)
    assert "Removed: 1" in out


def test_show_diff_flag_outputs_prefixed_lines(baseline_file, current_file):
    _, out, _ = _run(baseline_file, current_file, ["--show-diff"])
    assert any(l.startswith("+ ") for l in out.splitlines())
    assert any(l.startswith("- ") for l in out.splitlines())


def test_added_only_flag(baseline_file, current_file):
    _, out, _ = _run(baseline_file, current_file, ["--added-only"])
    assert "delta" in out
    assert "alpha" not in out


def test_removed_only_flag(baseline_file, current_file):
    _, out, _ = _run(baseline_file, current_file, ["--removed-only"])
    assert "alpha" in out
    assert "delta" not in out


def test_missing_baseline_returns_one(tmp_path, current_file):
    code, _, err = _run(str(tmp_path / "no.log"), current_file)
    assert code == 1
    assert "error" in err


def test_missing_current_returns_one(baseline_file, tmp_path):
    code, _, err = _run(baseline_file, str(tmp_path / "no.log"))
    assert code == 1
