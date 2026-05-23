"""Keyword highlighting utilities for log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class HighlightOptions:
    """Configuration for keyword highlighting."""

    keywords: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    ansi_color: str = "\033[1;33m"  # bold yellow
    ansi_reset: str = "\033[0m"
    mark_prefix: str = ">>>"
    use_ansi: bool = True


def _build_pattern(keywords: List[str], case_sensitive: bool) -> Optional[re.Pattern]:
    """Compile a combined regex pattern for all keywords.

    Returns ``None`` if *keywords* is empty, which callers treat as
    "match everything".
    """
    if not keywords:
        return None
    escaped = [re.escape(kw) for kw in keywords if kw]
    if not escaped:
        return None
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile("(" + "|".join(escaped) + ")", flags)


def highlight_line(line: str, opts: HighlightOptions) -> str:
    """Return *line* with every keyword occurrence wrapped in ANSI codes.

    If *use_ansi* is False the line is returned unchanged (keywords are
    not visually marked — callers should use :func:`line_matches` to
    decide whether to prefix the line with *mark_prefix* instead).
    """
    pattern = _build_pattern(opts.keywords, opts.case_sensitive)
    if pattern is None:
        return line
    if not opts.use_ansi:
        return line
    return pattern.sub(
        lambda m: f"{opts.ansi_color}{m.group(0)}{opts.ansi_reset}", line
    )


def line_matches(line: str, opts: HighlightOptions) -> bool:
    """Return True if *line* contains at least one of the keywords."""
    pattern = _build_pattern(opts.keywords, opts.case_sensitive)
    if pattern is None:
        return True
    return pattern.search(line) is not None


def highlight_lines(
    lines: Iterable[str], opts: HighlightOptions
) -> Iterator[str]:
    """Yield each line from *lines*, highlighting keyword occurrences.

    Lines that do not contain any keyword are yielded unchanged.
    When *use_ansi* is False a matching line is prefixed with
    ``opts.mark_prefix`` instead.
    """
    for line in lines:
        if not line_matches(line, opts):
            yield line
            continue
        if opts.use_ansi:
            yield highlight_line(line, opts)
        else:
            yield f"{opts.mark_prefix} {line}" if opts.mark_prefix else line
