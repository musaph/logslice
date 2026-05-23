"""Tests for logslice.log_templater."""
from __future__ import annotations

import pytest

from logslice.log_templater import (
    TemplateOptions,
    RenderResult,
    render_line,
    render_lines,
    compute_render_result,
    format_render_result,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _opts(template: str, fallback: str = "", skip: bool = False) -> TemplateOptions:
    return TemplateOptions(template=template, fallback=fallback, skip_unmatched=skip)


JSON_LINE = '{"level": "INFO", "msg": "hello", "service": "api"}'
LOGFMT_LINE = 'level=WARN msg="disk full" host=web01'
PLAIN_LINE = "just a plain log line with no structure"


# ---------------------------------------------------------------------------
# render_line
# ---------------------------------------------------------------------------

def test_render_line_json_fields():
    result = render_line(JSON_LINE, _opts("{level} | {msg}"))
    assert result == "INFO | hello"


def test_render_line_logfmt_fields():
    result = render_line(LOGFMT_LINE, _opts("[{level}] {msg} on {host}"))
    assert result == "[WARN] disk full on web01"


def test_render_line_plain_returns_line_when_no_fallback():
    result = render_line(PLAIN_LINE, _opts("{level}: {msg}"))
    assert result == PLAIN_LINE


def test_render_line_plain_returns_fallback():
    result = render_line(PLAIN_LINE, _opts("{level}: {msg}", fallback="<no fields>"))
    assert result == "<no fields>"


def test_render_line_skip_unmatched_plain_returns_none():
    result = render_line(PLAIN_LINE, _opts("{level}: {msg}", skip=True))
    assert result is None


def test_render_line_missing_key_returns_original_line():
    # JSON line exists but template references a missing key
    result = render_line(JSON_LINE, _opts("{level}: {nonexistent}"))
    assert result == JSON_LINE


def test_render_line_missing_key_skip_returns_none():
    result = render_line(JSON_LINE, _opts("{level}: {nonexistent}", skip=True))
    assert result is None


def test_render_line_missing_key_uses_fallback():
    result = render_line(JSON_LINE, _opts("{nonexistent}", fallback="N/A"))
    assert result == "N/A"


# ---------------------------------------------------------------------------
# render_lines
# ---------------------------------------------------------------------------

def test_render_lines_yields_rendered_strings():
    lines = [JSON_LINE, LOGFMT_LINE]
    results = list(render_lines(lines, _opts("{level}")))
    assert results == ["INFO", "WARN"]


def test_render_lines_skips_unmatched_when_flag_set():
    lines = [JSON_LINE, PLAIN_LINE, LOGFMT_LINE]
    results = list(render_lines(lines, _opts("{level}", skip=True)))
    assert len(results) == 2
    assert PLAIN_LINE not in results


def test_render_lines_empty_input_yields_nothing():
    results = list(render_lines([], _opts("{level}")))
    assert results == []


# ---------------------------------------------------------------------------
# compute_render_result
# ---------------------------------------------------------------------------

def test_compute_render_result_totals():
    lines = [JSON_LINE, PLAIN_LINE, LOGFMT_LINE]
    result = compute_render_result(lines, _opts("{level}", skip=True))
    assert result.total == 3
    assert len(result.rendered) == 2
    assert result.skipped == 1


def test_compute_render_result_no_skips():
    lines = [JSON_LINE, LOGFMT_LINE]
    result = compute_render_result(lines, _opts("{level}"))
    assert result.skipped == 0
    assert result.total == 2


# ---------------------------------------------------------------------------
# format_render_result
# ---------------------------------------------------------------------------

def test_format_render_result_contains_counts():
    r = RenderResult(rendered=["a", "b"], skipped=1, total=3)
    summary = format_render_result(r)
    assert "3" in summary
    assert "2" in summary
    assert "1" in summary
