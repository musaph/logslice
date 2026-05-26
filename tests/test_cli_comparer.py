"""Tests for logslice.cli_comparer."""
import io
import textwrap
from pathlib import Path

import pytest

from logslice.cli_comparer import build_comparer_parser, run_comparer


@pytest.fixture()
def log_a(tmp_path: Path) -> Path:
    p = tmp_path / "a.log"
    p.write_text("alpha\nbeta\ngamma\n")
    return p


@pytest.fixture()
def log_b(tmp_path: Path) -> Path:
    p = tmp_path / "b.log"
    p.write_text("beta\ngamma\ndelta\n")
    return p


def _run(args_list, **kwargs):
    parser = build_comparer_parser()
    args = parser.parse_args(args_list)
    out = io.StringIO()
    err = io.StringIO()
    code = run_comparer(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(log_a, log_b):
    code, _, _ = _run([str(log_a), str(log_b)])
    assert code == 0


def test_run_returns_one_on_missing_file(log_a, tmp_path):
    missing = str(tmp_path / "no.log")
    code, _, err = _run([str(log_a), missing])
    assert code == 1
    assert "error" in err.lower()


def test_summary_output_contains_jaccard(log_a, log_b):
    _, out, _ = _run([str(log_a), str(log_b)])
    assert "Jaccard" in out


def test_summary_output_contains_similarity(log_a, log_b):
    _, out, _ = _run([str(log_a), str(log_b)])
    assert "Similarity" in out


def test_only_a_prints_exclusive_lines(log_a, log_b):
    _, out, _ = _run([str(log_a), str(log_b), "--only-a"])
    assert "alpha" in out
    assert "delta" not in out


def test_only_b_prints_exclusive_lines(log_a, log_b):
    _, out, _ = _run([str(log_a), str(log_b), "--only-b"])
    assert "delta" in out
    assert "alpha" not in out


def test_identical_files_show_100_percent(tmp_path):
    p = tmp_path / "same.log"
    p.write_text("line1\nline2\n")
    _, out, _ = _run([str(p), str(p)])
    assert "100.00%" in out
