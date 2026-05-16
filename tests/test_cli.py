"""Tests for the CLI interface."""

import gzip
import os
import textwrap
from pathlib import Path

import pytest

from logslice.cli import run, build_parser, _parse_dt
from datetime import datetime
import argparse


@pytest.fixture()
def plain_log(tmp_path):
    log = tmp_path / "app.log"
    log.write_text(
        "2024-01-10T08:00:00 INFO  startup\n"
        "2024-01-10T09:00:00 DEBUG debug message\n"
        "2024-01-10T10:00:00 ERROR something failed\n"
        "2024-01-10T11:00:00 INFO  shutdown\n"
    )
    return str(log)


@pytest.fixture()
def gz_log(tmp_path):
    log = tmp_path / "app.log.gz"
    content = b"2024-01-10T08:00:00 INFO  startup\n2024-01-10T09:00:00 ERROR fail\n"
    with gzip.open(log, "wb") as fh:
        fh.write(content)
    return str(log)


def test_run_returns_zero_on_success(plain_log):
    assert run([plain_log]) == 0


def test_run_returns_one_on_missing_file():
    assert run(["nonexistent_file_xyz.log"]) == 1


def test_run_with_keyword_filter(plain_log, capsys):
    run([plain_log, "--keyword", "ERROR"])
    out = capsys.readouterr().out
    assert "ERROR" in out
    assert "startup" not in out


def test_run_with_ignore_case(plain_log, capsys):
    run([plain_log, "--keyword", "error", "--ignore-case"])
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_run_with_line_numbers(plain_log, capsys):
    run([plain_log, "--line-numbers"])
    out = capsys.readouterr().out
    assert out.startswith("1:")


def test_run_with_start_filter(plain_log, capsys):
    run([plain_log, "--start", "2024-01-10T09:30:00"])
    out = capsys.readouterr().out
    assert "startup" not in out
    assert "debug message" not in out
    assert "something failed" in out


def test_run_with_end_filter(plain_log, capsys):
    run([plain_log, "--end", "2024-01-10T08:30:00"])
    out = capsys.readouterr().out
    assert "startup" in out
    assert "shutdown" not in out


def test_run_gz_file(gz_log, capsys):
    assert run([gz_log]) == 0
    out = capsys.readouterr().out
    assert "startup" in out


def test_parse_dt_iso():
    assert _parse_dt("2024-03-15T12:30:00") == datetime(2024, 3, 15, 12, 30, 0)


def test_parse_dt_date_only():
    assert _parse_dt("2024-03-15") == datetime(2024, 3, 15)


def test_parse_dt_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_dt("not-a-date")


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["somefile.log"])
    assert args.file == "somefile.log"
    assert args.start is None
    assert args.end is None
    assert args.keyword is None
    assert not args.line_numbers
    assert not args.highlight
