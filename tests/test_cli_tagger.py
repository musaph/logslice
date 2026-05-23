"""Tests for logslice.cli_tagger."""
import io
import json
import os
import tempfile

import pytest

from logslice.cli_tagger import build_tagger_parser, run_tagger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_plain(lines, suffix=".log"):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix,
                                     delete=False, encoding="utf-8")
    tmp.write("\n".join(lines) + "\n")
    tmp.flush()
    tmp.close()
    return tmp.name


def _run(argv, out=None, err=None):
    if out is None:
        out = io.StringIO()
    if err is None:
        err = io.StringIO()
    parser = build_tagger_parser()
    args = parser.parse_args(argv)
    code = run_tagger(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


@pytest.fixture()
def plain_log():
    path = _write_plain(["ERROR disk full", "INFO all good", "WARN low memory"])
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_returns_zero_on_success(plain_log):
    code, _, _ = _run([plain_log, "--rule", "err:ERROR"])
    assert code == 0


def test_run_returns_one_on_missing_file():
    code, _, err = _run(["/no/such/file.log", "--rule", "err:ERROR"])
    assert code == 1
    assert "error" in err.lower()


def test_run_tagged_only_filters_untagged(plain_log):
    code, out, _ = _run([plain_log, "--rule", "err:ERROR", "--tagged-only"])
    assert code == 0
    lines = [l for l in out.splitlines() if l]
    assert len(lines) == 1
    assert "ERROR" in lines[0]


def test_run_formats_tagged_lines(plain_log):
    code, out, _ = _run([plain_log, "--rule", "err:ERROR"])
    assert code == 0
    tagged = [l for l in out.splitlines() if l.startswith("[err]")]
    assert len(tagged) == 1


def test_run_multiple_rules(plain_log):
    code, out, _ = _run([
        plain_log,
        "--rule", "err:ERROR",
        "--rule", "warn:WARN",
        "--tagged-only",
    ])
    assert code == 0
    lines = [l for l in out.splitlines() if l]
    assert len(lines) == 2


def test_run_stats_writes_to_stderr(plain_log):
    code, out, err = _run([plain_log, "--rule", "err:ERROR", "--stats"])
    assert code == 0
    assert "err: 1" in err


def test_run_rules_file(plain_log):
    rules = [{"tag": "warn", "pattern": "WARN"}]
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False, encoding="utf-8")
    json.dump(rules, tmp)
    tmp.close()
    try:
        code, out, _ = _run([plain_log, "--rules-file", tmp.name, "--tagged-only"])
        assert code == 0
        lines = [l for l in out.splitlines() if l]
        assert any("WARN" in l for l in lines)
    finally:
        os.unlink(tmp.name)


def test_run_invalid_rule_format_returns_one(plain_log):
    code, _, err = _run([plain_log, "--rule", "bad-rule-no-colon"])
    assert code == 1
    assert "error" in err.lower()


def test_run_no_rules_no_tags_all_lines_output(plain_log):
    code, out, _ = _run([plain_log])
    assert code == 0
    assert len(out.splitlines()) == 3
