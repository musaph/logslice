"""Tests for logslice.session_splitter."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from logslice.session_splitter import (
    Session,
    format_session_summary,
    split_into_sessions,
)


def _line(ts: str, msg: str = "event") -> str:
    return f"{ts} {msg}"


BASE = "2024-01-15T10:00:"


def _ts(offset_seconds: int) -> str:
    minutes, secs = divmod(offset_seconds, 60)
    return f"2024-01-15T10:{minutes:02d}:{secs:02d}"


# ---------------------------------------------------------------------------
# split_into_sessions
# ---------------------------------------------------------------------------


def test_empty_input_yields_nothing():
    sessions = list(split_into_sessions([]))
    assert sessions == []


def test_single_line_yields_one_session():
    lines = [_line(_ts(0))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    assert len(sessions) == 1
    assert sessions[0].line_count == 1


def test_lines_within_gap_form_one_session():
    lines = [_line(_ts(0)), _line(_ts(30)), _line(_ts(59))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    assert len(sessions) == 1
    assert sessions[0].line_count == 3


def test_gap_exceeding_threshold_splits_sessions():
    lines = [_line(_ts(0)), _line(_ts(30)), _line(_ts(200))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    assert len(sessions) == 2
    assert sessions[0].line_count == 2
    assert sessions[1].line_count == 1


def test_multiple_gaps_produce_multiple_sessions():
    lines = [
        _line(_ts(0)),
        _line(_ts(400)),
        _line(_ts(800)),
    ]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    assert len(sessions) == 3


def test_lines_without_timestamp_appended_to_current_session():
    lines = [_line(_ts(0)), "no timestamp here", _line(_ts(10))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    assert len(sessions) == 1
    assert sessions[0].line_count == 3


def test_session_start_and_end_populated():
    lines = [_line(_ts(0)), _line(_ts(30))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    s = sessions[0]
    assert s.start is not None
    assert s.end is not None
    assert s.end >= s.start


def test_span_seconds_correct():
    lines = [_line(_ts(0)), _line(_ts(60))]
    sessions = list(split_into_sessions(lines, gap_seconds=120))
    assert sessions[0].span_seconds == pytest.approx(60.0)


def test_span_seconds_none_when_no_timestamps():
    sessions = list(split_into_sessions(["plain line"], gap_seconds=60))
    assert sessions[0].span_seconds is None


def test_all_lines_preserved_across_sessions():
    lines = [_line(_ts(0)), _line(_ts(400)), _line(_ts(401))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    all_lines = [l for s in sessions for l in s.lines]
    assert all_lines == lines


# ---------------------------------------------------------------------------
# format_session_summary
# ---------------------------------------------------------------------------


def test_format_empty_sessions():
    result = format_session_summary([])
    assert result == "No sessions found."


def test_format_shows_session_numbers():
    lines = [_line(_ts(0)), _line(_ts(400))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    summary = format_session_summary(sessions)
    assert "Session   1" in summary
    assert "Session   2" in summary


def test_format_shows_line_counts():
    lines = [_line(_ts(0)), _line(_ts(10)), _line(_ts(500))]
    sessions = list(split_into_sessions(lines, gap_seconds=60))
    summary = format_session_summary(sessions)
    assert "lines=2" in summary
    assert "lines=1" in summary
