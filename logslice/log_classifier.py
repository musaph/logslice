"""Classify log lines into categories based on configurable rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional


@dataclass
class ClassifyRule:
    category: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class ClassifiedLine:
    line: str
    category: str
    rule_index: Optional[int] = None  # index of first matching rule


@dataclass
class ClassifySummary:
    total: int = 0
    unclassified: int = 0
    counts: dict[str, int] = field(default_factory=dict)


DEFAULT_CATEGORY = "unclassified"


def classify_line(
    line: str,
    rules: list[ClassifyRule],
    default: str = DEFAULT_CATEGORY,
) -> ClassifiedLine:
    """Return a ClassifiedLine using the first matching rule, or *default*."""
    for idx, rule in enumerate(rules):
        if rule.matches(line):
            return ClassifiedLine(line=line, category=rule.category, rule_index=idx)
    return ClassifiedLine(line=line, category=default, rule_index=None)


def classify_lines(
    lines: Iterable[str],
    rules: list[ClassifyRule],
    default: str = DEFAULT_CATEGORY,
) -> Iterator[ClassifiedLine]:
    """Yield a ClassifiedLine for every input line."""
    for line in lines:
        yield classify_line(line, rules, default)


def compute_classify_summary(
    classified: Iterable[ClassifiedLine],
) -> ClassifySummary:
    """Aggregate classification counts into a summary."""
    summary = ClassifySummary()
    for cl in classified:
        summary.total += 1
        summary.counts[cl.category] = summary.counts.get(cl.category, 0) + 1
        if cl.rule_index is None:
            summary.unclassified += 1
    return summary


def format_classify_summary(summary: ClassifySummary) -> str:
    """Return a human-readable summary string."""
    lines = [f"total: {summary.total}", f"unclassified: {summary.unclassified}"]
    for cat, count in sorted(summary.counts.items()):
        lines.append(f"  {cat}: {count}")
    return "\n".join(lines)
