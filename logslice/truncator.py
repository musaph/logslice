"""truncator.py — Utilities for truncating long log lines.

Provides helpers to shorten lines that exceed a maximum character width,
optionally preserving a configurable tail so that trailing fields (e.g.
HTTP status codes, durations) remain visible.
"""

from __future__ import annotations

from typing import Generator, Iterable

_DEFAULT_MAX_WIDTH: int = 200
_DEFAULT_ELLIPSIS: str = "..."


def truncate_line(
    line: str,
    max_width: int = _DEFAULT_MAX_WIDTH,
    ellipsis: str = _DEFAULT_ELLIPSIS,
    tail: int = 0,
) -> str:
    """Return *line* truncated to *max_width* characters.

    Parameters
    ----------
    line:
        The raw log line to truncate (should not contain a trailing newline).
    max_width:
        Maximum number of characters allowed in the returned string,
        including the *ellipsis* and any preserved *tail*.
    ellipsis:
        Replacement marker inserted at the truncation point.
    tail:
        Number of characters from the **end** of *line* to preserve after
        the ellipsis.  Must be less than ``max_width - len(ellipsis)``.
        When *tail* is 0 the tail is omitted entirely.

    Returns
    -------
    str
        The (possibly truncated) line.  If ``len(line) <= max_width`` the
        original string is returned unchanged.

    Raises
    ------
    ValueError
        If *max_width* is too small to fit the *ellipsis* and requested
        *tail*, or if *tail* is negative.
    """
    if max_width < 1:
        raise ValueError(f"max_width must be >= 1, got {max_width}")
    if tail < 0:
        raise ValueError(f"tail must be >= 0, got {tail}")

    ell_len = len(ellipsis)
    budget = max_width - ell_len - tail
    if budget < 0:
        raise ValueError(
            f"max_width ({max_width}) is too small to fit ellipsis "
            f"({ell_len} chars) and tail ({tail} chars)"
        )

    if len(line) <= max_width:
        return line

    head_part = line[:budget]
    if tail:
        tail_part = line[-tail:]
        return head_part + ellipsis + tail_part
    return head_part + ellipsis


def truncate_lines(
    lines: Iterable[str],
    max_width: int = _DEFAULT_MAX_WIDTH,
    ellipsis: str = _DEFAULT_ELLIPSIS,
    tail: int = 0,
) -> Generator[str, None, None]:
    """Yield each line from *lines* truncated to *max_width* characters.

    This is a thin convenience wrapper around :func:`truncate_line` that
    operates on an iterable of lines rather than a single string.

    Parameters
    ----------
    lines:
        Iterable of log lines (trailing newlines should already be stripped).
    max_width:
        Forwarded to :func:`truncate_line`.
    ellipsis:
        Forwarded to :func:`truncate_line`.
    tail:
        Forwarded to :func:`truncate_line`.
    """
    for line in lines:
        yield truncate_line(line, max_width=max_width, ellipsis=ellipsis, tail=tail)


def count_truncated(
    lines: Iterable[str],
    max_width: int = _DEFAULT_MAX_WIDTH,
) -> int:
    """Return the number of lines in *lines* that exceed *max_width* characters.

    Useful for reporting how many lines *would* be affected before committing
    to truncation.
    """
    return sum(1 for line in lines if len(line) > max_width)
