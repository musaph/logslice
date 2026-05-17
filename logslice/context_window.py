"""Context-window extraction: return matching lines plus surrounding context."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, List, Tuple


@dataclass
class ContextMatch:
    """A matching line together with its surrounding context lines."""

    line_number: int  # 1-based
    line: str
    before: List[Tuple[int, str]]  # (line_number, text)
    after: List[Tuple[int, str]]   # (line_number, text)


def extract_context(
    lines: Iterable[str],
    predicate: Callable[[str], bool],
    before: int = 2,
    after: int = 2,
) -> Iterator[ContextMatch]:
    """Yield :class:`ContextMatch` for every line where *predicate* is True.

    Parameters
    ----------
    lines:
        Source lines (without trailing newlines is fine).
    predicate:
        Called with each line; a truthy return triggers a match.
    before:
        Number of lines of context to include *before* the match.
    after:
        Number of lines of context to include *after* the match.
    """
    if before < 0 or after < 0:
        raise ValueError("'before' and 'after' must be non-negative integers")

    # Buffer all lines so we can look ahead for the 'after' context.
    buffered: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        buffered.append((idx, line))

    total = len(buffered)
    for i, (lineno, line) in enumerate(buffered):
        if not predicate(line):
            continue
        before_slice = buffered[max(0, i - before) : i]
        after_slice = buffered[i + 1 : min(total, i + 1 + after)]
        yield ContextMatch(
            line_number=lineno,
            line=line,
            before=list(before_slice),
            after=list(after_slice),
        )


def format_context_match(match: ContextMatch, separator: str = "--") -> List[str]:
    """Return a list of formatted strings representing *match*.

    Each entry is ``"<lineno>: <text>"``.  A *separator* line is
    appended after the block so consecutive matches are visually
    separated.
    """
    out: List[str] = []
    for lineno, text in match.before:
        out.append(f"{lineno}: {text}")
    out.append(f"{match.line_number}: {match.line}")
    for lineno, text in match.after:
        out.append(f"{lineno}: {text}")
    if separator:
        out.append(separator)
    return out
