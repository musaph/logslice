"""Template-based log line renderer.

Allows users to reformat log lines using a Python str.format_map style
template, pulling fields extracted by field_extractor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.field_extractor import extract_fields


@dataclass
class TemplateOptions:
    template: str
    fallback: str = ""
    skip_unmatched: bool = False


@dataclass
class RenderResult:
    rendered: list[str] = field(default_factory=list)
    skipped: int = 0
    total: int = 0


def render_line(line: str, options: TemplateOptions) -> str | None:
    """Render a single line using the template.

    Returns None when the line cannot be rendered and skip_unmatched is True.
    """
    fields = extract_fields(line)
    if not fields:
        if options.skip_unmatched:
            return None
        return options.fallback if options.fallback else line
    try:
        return options.template.format_map(fields)
    except KeyError:
        if options.skip_unmatched:
            return None
        return options.fallback if options.fallback else line


def render_lines(
    lines: Iterable[str], options: TemplateOptions
) -> Iterator[str]:
    """Yield rendered lines, skipping those that cannot be rendered when
    skip_unmatched is True."""
    for line in lines:
        result = render_line(line, options)
        if result is not None:
            yield result


def compute_render_result(
    lines: Iterable[str], options: TemplateOptions
) -> RenderResult:
    """Collect all rendered lines and return a RenderResult with counts."""
    result = RenderResult()
    for line in lines:
        result.total += 1
        rendered = render_line(line, options)
        if rendered is None:
            result.skipped += 1
        else:
            result.rendered.append(rendered)
    return result


def format_render_result(result: RenderResult) -> str:
    """Return a human-readable summary of a RenderResult."""
    lines = [
        f"total   : {result.total}",
        f"rendered: {len(result.rendered)}",
        f"skipped : {result.skipped}",
    ]
    return "\n".join(lines)
