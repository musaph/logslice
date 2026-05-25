"""Token-frequency analysis for log lines."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator

# Tokens that carry little diagnostic value
_STOP_WORDS: frozenset[str] = frozenset(
    {"the", "a", "an", "in", "on", "at", "to", "of", "and", "or", "is", "was"}
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,}")


@dataclass
class TokenFrequency:
    """Aggregated token counts across a corpus of log lines."""

    counts: Counter = field(default_factory=Counter)
    total_lines: int = 0
    total_tokens: int = 0


def tokenize_line(line: str, stop_words: frozenset[str] = _STOP_WORDS) -> list[str]:
    """Return lower-cased word tokens from *line*, excluding stop words."""
    return [
        m.lower()
        for m in _TOKEN_RE.findall(line)
        if m.lower() not in stop_words
    ]


def compute_token_frequency(
    lines: Iterable[str],
    stop_words: frozenset[str] = _STOP_WORDS,
) -> TokenFrequency:
    """Count token occurrences across all *lines*."""
    result = TokenFrequency()
    for line in lines:
        tokens = tokenize_line(line, stop_words)
        result.counts.update(tokens)
        result.total_lines += 1
        result.total_tokens += len(tokens)
    return result


def top_tokens(freq: TokenFrequency, n: int = 10) -> list[tuple[str, int]]:
    """Return the *n* most common tokens as (token, count) pairs."""
    return freq.counts.most_common(n)


def format_token_frequency(freq: TokenFrequency, n: int = 10) -> Iterator[str]:
    """Yield human-readable lines summarising token frequency."""
    yield f"Lines analysed : {freq.total_lines}"
    yield f"Total tokens   : {freq.total_tokens}"
    yield f"Unique tokens  : {len(freq.counts)}"
    yield ""
    yield f"{'Token':<30} {'Count':>8}"
    yield "-" * 40
    for token, count in top_tokens(freq, n):
        yield f"{token:<30} {count:>8}"
