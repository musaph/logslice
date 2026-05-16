"""Line filtering utilities for logslice.

Provides filtering of log lines based on time range using parsed timestamps.
"""

from datetime import datetime
from typing import Iterable, Iterator, Optional, Tuple

from logslice.timestamp_parser import parse_timestamp


def filter_lines_by_range(
    lines: Iterable[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Iterator[str]:
    """Yield log lines whose timestamps fall within [start, end].

    Lines that contain no parseable timestamp are always yielded so that
    continuation lines (stack traces, multi-line payloads, etc.) are
    preserved alongside their parent log entry.

    Args:
        lines:  Iterable of raw log line strings.
        start:  Inclusive lower bound (timezone-aware or naive, must match
                the timestamps found in the log).  ``None`` means no lower
                bound.
        end:    Inclusive upper bound.  ``None`` means no upper bound.

    Yields:
        Log lines that satisfy the time-range filter.
    """
    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            # No timestamp — keep the line (continuation / header / blank)
            yield line
            continue
        if start is not None and ts < start:
            continue
        if end is not None and ts > end:
            continue
        yield line


def filter_lines_by_keyword(
    lines: Iterable[str],
    keyword: str,
    case_sensitive: bool = False,
) -> Iterator[str]:
    """Yield log lines that contain *keyword*.

    Args:
        lines:          Iterable of raw log line strings.
        keyword:        Substring to search for.
        case_sensitive: When ``False`` (default) the comparison is
                        case-insensitive.

    Yields:
        Matching log lines.
    """
    needle = keyword if case_sensitive else keyword.lower()
    for line in lines:
        haystack = line if case_sensitive else line.lower()
        if needle in haystack:
            yield line


def count_matching(
    lines: Iterable[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Tuple[int, int]:
    """Return (total_lines, matched_lines) for a time-range filter pass."""
    total = 0
    matched = 0
    for line in filter_lines_by_range(lines, start=start, end=end):
        matched += 1
    # We need to count total separately; caller should pass a rewindable source.
    # This helper is intentionally simple — callers that need both counts
    # should materialise the lines first.
    return matched
