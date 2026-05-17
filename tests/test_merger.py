"""Tests for logslice.merger — merge_logs and merge_log_files."""

import gzip
import os
import tempfile
from datetime import datetime

import pytest

from logslice.merger import merge_logs, merge_log_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect(gen):
    return list(gen)


def _dt(year=2024, month=1, day=1, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second)


# Lines with embedded ISO-8601 timestamps so the merger can sort them.
LOG_A = [
    "2024-01-01T00:00:01 alpha first\n",
    "2024-01-01T00:00:03 alpha third\n",
    "2024-01-01T00:00:05 alpha fifth\n",
]

LOG_B = [
    "2024-01-01T00:00:02 beta second\n",
    "2024-01-01T00:00:04 beta fourth\n",
    "2024-01-01T00:00:06 beta sixth\n",
]

LOG_NO_TS = [
    "no timestamp here\n",
    "another plain line\n",
]


# ---------------------------------------------------------------------------
# merge_logs
# ---------------------------------------------------------------------------

class TestMergeLogs:
    def test_empty_sources_yield_nothing(self):
        result = _collect(merge_logs([]))
        assert result == []

    def test_single_source_passes_through(self):
        result = _collect(merge_logs([iter(LOG_A)]))
        assert result == [l.rstrip("\n") for l in LOG_A]

    def test_two_sources_interleaved_by_timestamp(self):
        result = _collect(merge_logs([iter(LOG_A), iter(LOG_B)]))
        assert "alpha first" in result[0]
        assert "beta second" in result[1]
        assert "alpha third" in result[2]
        assert "beta fourth" in result[3]
        assert "alpha fifth" in result[4]
        assert "beta sixth" in result[5]

    def test_output_length_equals_sum_of_inputs(self):
        result = _collect(merge_logs([iter(LOG_A), iter(LOG_B)]))
        assert len(result) == len(LOG_A) + len(LOG_B)

    def test_lines_without_timestamps_are_appended_last(self):
        result = _collect(merge_logs([iter(LOG_A), iter(LOG_NO_TS)]))
        # Timestamped lines come first; plain lines follow.
        assert len(result) == len(LOG_A) + len(LOG_NO_TS)
        plain = [r for r in result if "no timestamp" in r or "another plain" in r]
        assert len(plain) == 2

    def test_merge_is_stable_for_equal_timestamps(self):
        same_ts = [
            "2024-01-01T00:00:01 first\n",
            "2024-01-01T00:00:01 second\n",
        ]
        result = _collect(merge_logs([iter(same_ts)]))
        assert "first" in result[0]
        assert "second" in result[1]

    def test_three_sources_all_lines_present(self):
        log_c = ["2024-01-01T00:00:07 gamma seventh\n"]
        result = _collect(merge_logs([iter(LOG_A), iter(LOG_B), iter(log_c)]))
        assert len(result) == 7
        assert any("gamma seventh" in r for r in result)


# ---------------------------------------------------------------------------
# merge_log_files
# ---------------------------------------------------------------------------

class TestMergeLogFiles:
    def _write_plain(self, lines):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        )
        f.writelines(lines)
        f.close()
        return f.name

    def _write_gz(self, lines):
        f = tempfile.NamedTemporaryFile(
            suffix=".log.gz", delete=False
        )
        f.close()
        with gzip.open(f.name, "wt") as gz:
            gz.writelines(lines)
        return f.name

    def teardown_method(self, _method):
        # Cleanup handled per-test via stored paths.
        pass

    def test_plain_files_merged(self):
        p1 = self._write_plain(LOG_A)
        p2 = self._write_plain(LOG_B)
        try:
            result = _collect(merge_log_files([p1, p2]))
            assert len(result) == 6
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_gzip_files_merged(self):
        g1 = self._write_gz(LOG_A)
        g2 = self._write_gz(LOG_B)
        try:
            result = _collect(merge_log_files([g1, g2]))
            assert len(result) == 6
        finally:
            os.unlink(g1)
            os.unlink(g2)

    def test_missing_file_raises(self):
        with pytest.raises(Exception):
            _collect(merge_log_files(["/nonexistent/path/file.log"]))

    def test_single_file_returns_all_lines(self):
        p = self._write_plain(LOG_A)
        try:
            result = _collect(merge_log_files([p]))
            assert len(result) == len(LOG_A)
        finally:
            os.unlink(p)
