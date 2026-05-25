"""Log profiling: measure parse rate, timestamp density, and field richness."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.timestamp_parser import parse_timestamp
from logslice.field_extractor import extract_fields


@dataclass
class ProfileResult:
    total_lines: int = 0
    lines_with_timestamp: int = 0
    lines_with_fields: int = 0
    total_fields: int = 0
    elapsed_seconds: float = 0.0
    unique_field_names: set[str] = field(default_factory=set)

    @property
    def timestamp_density(self) -> float:
        """Fraction of lines that carry a parseable timestamp."""
        return self.lines_with_timestamp / self.total_lines if self.total_lines else 0.0

    @property
    def field_density(self) -> float:
        """Fraction of lines that carry structured fields."""
        return self.lines_with_fields / self.total_lines if self.total_lines else 0.0

    @property
    def avg_fields_per_line(self) -> float:
        base = self.lines_with_fields or 1
        return self.total_fields / base

    @property
    def lines_per_second(self) -> float:
        return self.total_lines / self.elapsed_seconds if self.elapsed_seconds else 0.0


def profile_lines(lines: Iterable[str]) -> ProfileResult:
    """Consume *lines* once and return a :class:`ProfileResult`."""
    result = ProfileResult()
    start = time.perf_counter()
    for line in lines:
        result.total_lines += 1
        if parse_timestamp(line) is not None:
            result.lines_with_timestamp += 1
        fields = extract_fields(line)
        if fields:
            result.lines_with_fields += 1
            result.total_fields += len(fields)
            result.unique_field_names.update(fields.keys())
    result.elapsed_seconds = time.perf_counter() - start
    return result


def format_profile(result: ProfileResult) -> Iterator[str]:
    """Yield human-readable summary lines for *result*."""
    yield f"total_lines          : {result.total_lines}"
    yield f"lines_with_timestamp : {result.lines_with_timestamp} ({result.timestamp_density:.1%})"
    yield f"lines_with_fields    : {result.lines_with_fields} ({result.field_density:.1%})"
    yield f"unique_field_names   : {len(result.unique_field_names)}"
    yield f"avg_fields_per_line  : {result.avg_fields_per_line:.2f}"
    yield f"elapsed_seconds      : {result.elapsed_seconds:.4f}"
    yield f"lines_per_second     : {result.lines_per_second:.0f}"
    if result.unique_field_names:
        names = ", ".join(sorted(result.unique_field_names))
        yield f"field_names          : {names}"
