"""log_formatter.py — Reformat log lines between JSON, logfmt, and plain text."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Iterator, Literal

OutputFormat = Literal["json", "logfmt", "plain"]


@dataclass(frozen=True)
class FormatResult:
    total: int
    converted: int
    unchanged: int

    @property
    def conversion_rate(self) -> float:
        return self.converted / self.total if self.total else 0.0


def _parse_line(line: str) -> dict[str, str] | None:
    """Try to parse a line as JSON or logfmt; return None for plain text."""
    stripped = line.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    if "=" in stripped:
        fields: dict[str, str] = {}
        for token in stripped.split():
            if "=" in token:
                k, _, v = token.partition("=")
                fields[k] = v.strip('"')
        if fields:
            return fields
    return None


def _to_json(fields: dict[str, str]) -> str:
    return json.dumps(fields, separators=(",", ":"))


def _to_logfmt(fields: dict[str, str]) -> str:
    parts = []
    for k, v in fields.items():
        parts.append(f'{k}="{v}"' if " " in v else f"{k}={v}")
    return " ".join(parts)


def reformat_line(line: str, target: OutputFormat) -> str:
    """Reformat a single log line to *target* format.

    Lines that cannot be parsed are returned unchanged.
    """
    fields = _parse_line(line)
    if fields is None:
        return line.rstrip("\n")
    if target == "json":
        return _to_json(fields)
    if target == "logfmt":
        return _to_logfmt(fields)
    # plain: join values separated by spaces
    return " ".join(fields.values())


def reformat_lines(
    lines: Iterable[str], target: OutputFormat
) -> Iterator[str]:
    """Yield each line reformatted to *target* format."""
    for line in lines:
        yield reformat_line(line, target)


def compute_format_result(
    lines: Iterable[str], target: OutputFormat
) -> FormatResult:
    """Return conversion statistics without yielding lines."""
    total = converted = 0
    for line in lines:
        total += 1
        if _parse_line(line) is not None:
            converted += 1
    return FormatResult(
        total=total,
        converted=converted,
        unchanged=total - converted,
    )
