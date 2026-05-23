"""Redact or mask sensitive patterns from log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

# Built-in patterns for common sensitive data
_BUILTIN_PATTERNS: dict[str, str] = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "token": r"(?i)(?:token|api[_-]?key|secret)[=:\s]+[\w\-]{8,}",
    "jwt": r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
    "credit_card": r"\b(?:\d[ \-]?){13,16}\b",
}

DEFAULT_MASK = "***REDACTED***"


@dataclass
class SanitizeOptions:
    mask: str = DEFAULT_MASK
    builtin_patterns: List[str] = field(default_factory=list)
    custom_patterns: List[str] = field(default_factory=list)


@dataclass
class SanitizeResult:
    line: str
    redacted_count: int


def _build_regex(options: SanitizeOptions) -> Optional[re.Pattern]:
    parts: list[str] = []
    for name in options.builtin_patterns:
        pattern = _BUILTIN_PATTERNS.get(name)
        if pattern:
            parts.append(pattern)
    for custom in options.custom_patterns:
        parts.append(custom)
    if not parts:
        return None
    combined = "|".join(f"(?:{p})" for p in parts)
    return re.compile(combined)


def sanitize_line(line: str, options: SanitizeOptions) -> SanitizeResult:
    """Redact sensitive data from a single log line."""
    pattern = _build_regex(options)
    if pattern is None:
        return SanitizeResult(line=line, redacted_count=0)
    count = 0

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        nonlocal count
        count += 1
        return options.mask

    sanitized = pattern.sub(_replace, line)
    return SanitizeResult(line=sanitized, redacted_count=count)


def sanitize_lines(
    lines: Iterable[str], options: SanitizeOptions
) -> Iterator[SanitizeResult]:
    """Yield SanitizeResult for each line."""
    for line in lines:
        yield sanitize_line(line, options)


def count_redactions(lines: Iterable[str], options: SanitizeOptions) -> int:
    """Return total number of redactions across all lines."""
    return sum(r.redacted_count for r in sanitize_lines(lines, options))
