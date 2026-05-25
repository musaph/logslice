"""Tests for logslice.log_classifier."""
from __future__ import annotations

import pytest

from logslice.log_classifier import (
    ClassifyRule,
    ClassifiedLine,
    classify_line,
    classify_lines,
    compute_classify_summary,
    format_classify_summary,
    DEFAULT_CATEGORY,
)


def _rules():
    return [
        ClassifyRule(category="error", pattern=r"\bERROR\b"),
        ClassifyRule(category="warning", pattern=r"\bWARN(ING)?\b"),
        ClassifyRule(category="info", pattern=r"\bINFO\b"),
    ]


def test_classify_line_matches_first_rule():
    cl = classify_line("2024-01-01 ERROR something broke", _rules())
    assert cl.category == "error"
    assert cl.rule_index == 0


def test_classify_line_matches_second_rule():
    cl = classify_line("2024-01-01 WARNING disk low", _rules())
    assert cl.category == "warning"
    assert cl.rule_index == 1


def test_classify_line_unclassified_when_no_match():
    cl = classify_line("some random log line", _rules())
    assert cl.category == DEFAULT_CATEGORY
    assert cl.rule_index is None


def test_classify_line_preserves_original_line():
    original = "INFO server started"
    cl = classify_line(original, _rules())
    assert cl.line == original


def test_classify_line_case_insensitive_by_default():
    cl = classify_line("error: connection refused", _rules())
    assert cl.category == "error"


def test_classify_line_case_sensitive_no_match():
    rule = ClassifyRule(category="error", pattern=r"ERROR", case_sensitive=True)
    cl = classify_line("error: connection refused", [rule])
    assert cl.category == DEFAULT_CATEGORY


def test_classify_line_case_sensitive_match():
    rule = ClassifyRule(category="error", pattern=r"ERROR", case_sensitive=True)
    cl = classify_line("ERROR: connection refused", [rule])
    assert cl.category == "error"


def test_classify_lines_yields_classified_line_instances():
    lines = ["INFO ok", "ERROR bad", "nothing"]
    results = list(classify_lines(lines, _rules()))
    assert all(isinstance(r, ClassifiedLine) for r in results)


def test_classify_lines_correct_categories():
    lines = ["INFO ok", "ERROR bad", "nothing"]
    results = list(classify_lines(lines, _rules()))
    assert [r.category for r in results] == ["info", "error", DEFAULT_CATEGORY]


def test_classify_lines_empty_input_yields_nothing():
    assert list(classify_lines([], _rules())) == []


def test_compute_summary_total():
    lines = ["INFO ok", "ERROR bad", "nothing"]
    classified = classify_lines(lines, _rules())
    summary = compute_classify_summary(classified)
    assert summary.total == 3


def test_compute_summary_unclassified_count():
    lines = ["INFO ok", "nothing", "also nothing"]
    classified = classify_lines(lines, _rules())
    summary = compute_classify_summary(classified)
    assert summary.unclassified == 2


def test_compute_summary_category_counts():
    lines = ["INFO ok", "INFO again", "ERROR bad"]
    classified = classify_lines(lines, _rules())
    summary = compute_classify_summary(classified)
    assert summary.counts["info"] == 2
    assert summary.counts["error"] == 1


def test_format_summary_contains_total():
    lines = ["INFO ok", "ERROR bad"]
    classified = classify_lines(lines, _rules())
    summary = compute_classify_summary(classified)
    text = format_classify_summary(summary)
    assert "total: 2" in text


def test_format_summary_contains_category_names():
    lines = ["INFO ok", "ERROR bad"]
    classified = classify_lines(lines, _rules())
    summary = compute_classify_summary(classified)
    text = format_classify_summary(summary)
    assert "error" in text
    assert "info" in text
