"""Tests for logslice.line_filter."""

from datetime import datetime, timezone

import pytest

from logslice.line_filter import filter_lines_by_keyword, filter_lines_by_range


ISO_LINES = [
    "2024-01-10T08:00:00Z INFO  service started",
    "2024-01-10T09:00:00Z DEBUG request received",
    "2024-01-10T10:00:00Z ERROR something went wrong",
    "2024-01-10T11:00:00Z INFO  service stopped",
]

NO_TS_LINE = "    at com.example.Foo.bar(Foo.java:42)"


def _dt(hour: int) -> datetime:
    return datetime(2024, 1, 10, hour, 0, 0, tzinfo=timezone.utc)


class TestFilterLinesByRange:
    def test_no_bounds_yields_all_lines(self):
        result = list(filter_lines_by_range(ISO_LINES))
        assert result == ISO_LINES

    def test_start_bound_excludes_earlier_lines(self):
        result = list(filter_lines_by_range(ISO_LINES, start=_dt(9)))
        assert result[0].startswith("2024-01-10T09")
        assert len(result) == 3

    def test_end_bound_excludes_later_lines(self):
        result = list(filter_lines_by_range(ISO_LINES, end=_dt(9)))
        assert len(result) == 2
        assert all("ERROR" not in l and "stopped" not in l for l in result)

    def test_both_bounds_slice_middle(self):
        result = list(filter_lines_by_range(ISO_LINES, start=_dt(9), end=_dt(10)))
        assert len(result) == 2
        assert "DEBUG" in result[0]
        assert "ERROR" in result[1]

    def test_exact_boundary_is_inclusive(self):
        result = list(filter_lines_by_range(ISO_LINES, start=_dt(8), end=_dt(8)))
        assert len(result) == 1
        assert "started" in result[0]

    def test_lines_without_timestamp_are_always_yielded(self):
        mixed = [ISO_LINES[2], NO_TS_LINE, ISO_LINES[3]]
        # Filter to only the 10:00 entry; the no-ts line should still appear
        result = list(filter_lines_by_range(mixed, start=_dt(10), end=_dt(10)))
        assert NO_TS_LINE in result
        assert len(result) == 2

    def test_empty_input_yields_nothing(self):
        assert list(filter_lines_by_range([])) == []


class TestFilterLinesByKeyword:
    def test_matches_case_insensitive_by_default(self):
        result = list(filter_lines_by_keyword(ISO_LINES, "error"))
        assert len(result) == 1
        assert "ERROR" in result[0]

    def test_case_sensitive_no_match(self):
        result = list(filter_lines_by_keyword(ISO_LINES, "error", case_sensitive=True))
        assert result == []

    def test_case_sensitive_match(self):
        result = list(filter_lines_by_keyword(ISO_LINES, "ERROR", case_sensitive=True))
        assert len(result) == 1

    def test_keyword_not_present_yields_nothing(self):
        result = list(filter_lines_by_keyword(ISO_LINES, "critical"))
        assert result == []

    def test_keyword_matches_multiple_lines(self):
        result = list(filter_lines_by_keyword(ISO_LINES, "info"))
        assert len(result) == 2

    def test_empty_keyword_matches_all_lines(self):
        result = list(filter_lines_by_keyword(ISO_LINES, ""))
        assert result == ISO_LINES
