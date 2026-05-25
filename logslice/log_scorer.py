"""Relevance scoring for log lines based on keyword weights."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


@dataclass
class ScoredLine:
    line: str
    line_number: int
    score: float
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class ScoreOptions:
    weights: Dict[str, float]
    case_sensitive: bool = False
    min_score: float = 0.0


def _score_line(line: str, opts: ScoreOptions) -> tuple[float, List[str]]:
    """Return (total_score, matched_terms) for a single line."""
    total = 0.0
    matched: List[str] = []
    haystack = line if opts.case_sensitive else line.lower()
    for term, weight in opts.weights.items():
        needle = term if opts.case_sensitive else term.lower()
        if re.search(re.escape(needle), haystack):
            total += weight
            matched.append(term)
    return total, matched


def score_lines(
    lines: Iterable[str],
    opts: ScoreOptions,
    *,
    start: int = 1,
) -> Iterator[ScoredLine]:
    """Yield ScoredLine for every line whose score meets min_score."""
    for idx, line in enumerate(lines, start=start):
        score, matched = _score_line(line, opts)
        if score >= opts.min_score:
            yield ScoredLine(
                line=line.rstrip("\n"),
                line_number=idx,
                score=score,
                matched_terms=matched,
            )


def top_n(
    lines: Iterable[str],
    opts: ScoreOptions,
    n: int,
    *,
    start: int = 1,
) -> List[ScoredLine]:
    """Return the top-n highest-scoring lines."""
    scored = list(score_lines(lines, opts, start=start))
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:n]


def format_scored_line(sl: ScoredLine, *, show_terms: bool = True) -> str:
    """Format a ScoredLine for human-readable output."""
    terms = ", ".join(sl.matched_terms) if show_terms and sl.matched_terms else ""
    terms_part = f" [{terms}]" if terms else ""
    return f"{sl.line_number:>6} | score={sl.score:.2f}{terms_part} | {sl.line}"
