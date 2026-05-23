"""Line sampling utilities for logslice.

Provides functions to sample log lines at a fixed rate or up to a
maximum count, useful for previewing large log files.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Iterator


def sample_every_nth(lines: Iterable[str], n: int) -> Iterator[str]:
    """Yield every *n*-th line from *lines* (1-indexed).

    Parameters
    ----------
    lines:
        Source iterable of log lines.
    n:
        Step size. Must be >= 1. When *n* is 1 every line is yielded.

    Raises
    ------
    ValueError
        If *n* is less than 1.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for index, line in enumerate(lines):
        if index % n == 0:
            yield line


def sample_head(lines: Iterable[str], max_lines: int) -> Iterator[str]:
    """Yield at most *max_lines* lines from the beginning of *lines*.

    Parameters
    ----------
    lines:
        Source iterable of log lines.
    max_lines:
        Maximum number of lines to yield. Must be >= 0.

    Raises
    ------
    ValueError
        If *max_lines* is negative.
    """
    if max_lines < 0:
        raise ValueError(f"max_lines must be >= 0, got {max_lines}")
    count = 0
    for line in lines:
        if count >= max_lines:
            break
        yield line
        count += 1


def sample_tail(lines: Iterable[str], max_lines: int) -> list[str]:
    """Return the last *max_lines* lines from *lines*.

    Consumes the entire iterable into a buffer; use only when the
    source is finite.

    Parameters
    ----------
    lines:
        Source iterable of log lines.
    max_lines:
        Number of trailing lines to return. Must be >= 0.

    Raises
    ------
    ValueError
        If *max_lines* is negative.
    """
    if max_lines < 0:
        raise ValueError(f"max_lines must be >= 0, got {max_lines}")
    if max_lines == 0:
        return []
    # deque with a fixed maxlen is O(1) for appends and automatic eviction,
    # avoiding the O(n) cost of list.pop(0) in the previous implementation.
    buffer: deque[str] = deque(lines, maxlen=max_lines)
    return list(buffer)
