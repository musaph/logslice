"""Tests for logslice.log_differ."""
import pytest
from logslice.log_differ import (
    DiffResult,
    diff_logs,
    format_diff,
    iter_diff_lines,
)


BASELINE = ["alpha\n", "beta\n", "gamma\n"]
CURRENT = ["beta\n", "gamma\n", "delta\n"]


def test_added_lines_detected():
    result = diff_logs(BASELINE, CURRENT)
    assert "delta" in result.added


def test_removed_lines_detected():
    result = diff_logs(BASELINE, CURRENT)
    assert "alpha" in result.removed


def test_common_lines_detected():
    result = diff_logs(BASELINE, CURRENT)
    assert "beta" in result.common
    assert "gamma" in result.common


def test_total_added_count():
    result = diff_logs(BASELINE, CURRENT)
    assert result.total_added == 1


def test_total_removed_count():
    result = diff_logs(BASELINE, CURRENT)
    assert result.total_removed == 1


def test_total_common_count():
    result = diff_logs(BASELINE, CURRENT)
    assert result.total_common == 2


def test_identical_streams_no_diff():
    result = diff_logs(BASELINE, BASELINE)
    assert result.total_added == 0
    assert result.total_removed == 0
    assert result.total_common == 3


def test_empty_baseline_all_added():
    result = diff_logs([], CURRENT)
    assert result.total_added == 3
    assert result.total_removed == 0


def test_empty_current_all_removed():
    result = diff_logs(BASELINE, [])
    assert result.total_removed == 3
    assert result.total_added == 0


def test_blank_lines_ignored_by_default():
    result = diff_logs(["\n", "alpha\n"], ["alpha\n", "\n"])
    assert result.total_common == 1
    assert result.total_added == 0
    assert result.total_removed == 0


def test_strip_false_preserves_newlines():
    result = diff_logs(["alpha\n"], ["alpha"], strip=False)
    # With strip=False newlines are kept verbatim so they differ
    assert result.total_added == 1
    assert result.total_removed == 1


def test_iter_diff_lines_prefixes():
    result = diff_logs(["old"], ["new"])
    lines = list(iter_diff_lines(result))
    assert any(l.startswith("- ") for l in lines)
    assert any(l.startswith("+ ") for l in lines)


def test_format_diff_contains_counts():
    result = diff_logs(BASELINE, CURRENT)
    summary = format_diff(result)
    assert "Added  : 1" in summary
    assert "Removed: 1" in summary
    assert "Common : 2" in summary


def test_diff_result_is_dataclass():
    r = DiffResult(added=["x"], removed=["y"], common=["z"])
    assert r.total_added == 1
    assert r.total_removed == 1
    assert r.total_common == 1
