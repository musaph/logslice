"""log_denoiser.py – suppress repetitive or low-signal log lines.

A *noisy* line is one whose normalised form appears more than
`threshold` times in the input stream.  The denoiser keeps track of
seen patterns and drops lines that exceed the threshold, optionally
replacing them with a single summary line.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator

# Tokens that vary per-event (numbers, hex ids, UUIDs, IPs)
_NOISE_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r"|\b(?:\d{1,3}\.){3}\d{1,3}\b"
    r"|0x[0-9a-fA-F]+"
    r"|\b\d+\b",
    re.IGNORECASE,
)


def _normalise(line: str) -> str:
    """Replace variable tokens with a placeholder to create a pattern key."""
    return _NOISE_RE.sub("<V>", line).strip()


@dataclass
class DenoiseResult:
    total_lines: int = 0
    kept_lines: int = 0
    suppressed_lines: int = 0
    unique_patterns: int = 0

    @property
    def suppression_rate(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.suppressed_lines / self.total_lines


def denoise(
    lines: Iterable[str],
    threshold: int = 5,
    summarise: bool = False,
) -> Iterator[str]:
    """Yield lines whose normalised pattern has not exceeded *threshold*.

    Parameters
    ----------
    lines:      Input log lines.
    threshold:  Maximum occurrences of a pattern before suppression starts.
    summarise:  When True, emit one summary line per suppressed pattern after
                the stream ends.
    """
    counts: dict[str, int] = {}
    suppressed: dict[str, int] = {}

    for line in lines:
        key = _normalise(line)
        counts[key] = counts.get(key, 0) + 1
        if counts[key] <= threshold:
            yield line
        else:
            suppressed[key] = suppressed.get(key, 0) + 1

    if summarise:
        for pattern, extra in suppressed.items():
            yield f"[denoiser] suppressed {extra} repetition(s) of: {pattern}"


def compute_denoise_result(
    lines: Iterable[str],
    threshold: int = 5,
) -> tuple[list[str], DenoiseResult]:
    """Return (kept_lines, DenoiseResult) for the given input."""
    counts: dict[str, int] = {}
    kept: list[str] = []
    total = 0

    for line in lines:
        total += 1
        key = _normalise(line)
        counts[key] = counts.get(key, 0) + 1
        if counts[key] <= threshold:
            kept.append(line)

    result = DenoiseResult(
        total_lines=total,
        kept_lines=len(kept),
        suppressed_lines=total - len(kept),
        unique_patterns=len(counts),
    )
    return kept, result


def format_denoise_result(r: DenoiseResult) -> str:
    rate_pct = r.suppression_rate * 100
    return (
        f"total={r.total_lines} kept={r.kept_lines} "
        f"suppressed={r.suppressed_lines} "
        f"patterns={r.unique_patterns} "
        f"suppression_rate={rate_pct:.1f}%"
    )
