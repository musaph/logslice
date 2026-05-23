"""Tests for logslice.log_tailer."""

from __future__ import annotations

import os
import tempfile
import threading
import time

import pytest

from logslice.log_tailer import tail_file, tail_lines, DEFAULT_POLL_INTERVAL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_lines(path: str, lines: list[str], delay: float = 0.05) -> None:
    """Append *lines* to *path* with a small delay, used from a background thread."""
    time.sleep(delay)
    with open(path, "a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line + "\n")
            fh.flush()
            time.sleep(0.01)


# ---------------------------------------------------------------------------
# tail_lines
# ---------------------------------------------------------------------------

class TestTailLines:
    def _tmp(self, lines: list[str]) -> str:
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return path

    def test_returns_last_n_lines(self):
        path = self._tmp(["a", "b", "c", "d", "e"])
        assert tail_lines(path, n=3) == ["c", "d", "e"]

    def test_n_larger_than_file_returns_all(self):
        path = self._tmp(["x", "y"])
        assert tail_lines(path, n=100) == ["x", "y"]

    def test_n_zero_returns_empty(self):
        path = self._tmp(["x", "y"])
        assert tail_lines(path, n=0) == []

    def test_n_default_is_ten(self):
        path = self._tmp([str(i) for i in range(20)])
        result = tail_lines(path)
        assert len(result) == 10
        assert result[-1] == "19"

    def test_strips_newlines(self):
        path = self._tmp(["hello"])
        result = tail_lines(path, n=1)
        assert result == ["hello"]


# ---------------------------------------------------------------------------
# tail_file
# ---------------------------------------------------------------------------

class TestTailFile:
    def _tmp_empty(self) -> str:
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        return path

    def _collect_n(self, path: str, n: int, **kwargs) -> list[str]:
        """Collect exactly *n* lines from tail_file then stop."""
        return list(tail_file(path, max_lines=n, poll_interval=0.05, **kwargs))

    def test_yields_new_lines_appended_to_file(self):
        path = self._tmp_empty()
        new_lines = ["line1", "line2", "line3"]
        t = threading.Thread(target=_write_lines, args=(path, new_lines))
        t.start()
        result = self._collect_n(path, 3)
        t.join(timeout=5)
        assert result == new_lines

    def test_max_lines_stops_iteration(self):
        path = self._tmp_empty()
        t = threading.Thread(target=_write_lines, args=(path, ["a", "b", "c", "d", "e"]))
        t.start()
        result = self._collect_n(path, 2)
        t.join(timeout=5)
        assert len(result) == 2

    def test_predicate_filters_lines(self):
        path = self._tmp_empty()
        lines = ["ERROR foo", "INFO bar", "ERROR baz"]
        t = threading.Thread(target=_write_lines, args=(path, lines))
        t.start()
        result = self._collect_n(path, 2, predicate=lambda l: l.startswith("ERROR"))
        t.join(timeout=5)
        assert result == ["ERROR foo", "ERROR baz"]

    def test_default_poll_interval_is_float(self):
        assert isinstance(DEFAULT_POLL_INTERVAL, float)
        assert DEFAULT_POLL_INTERVAL > 0
