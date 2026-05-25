"""Tests for logslice.log_tokenizer."""
from __future__ import annotations

from collections import Counter

import pytest

from logslice.log_tokenizer import (
    TokenFrequency,
    compute_token_frequency,
    format_token_frequency,
    tokenize_line,
    top_tokens,
)


# ---------------------------------------------------------------------------
# tokenize_line
# ---------------------------------------------------------------------------

def test_tokenize_returns_lowercase_tokens():
    tokens = tokenize_line("ERROR connecting to Database")
    assert "error" in tokens
    assert "connecting" in tokens
    assert "database" in tokens


def test_tokenize_excludes_stop_words():
    tokens = tokenize_line("the connection to the server is down")
    assert "the" not in tokens
    assert "is" not in tokens
    assert "to" not in tokens


def test_tokenize_excludes_single_char_tokens():
    # _TOKEN_RE requires at least 2 chars total (letter + 1 more)
    tokens = tokenize_line("a b c error")
    assert "a" not in tokens
    assert "b" not in tokens
    assert "error" in tokens


def test_tokenize_empty_line_returns_empty_list():
    assert tokenize_line("") == []


def test_tokenize_custom_stop_words():
    tokens = tokenize_line("error in service", stop_words=frozenset({"error"}))
    assert "error" not in tokens
    assert "service" in tokens


# ---------------------------------------------------------------------------
# compute_token_frequency
# ---------------------------------------------------------------------------

def test_total_lines_counted():
    freq = compute_token_frequency(["line one", "line two", "line three"])
    assert freq.total_lines == 3


def test_total_tokens_counted():
    freq = compute_token_frequency(["error connecting", "error timeout"])
    # 'error' x2, 'connecting' x1, 'timeout' x1 = 4
    assert freq.total_tokens == 4


def test_counts_aggregated_across_lines():
    freq = compute_token_frequency(["error here", "another error"])
    assert freq.counts["error"] == 2


def test_empty_input_returns_zero_stats():
    freq = compute_token_frequency([])
    assert freq.total_lines == 0
    assert freq.total_tokens == 0
    assert len(freq.counts) == 0


# ---------------------------------------------------------------------------
# top_tokens
# ---------------------------------------------------------------------------

def test_top_tokens_returns_most_common():
    freq = TokenFrequency(counts=Counter({"error": 5, "timeout": 3, "warn": 1}))
    result = top_tokens(freq, n=2)
    assert result[0] == ("error", 5)
    assert result[1] == ("timeout", 3)


def test_top_tokens_n_larger_than_vocab_returns_all():
    freq = TokenFrequency(counts=Counter({"error": 2, "warn": 1}))
    assert len(top_tokens(freq, n=100)) == 2


# ---------------------------------------------------------------------------
# format_token_frequency
# ---------------------------------------------------------------------------

def test_format_includes_header_fields():
    freq = compute_token_frequency(["error connecting to server"])
    output = list(format_token_frequency(freq))
    combined = "\n".join(output)
    assert "Lines analysed" in combined
    assert "Total tokens" in combined
    assert "Unique tokens" in combined


def test_format_includes_top_token():
    freq = compute_token_frequency(["error error error"])
    output = "\n".join(format_token_frequency(freq, n=5))
    assert "error" in output
