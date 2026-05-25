"""log_watchdog.py — Monitor a log file and alert when a pattern is seen."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, Optional

from logslice.pattern_filter import _compile


@dataclass
class WatchAlert:
    line_number: int
    line: str
    pattern: str

    def __str__(self) -> str:
        return f"[ALERT] line {self.line_number} matched {self.pattern!r}: {self.line.rstrip()}"


@dataclass
class WatchdogOptions:
    patterns: list[str]
    case_sensitive: bool = False
    max_alerts: int = 0  # 0 = unlimited
    stop_on_first: bool = False


@dataclass
class WatchdogResult:
    alerts: list[WatchAlert] = field(default_factory=list)
    lines_scanned: int = 0

    @property
    def alert_count(self) -> int:
        return len(self.alerts)


def watch_lines(
    lines: Iterable[str],
    options: WatchdogOptions,
    callback: Optional[Callable[[WatchAlert], None]] = None,
) -> Iterator[WatchAlert]:
    """Scan *lines* and yield a WatchAlert for every line matching any pattern."""
    compiled = [
        (pat, _compile(pat, case_sensitive=options.case_sensitive))
        for pat in options.patterns
    ]
    alerts_emitted = 0
    for lineno, line in enumerate(lines, start=1):
        for pat, regex in compiled:
            if regex.search(line):
                alert = WatchAlert(line_number=lineno, line=line, pattern=pat)
                if callback is not None:
                    callback(alert)
                yield alert
                alerts_emitted += 1
                if options.stop_on_first:
                    return
                if options.max_alerts and alerts_emitted >= options.max_alerts:
                    return
                break  # one alert per line even if multiple patterns match


def compute_watchdog_result(
    lines: Iterable[str],
    options: WatchdogOptions,
) -> WatchdogResult:
    """Consume *lines* and return a WatchdogResult summary."""
    result = WatchdogResult()
    all_lines = list(lines)
    result.lines_scanned = len(all_lines)
    result.alerts = list(watch_lines(all_lines, options))
    return result


def format_watchdog_result(result: WatchdogResult) -> str:
    parts = [
        f"lines_scanned={result.lines_scanned}",
        f"alerts={result.alert_count}",
    ]
    body = "\n".join(str(a) for a in result.alerts)
    header = "  ".join(parts)
    return f"{header}\n{body}".strip()
