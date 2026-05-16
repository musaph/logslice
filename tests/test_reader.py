"""Tests for logslice.reader."""

import gzip
import io
import os
import tempfile

import pytest

from logslice.reader import LogReadError, iter_lines, read_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp_plain(lines: list, suffix: str = ".log") -> str:
    """Write *lines* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def _tmp_gzip(lines: list) -> str:
    """Write *lines* to a gzip-compressed temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".gz")
    os.close(fd)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Plain file tests
# ---------------------------------------------------------------------------

def test_read_plain_file_returns_all_lines():
    path = _tmp_plain(["line one", "line two", "line three"])
    try:
        result = read_lines(path)
        assert result == ["line one", "line two", "line three"]
    finally:
        os.unlink(path)


def test_strip_newlines_false_preserves_newline():
    path = _tmp_plain(["hello", "world"])
    try:
        result = read_lines(path, strip_newlines=False)
        assert all(line.endswith("\n") for line in result)
    finally:
        os.unlink(path)


def test_iter_lines_yields_strings():
    path = _tmp_plain(["a", "b"])
    try:
        for line in iter_lines(path):
            assert isinstance(line, str)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Gzip file tests
# ---------------------------------------------------------------------------

def test_read_gzip_file_returns_all_lines():
    path = _tmp_gzip(["compressed one", "compressed two"])
    try:
        result = read_lines(path)
        assert result == ["compressed one", "compressed two"]
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# File-like object tests
# ---------------------------------------------------------------------------

def test_iter_lines_accepts_file_like_object():
    fh = io.StringIO("alpha\nbeta\ngamma\n")
    result = read_lines(fh)
    assert result == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

def test_missing_file_raises_log_read_error():
    with pytest.raises(LogReadError, match="File not found"):
        read_lines("/nonexistent/path/to/file.log")


def test_directory_path_raises_log_read_error():
    with pytest.raises(LogReadError, match="Not a regular file"):
        read_lines(tempfile.gettempdir())
