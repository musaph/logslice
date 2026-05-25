"""Correlate log lines across multiple sources by a shared field or pattern."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.field_extractor import extract_fields


@dataclass
class CorrelationGroup:
    key: str
    lines: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.lines)


@dataclass
class CorrelationResult:
    groups: List[CorrelationGroup]
    unmatched: List[str]

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_matched(self) -> int:
        return sum(g.count for g in self.groups)


def _extract_key(line: str, correlation_field: str) -> Optional[str]:
    """Return the value of *correlation_field* from *line*, or None."""
    fields = extract_fields(line)
    value = fields.get(correlation_field)
    if value is None:
        return None
    return str(value)


def correlate(
    lines: Iterable[str],
    correlation_field: str,
    min_group_size: int = 1,
) -> CorrelationResult:
    """Group *lines* by the value of *correlation_field*.

    Lines that do not contain the field are collected in *unmatched*.
    Groups with fewer than *min_group_size* lines are also moved to *unmatched*.
    """
    buckets: Dict[str, List[str]] = {}
    unmatched: List[str] = []

    for line in lines:
        key = _extract_key(line, correlation_field)
        if key is None:
            unmatched.append(line)
        else:
            buckets.setdefault(key, []).append(line)

    groups: List[CorrelationGroup] = []
    for key, group_lines in buckets.items():
        if len(group_lines) < min_group_size:
            unmatched.extend(group_lines)
        else:
            groups.append(CorrelationGroup(key=key, lines=group_lines))

    groups.sort(key=lambda g: g.count, reverse=True)
    return CorrelationResult(groups=groups, unmatched=unmatched)


def iter_correlated_lines(result: CorrelationResult) -> Iterator[str]:
    """Yield lines in group order (largest group first)."""
    for group in result.groups:
        yield from group.lines


def format_correlation_summary(result: CorrelationResult) -> str:
    """Return a human-readable summary of the correlation result."""
    lines = [
        f"groups={result.total_groups}",
        f"matched={result.total_matched}",
        f"unmatched={len(result.unmatched)}",
    ]
    for g in result.groups:
        lines.append(f"  [{g.key}] {g.count} line(s)")
    return "\n".join(lines)
