"""Tests for logslice.log_sanitizer."""

from __future__ import annotations

import pytest

from logslice.log_sanitizer import (
    DEFAULT_MASK,
    SanitizeOptions,
    SanitizeResult,
    count_redactions,
    sanitize_line,
    sanitize_lines,
)


def _opts(*builtins: str, custom: list[str] | None = None, mask: str = DEFAULT_MASK) -> SanitizeOptions:
    return SanitizeOptions(mask=mask, builtin_patterns=list(builtins), custom_patterns=custom or [])


def test_no_patterns_returns_line_unchanged():
    opts = _opts()
    result = sanitize_line("hello world 192.168.1.1", opts)
    assert result.line == "hello world 192.168.1.1"
    assert result.redacted_count == 0


def test_ipv4_redacted():
    opts = _opts("ipv4")
    result = sanitize_line("connected from 10.0.0.1", opts)
    assert "10.0.0.1" not in result.line
    assert DEFAULT_MASK in result.line
    assert result.redacted_count == 1


def test_email_redacted():
    opts = _opts("email")
    result = sanitize_line("user alice@example.com logged in", opts)
    assert "alice@example.com" not in result.line
    assert result.redacted_count == 1


def test_jwt_redacted():
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    opts = _opts("jwt")
    result = sanitize_line(f"Authorization: Bearer {token}", opts)
    assert token not in result.line
    assert result.redacted_count == 1


def test_multiple_matches_counted():
    opts = _opts("ipv4")
    result = sanitize_line("src=1.2.3.4 dst=5.6.7.8", opts)
    assert result.redacted_count == 2


def test_custom_pattern_redacted():
    opts = _opts(custom=[r"password=\S+"])
    result = sanitize_line("login password=s3cr3t ok", opts)
    assert "s3cr3t" not in result.line
    assert result.redacted_count == 1


def test_custom_mask_used():
    opts = _opts("ipv4", mask="[IP]") 
    result = sanitize_line("host 192.168.0.1", opts)
    assert "[IP]" in result.line


def test_sanitize_lines_yields_results():
    opts = _opts("email")
    lines = ["a@b.com logged in", "no email here", "c@d.org logged out"]
    results = list(sanitize_lines(lines, opts))
    assert len(results) == 3
    assert all(isinstance(r, SanitizeResult) for r in results)
    assert results[0].redacted_count == 1
    assert results[1].redacted_count == 0
    assert results[2].redacted_count == 1


def test_count_redactions_sums_all():
    opts = _opts("ipv4")
    lines = ["ip 1.2.3.4", "ip 5.6.7.8 and 9.10.11.12", "nothing"]
    assert count_redactions(lines, opts) == 3


def test_empty_input_yields_nothing():
    opts = _opts("ipv4")
    results = list(sanitize_lines([], opts))
    assert results == []


def test_multiple_builtin_patterns():
    opts = _opts("ipv4", "email")
    result = sanitize_line("from 1.2.3.4 to user@host.com", opts)
    assert result.redacted_count == 2
    assert "1.2.3.4" not in result.line
    assert "user@host.com" not in result.line
