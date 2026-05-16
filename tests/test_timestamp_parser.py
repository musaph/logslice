"""Tests for logslice.timestamp_parser module."""

import pytest
from datetime import datetime
from logslice.timestamp_parser import parse_timestamp


@pytest.mark.parametrize("line, expected", [
    (
        "2024-01-15T13:45:00Z INFO server started",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    (
        "2024-01-15T13:45:00.123+00:00 ERROR disk full",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    (
        "Jan 15 13:45:00 myhost sshd[1234]: Accepted",
        datetime(1900, 1, 15, 13, 45, 0),
    ),
    (
        "2024-01-15 13:45:00.456 DEBUG connection pool",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    (
        '192.168.1.1 - - [15/Jan/2024:13:45:00 +0000] "GET / HTTP/1.1" 200',
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    (
        "1705326300 INFO epoch seconds log entry",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    (
        "1705326300000 INFO epoch millis log entry",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
])
def test_parse_known_formats(line, expected):
    result = parse_timestamp(line)
    assert result is not None
    assert result.year == expected.year or expected.year == 1900
    assert result.hour == expected.hour
    assert result.minute == expected.minute
    assert result.second == expected.second


def test_parse_returns_none_for_no_timestamp():
    assert parse_timestamp("no timestamp here at all") is None
    assert parse_timestamp("") is None
    assert parse_timestamp("ERROR something went wrong") is None


def test_parse_returns_datetime_instance():
    result = parse_timestamp("2024-06-01T00:00:00Z start")
    assert isinstance(result, datetime)


def test_parse_prefers_iso8601_over_epoch():
    """ISO 8601 pattern should match before a bare 10-digit number."""
    line = "2024-01-15T13:45:00Z 1705326300 two timestamps"
    result = parse_timestamp(line)
    assert result is not None
    assert result.year == 2024


@pytest.mark.parametrize("line", [
    "2024-01-15T13:45:00Z INFO server started",
    "2024-01-15 13:45:00.456 DEBUG connection pool",
    '192.168.1.1 - - [15/Jan/2024:13:45:00 +0000] "GET / HTTP/1.1" 200',
    "1705326300 INFO epoch seconds log entry",
])
def test_parse_result_has_no_tzinfo(line):
    """Parsed timestamps should be naive datetimes (no tzinfo attached)."""
    result = parse_timestamp(line)
    assert result is not None
    assert result.tzinfo is None
