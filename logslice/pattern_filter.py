"""Regex-based pattern filtering for log lines."""
from __future__ import annotations

import re
from typing import Iterable, Iterator, List, Optional, Pattern


def _compile(pattern: str, ignore_case: bool) -> Pattern[str]:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(pattern, flags)


def filter_by_pattern(
    lines: Iterable[str],
    pattern: str,
    *,
    ignore_case: bool = True,
    invert: bool = False,
) -> Iterator[str]:
    """Yield lines that match (or don't match) *pattern*.

    Args:
        lines: Iterable of log line strings.
        pattern: Regular expression to match against each line.
        ignore_case: When True, matching is case-insensitive.
        invert: When True, yield lines that do *not* match.

    Yields:
        Lines satisfying the match condition.
    """
    rx = _compile(pattern, ignore_case)
    for line in lines:
        matched = rx.search(line) is not None
        if matched ^ invert:
            yield line


def count_pattern_matches(
    lines: Iterable[str],
    pattern: str,
    *,
    ignore_case: bool = True,
) -> int:
    """Return the number of lines that match *pattern*."""
    return sum(1 for _ in filter_by_pattern(lines, pattern, ignore_case=ignore_case))


def extract_pattern_groups(
    lines: Iterable[str],
    pattern: str,
    *,
    ignore_case: bool = True,
) -> Iterator[List[str]]:
    """For each matching line yield the list of captured groups.

    Lines that do not match are silently skipped.
    """
    rx = _compile(pattern, ignore_case)
    for line in lines:
        m = rx.search(line)
        if m:
            yield list(m.groups())


def first_match(
    lines: Iterable[str],
    pattern: str,
    *,
    ignore_case: bool = True,
) -> Optional[str]:
    """Return the first line matching *pattern*, or None."""
    return next(filter_by_pattern(lines, pattern, ignore_case=ignore_case), None)
