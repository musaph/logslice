"""Aggregate log lines by a field or time bucket, counting occurrences."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from logslice.field_extractor import extract_fields
from logslice.timestamp_parser import parse_timestamp


@dataclass
class AggregateGroup:
    key: str
    count: int
    lines: List[str] = field(default_factory=list)


@dataclass
class AggregateResult:
    groups: List[AggregateGroup]
    total_lines: int
    unmatched: int

    @property
    def total_groups(self) -> int:
        return len(self.groups)


def _minute_bucket(line: str) -> Optional[str]:
    """Return a 'YYYY-MM-DD HH:MM' bucket string for a line, or None."""
    dt = parse_timestamp(line)
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M")


def aggregate_by_field(
    lines: Iterable[str],
    field_name: str,
    *,
    case_sensitive: bool = False,
    keep_lines: bool = False,
) -> AggregateResult:
    """Group lines by the value of a structured field."""
    buckets: Dict[str, List[str]] = defaultdict(list)
    total = 0
    unmatched = 0

    for line in lines:
        total += 1
        fields = extract_fields(line)
        key: Optional[str] = None
        for k, v in fields.items():
            compare_k = k if case_sensitive else k.lower()
            compare_f = field_name if case_sensitive else field_name.lower()
            if compare_k == compare_f:
                key = v
                break
        if key is None:
            unmatched += 1
            key = "<unmatched>"
        buckets[key].append(line if keep_lines else "")

    groups = [
        AggregateGroup(
            key=k,
            count=len(v),
            lines=v if keep_lines else [],
        )
        for k, v in sorted(buckets.items())
    ]
    return AggregateResult(groups=groups, total_lines=total, unmatched=unmatched)


def aggregate_by_minute(
    lines: Iterable[str],
    *,
    keep_lines: bool = False,
) -> AggregateResult:
    """Group lines by their truncated timestamp minute."""
    return _aggregate_by_key(lines, _minute_bucket, keep_lines=keep_lines)


def _aggregate_by_key(
    lines: Iterable[str],
    key_fn: Callable[[str], Optional[str]],
    *,
    keep_lines: bool = False,
) -> AggregateResult:
    buckets: Dict[str, List[str]] = defaultdict(list)
    total = 0
    unmatched = 0
    for line in lines:
        total += 1
        key = key_fn(line)
        if key is None:
            unmatched += 1
            key = "<unmatched>"
        buckets[key].append(line if keep_lines else "")
    groups = [
        AggregateGroup(key=k, count=len(v), lines=v if keep_lines else [])
        for k, v in sorted(buckets.items())
    ]
    return AggregateResult(groups=groups, total_lines=total, unmatched=unmatched)


def format_aggregate_result(result: AggregateResult) -> str:
    lines = [f"{'Key':<30} {'Count':>8}"]
    lines.append("-" * 40)
    for g in result.groups:
        lines.append(f"{g.key:<30} {g.count:>8}")
    lines.append("-" * 40)
    lines.append(f"{'Total':<30} {result.total_lines:>8}")
    if result.unmatched:
        lines.append(f"Unmatched lines: {result.unmatched}")
    return "\n".join(lines)
