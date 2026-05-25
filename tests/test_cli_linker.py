"""Tests for logslice.cli_linker."""
from __future__ import annotations

import json
import os
from io import StringIO
from typing import List

import pytest

from logslice.cli_linker import build_linker_parser, run_linker


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_a(tmp_path):
    p = tmp_path / "a.log"
    p.write_text(
        json.dumps({"trace_id": "t1", "msg": "request"}) + "\n"
        + json.dumps({"trace_id": "t2", "msg": "other"}) + "\n"
    )
    return str(p)


@pytest.fixture()
def log_b(tmp_path):
    p = tmp_path / "b.log"
    p.write_text(
        json.dumps({"trace_id": "t1", "msg": "response"}) + "\n"
        + "plain unstructured line\n"
    )
    return str(p)


def _run(args: List[str]):
    parser = build_linker_parser()
    ns = parser.parse_args(args)
    out, err = StringIO(), StringIO()
    code = run_linker(ns, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_run_returns_zero_on_success(log_a):
    code, _, _ = _run([log_a, "--field", "trace_id"])
    assert code == 0


def test_run_returns_one_on_missing_file(tmp_path):
    code, _, err = _run([str(tmp_path / "ghost.log"), "--field", "trace_id"])
    assert code == 1
    assert "error" in err.lower()


def test_run_groups_matching_lines(log_a, log_b):
    code, out, _ = _run([log_a, log_b, "--field", "trace_id"])
    assert code == 0
    assert "t1" in out


def test_run_shows_source_labels(log_a, log_b):
    _, out, _ = _run([log_a, log_b, "--field", "trace_id"])
    assert "a.log" in out or "b.log" in out


def test_run_unmatched_hidden_by_default(log_a, log_b):
    _, out, _ = _run([log_a, log_b, "--field", "trace_id"])
    assert "unmatched" not in out


def test_run_show_unmatched_flag(log_a, log_b):
    _, out, _ = _run([log_a, log_b, "--field", "trace_id", "--show-unmatched"])
    assert "unmatched" in out


def test_run_min_group_size_filters_small_groups(log_a, log_b):
    # t2 only has 1 line; with --min-group-size 2 it should be hidden
    _, out, _ = _run([log_a, log_b, "--field", "trace_id", "--min-group-size", "2"])
    assert "t2" not in out
    assert "t1" in out


def test_run_case_insensitive_default(tmp_path):
    p = tmp_path / "mixed.log"
    p.write_text(json.dumps({"TRACE_ID": "abc", "msg": "hi"}) + "\n")
    code, out, _ = _run([str(p), "--field", "trace_id"])
    assert code == 0
    assert "abc" in out
