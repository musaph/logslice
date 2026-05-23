"""Log level filtering utilities for logslice."""

from __future__ import annotations

import re
from typing import Iterable, Iterator, Optional

# Ordered from lowest to highest severity
LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]

# Normalise aliases to canonical names
_CANONICAL = {
    "WARN": "WARNING",
    "FATAL": "CRITICAL",
}

_LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\b",
    re.IGNORECASE,
)


def _canonical(level: str) -> str:
    """Return the canonical upper-case name for *level*."""
    upper = level.upper()
    return _CANONICAL.get(upper, upper)


def _severity(level: str) -> int:
    """Return a numeric severity for *level* (higher == more severe)."""
    canon = _canonical(level)
    order = [_canonical(l) for l in LEVEL_ORDER]
    try:
        return order.index(canon)
    except ValueError:
        return -1


def detect_level(line: str) -> Optional[str]:
    """Return the first log level token found in *line*, or ``None``."""
    match = _LEVEL_PATTERN.search(line)
    if match:
        return _canonical(match.group(1))
    return None


def filter_by_level(
    lines: Iterable[str],
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
    exact_level: Optional[str] = None,
) -> Iterator[str]:
    """Yield lines whose detected log level satisfies the given constraints.

    Parameters
    ----------
    lines:
        Source lines to filter.
    min_level:
        Only yield lines at or above this severity (e.g. ``"WARNING"``).
    max_level:
        Only yield lines at or below this severity (e.g. ``"ERROR"``).
    exact_level:
        Only yield lines that match exactly this level.
    """
    min_sev = _severity(min_level) if min_level else None
    max_sev = _severity(max_level) if max_level else None
    exact_canon = _canonical(exact_level) if exact_level else None

    for line in lines:
        level = detect_level(line)
        if level is None:
            continue
        if exact_canon is not None and level != exact_canon:
            continue
        sev = _severity(level)
        if min_sev is not None and sev < min_sev:
            continue
        if max_sev is not None and sev > max_sev:
            continue
        yield line


def count_by_level(lines: Iterable[str]) -> dict[str, int]:
    """Return a mapping of canonical level name to occurrence count."""
    counts: dict[str, int] = {}
    for line in lines:
        level = detect_level(line)
        if level:
            counts[level] = counts.get(level, 0) + 1
    return counts
