"""Tests for logslice.deduplicator."""
import pytest
from logslice.deduplicator import deduplicate, count_duplicates


LINES = [
    "2024-01-01 INFO  starting up",
    "2024-01-01 INFO  starting up",
    "2024-01-02 DEBUG received request",
    "2024-01-03 INFO  starting up",
    "2024-01-04 ERROR something failed",
    "2024-01-04 ERROR something failed",
]


def _collect(it):
    return list(it)


# ---------------------------------------------------------------------------
# deduplicate – exact matching
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    assert _collect(deduplicate([])) == []


def test_all_unique_lines_pass_through():
    unique = ["line one", "line two", "line three"]
    assert _collect(deduplicate(unique)) == unique


def test_exact_duplicates_removed():
    lines = ["hello", "world", "hello"]
    assert _collect(deduplicate(lines)) == ["hello", "world"]


def test_first_occurrence_is_kept():
    lines = ["a", "b", "a", "c"]
    result = _collect(deduplicate(lines))
    assert result == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# deduplicate – ignore_timestamps
# ---------------------------------------------------------------------------

def test_ignore_timestamps_treats_same_message_as_duplicate():
    # timestamp occupies first 10 chars
    lines = [
        "2024-01-01 INFO  starting up",
        "2024-01-03 INFO  starting up",
    ]
    result = _collect(deduplicate(lines, ignore_timestamps=True, timestamp_col_end=10))
    assert len(result) == 1
    assert result[0] == lines[0]


def test_ignore_timestamps_false_keeps_both():
    lines = [
        "2024-01-01 INFO  starting up",
        "2024-01-03 INFO  starting up",
    ]
    result = _collect(deduplicate(lines, ignore_timestamps=False))
    assert len(result) == 2


def test_full_dedup_with_mixed_lines():
    result = _collect(deduplicate(LINES, ignore_timestamps=True, timestamp_col_end=10))
    messages = {line[10:].strip() for line in result}
    assert messages == {"INFO  starting up", "DEBUG received request", "ERROR something failed"}


# ---------------------------------------------------------------------------
# deduplicate – max_cache
# ---------------------------------------------------------------------------

def test_max_cache_evicts_old_entries():
    # With cache size 1, each new unique line evicts the previous key.
    # So a repeated line after one other unique line is NOT filtered.
    lines = ["a", "b", "a"]
    result = _collect(deduplicate(lines, max_cache=1))
    # "a" seen, then "b" evicts "a", then "a" is treated as new
    assert result == ["a", "b", "a"]


def test_max_cache_none_is_unlimited():
    lines = ["x", "y", "z", "x", "y"]
    assert _collect(deduplicate(lines, max_cache=None)) == ["x", "y", "z"]


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

def test_count_duplicates_no_dupes():
    assert count_duplicates(["a", "b", "c"]) == 0


def test_count_duplicates_with_dupes():
    assert count_duplicates(["a", "a", "b", "b", "b"]) == 3


def test_count_duplicates_ignore_timestamps():
    lines = [
        "2024-01-01 msg",
        "2024-01-02 msg",
        "2024-01-03 other",
    ]
    assert count_duplicates(lines, ignore_timestamps=True, timestamp_col_end=10) == 1
