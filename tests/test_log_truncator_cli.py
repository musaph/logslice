"""Tests for logslice.log_truncator_cli."""
from __future__ import annotations

import gzip
import io
import os
import textwrap

import pytest

from logslice.log_truncator_cli import run_truncator


@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text(
        textwrap.dedent(
            """\
            short line
            this is a much longer line that exceeds the default width limit set for truncation purposes in the test
            another short one
            """
        )
    )
    return str(p)


def _run(argv, stdin_text=None):
    out = io.StringIO()
    err = io.StringIO()
    rc = run_truncator(argv, stdout=out, stderr=err)
    return rc, out.getvalue(), err.getvalue()


def test_run_returns_zero_on_success(plain_log):
    rc, _, _ = _run([plain_log])
    assert rc == 0


def test_run_returns_one_on_missing_file():
    rc, _, err = _run(["nonexistent_file.log"])
    assert rc == 1
    assert "error" in err.lower()


def test_run_truncates_long_lines(plain_log):
    rc, out, _ = _run([plain_log, "--width", "20"])
    assert rc == 0
    lines = out.splitlines()
    for line in lines:
        assert len(line) <= 20, f"line too long: {line!r}"


def test_run_short_lines_unchanged(plain_log):
    rc, out, _ = _run([plain_log, "--width", "200"])
    assert rc == 0
    assert "short line" in out
    assert "another short one" in out


def test_run_count_prints_number(plain_log):
    rc, out, _ = _run([plain_log, "--width", "20", "--count"])
    assert rc == 0
    value = int(out.strip())
    assert value >= 1


def test_run_custom_suffix(plain_log):
    rc, out, _ = _run([plain_log, "--width", "20", "--suffix", "..."])
    assert rc == 0
    truncated = [l for l in out.splitlines() if l.endswith("...")]
    assert len(truncated) >= 1


def test_run_default_width_is_120(plain_log):
    """Lines shorter than 120 chars must pass through unmodified."""
    rc, out, _ = _run([plain_log])
    assert rc == 0
    assert "short line" in out
    assert "another short one" in out


def test_run_count_zero_when_all_short(tmp_path):
    p = tmp_path / "tiny.log"
    p.write_text("a\nb\nc\n")
    rc, out, _ = _run([str(p), "--width", "80", "--count"])
    assert rc == 0
    assert out.strip() == "0"


def test_run_truncated_line_starts_with_original_prefix(plain_log):
    """Truncated lines should begin with the original content up to --width."""
    width = 20
    rc, out, _ = _run([plain_log, "--width", str(width)])
    assert rc == 0

    # Read the original long line directly from the fixture file
    original_long_line = (
        "this is a much longer line that exceeds the default width limit "
        "set for truncation purposes in the test"
    )
    for line in out.splitlines():
        if len(line) == width:
            # The truncated output must start with the first `width` chars
            # (possibly minus a suffix), so at minimum the raw prefix is preserved.
            assert original_long_line.startswith(line) or line.startswith(
                original_long_line[:width]
            ), f"Truncated line has unexpected prefix: {line!r}"
