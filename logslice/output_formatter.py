"""Output formatting utilities for logslice results."""

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional


@dataclass
class FormatOptions:
    """Configuration for output formatting."""
    show_line_numbers: bool = False
    highlight_keyword: Optional[str] = None
    prefix: str = ""
    color: bool = False


_ANSI_YELLOW = "\033[33m"
_ANSI_RESET = "\033[0m"


def _highlight(line: str, keyword: str, use_color: bool) -> str:
    """Wrap occurrences of keyword in ANSI color codes or brackets."""
    if use_color:
        return line.replace(keyword, f"{_ANSI_YELLOW}{keyword}{_ANSI_RESET}")
    return line.replace(keyword, f"[{keyword}]")


def format_lines(
    lines: Iterable[str],
    options: Optional[FormatOptions] = None,
    start_line: int = 1,
) -> Iterator[str]:
    """Format an iterable of log lines according to FormatOptions.

    Args:
        lines: Raw log lines to format.
        options: Formatting configuration; defaults to plain output.
        start_line: The 1-based line number to assign to the first line.

    Yields:
        Formatted log line strings (without trailing newline).
    """
    if options is None:
        options = FormatOptions()

    for idx, line in enumerate(lines, start=start_line):
        text = line.rstrip("\n")

        if options.highlight_keyword:
            text = _highlight(text, options.highlight_keyword, options.color)

        parts = []
        if options.prefix:
            parts.append(options.prefix)
        if options.show_line_numbers:
            parts.append(f"{idx:>6}: ")
        parts.append(text)

        yield "".join(parts)


def lines_to_string(
    lines: Iterable[str],
    options: Optional[FormatOptions] = None,
) -> str:
    """Convenience wrapper that returns all formatted lines joined by newlines."""
    return "\n".join(format_lines(lines, options))
