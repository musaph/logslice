"""Tests for logslice.log_scorer."""
import pytest
from logslice.log_scorer import (
    ScoreOptions,
    ScoredLine,
    score_lines,
    top_n,
    format_scored_line,
)


def _opts(**kwargs):
    weights = kwargs.pop("weights", {"error": 2.0, "warn": 1.0})
    return ScoreOptions(weights=weights, **kwargs)


def _collect(it):
    return list(it)


# --- score_lines ---

def test_empty_input_yields_nothing():
    assert _collect(score_lines([], _opts())) == []


def test_non_matching_line_excluded_by_default():
    results = _collect(score_lines(["hello world\n"], _opts()))
    assert results == []


def test_matching_line_included():
    results = _collect(score_lines(["error occurred\n"], _opts()))
    assert len(results) == 1
    assert results[0].score == 2.0


def test_multiple_terms_scores_accumulate():
    results = _collect(score_lines(["error and warn\n"], _opts()))
    assert results[0].score == pytest.approx(3.0)


def test_matched_terms_listed():
    results = _collect(score_lines(["error here\n"], _opts()))
    assert "error" in results[0].matched_terms


def test_line_number_starts_at_one_by_default():
    lines = ["info\n", "error\n"]
    results = _collect(score_lines(lines, _opts()))
    assert results[0].line_number == 2


def test_line_number_custom_start():
    results = _collect(score_lines(["error\n"], _opts(), start=10))
    assert results[0].line_number == 10


def test_min_score_filters_low_scores():
    opts = _opts(min_score=2.0)
    lines = ["warn only\n", "error only\n"]
    results = _collect(score_lines(lines, opts))
    # warn=1.0 excluded, error=2.0 included
    assert len(results) == 1
    assert results[0].score == 2.0


def test_case_insensitive_default():
    results = _collect(score_lines(["ERROR occurred\n"], _opts()))
    assert len(results) == 1


def test_case_sensitive_no_match():
    opts = _opts(case_sensitive=True)
    results = _collect(score_lines(["ERROR occurred\n"], opts))
    assert results == []


def test_case_sensitive_match():
    opts = _opts(case_sensitive=True)
    results = _collect(score_lines(["error occurred\n"], opts))
    assert len(results) == 1


def test_line_stripped_of_newline():
    results = _collect(score_lines(["error\n"], _opts()))
    assert results[0].line == "error"


# --- top_n ---

def test_top_n_returns_highest_scores():
    lines = ["warn a\n", "error b\n", "error and warn\n"]
    results = top_n(lines, _opts(), n=2)
    assert len(results) == 2
    assert results[0].score >= results[1].score


def test_top_n_larger_than_results_returns_all():
    lines = ["error\n", "warn\n"]
    results = top_n(lines, _opts(), n=100)
    assert len(results) == 2


def test_top_n_zero_returns_empty():
    results = top_n(["error\n"], _opts(), n=0)
    assert results == []


# --- format_scored_line ---

def test_format_includes_line_number():
    sl = ScoredLine(line="error here", line_number=42, score=2.0, matched_terms=["error"])
    out = format_scored_line(sl)
    assert "42" in out


def test_format_includes_score():
    sl = ScoredLine(line="error here", line_number=1, score=2.0, matched_terms=["error"])
    out = format_scored_line(sl)
    assert "2.00" in out


def test_format_includes_terms():
    sl = ScoredLine(line="error here", line_number=1, score=2.0, matched_terms=["error"])
    out = format_scored_line(sl)
    assert "error" in out


def test_format_hide_terms():
    sl = ScoredLine(line="error here", line_number=1, score=2.0, matched_terms=["error"])
    out = format_scored_line(sl, show_terms=False)
    assert "[" not in out
