"""Compare two log streams and report similarity metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class CompareResult:
    total_a: int
    total_b: int
    common: int
    only_in_a: List[str]
    only_in_b: List[str]
    jaccard: float


def _line_set(lines: Iterable[str]) -> set:
    return {line.rstrip("\n") for line in lines if line.strip()}


def compare_logs(
    lines_a: Iterable[str],
    lines_b: Iterable[str],
) -> CompareResult:
    """Return a CompareResult describing similarity between two log streams."""
    set_a = _line_set(lines_a)
    set_b = _line_set(lines_b)

    common = set_a & set_b
    only_a = sorted(set_a - set_b)
    only_b = sorted(set_b - set_a)

    union_size = len(set_a | set_b)
    jaccard = len(common) / union_size if union_size else 0.0

    return CompareResult(
        total_a=len(set_a),
        total_b=len(set_b),
        common=len(common),
        only_in_a=only_a,
        only_in_b=only_b,
        jaccard=round(jaccard, 4),
    )


def similarity_percent(result: CompareResult) -> float:
    """Return Jaccard similarity as a percentage."""
    return round(result.jaccard * 100, 2)


def format_compare_result(result: CompareResult) -> str:
    lines = [
        f"Lines in A      : {result.total_a}",
        f"Lines in B      : {result.total_b}",
        f"Common lines    : {result.common}",
        f"Only in A       : {len(result.only_in_a)}",
        f"Only in B       : {len(result.only_in_b)}",
        f"Jaccard         : {result.jaccard:.4f}",
        f"Similarity      : {similarity_percent(result):.2f}%",
    ]
    return "\n".join(lines)
