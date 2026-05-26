"""Trace a value across log lines by tracking a correlated field."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.field_extractor import extract_fields


@dataclass
class TraceEntry:
    line_number: int
    line: str
    trace_value: str
    fields: dict


@dataclass
class TraceResult:
    trace_field: str
    trace_value: str
    entries: List[TraceEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)


def trace_lines(
    lines: Iterable[str],
    trace_field: str,
    trace_value: str,
    *,
    case_sensitive: bool = False,
) -> Iterator[TraceEntry]:
    """Yield TraceEntry for every line whose *trace_field* matches *trace_value*."""
    needle = trace_value if case_sensitive else trace_value.lower()
    for lineno, line in enumerate(lines, start=1):
        fields = extract_fields(line)
        raw = fields.get(trace_field)
        if raw is None:
            continue
        candidate = str(raw) if case_sensitive else str(raw).lower()
        if candidate == needle:
            yield TraceEntry(
                line_number=lineno,
                line=line.rstrip("\n"),
                trace_value=str(raw),
                fields=fields,
            )


def compute_trace_result(
    lines: Iterable[str],
    trace_field: str,
    trace_value: str,
    *,
    case_sensitive: bool = False,
) -> TraceResult:
    result = TraceResult(trace_field=trace_field, trace_value=trace_value)
    result.entries = list(
        trace_lines(lines, trace_field, trace_value, case_sensitive=case_sensitive)
    )
    return result


def format_trace_result(result: TraceResult) -> str:
    lines: List[str] = [
        f"trace_field={result.trace_field} trace_value={result.trace_value} "
        f"matches={result.count}",
        "-" * 60,
    ]
    for entry in result.entries:
        lines.append(f"[{entry.line_number:>6}] {entry.line}")
    return "\n".join(lines)
