"""Tests for logslice.log_tagger."""
import pytest
from logslice.log_tagger import (
    TagRule,
    TaggedLine,
    apply_rules,
    tag_lines,
    count_by_tag,
    rules_from_dict,
)


# ---------------------------------------------------------------------------
# TagRule
# ---------------------------------------------------------------------------

def test_tag_rule_matches_keyword():
    rule = TagRule(tag="error", pattern="error")
    assert rule.matches("ERROR: disk full") is True


def test_tag_rule_no_match():
    rule = TagRule(tag="error", pattern="error")
    assert rule.matches("INFO: all good") is False


def test_tag_rule_case_insensitive_default():
    rule = TagRule(tag="warn", pattern="warn")
    assert rule.matches("WARN something happened") is True


def test_tag_rule_case_sensitive_no_match():
    rule = TagRule(tag="warn", pattern="warn", case_sensitive=True)
    assert rule.matches("WARN something happened") is False


def test_tag_rule_regex_pattern():
    rule = TagRule(tag="http_error", pattern=r"5\d{2}")
    assert rule.matches("status=500") is True
    assert rule.matches("status=200") is False


# ---------------------------------------------------------------------------
# TaggedLine
# ---------------------------------------------------------------------------

def test_tagged_line_tagged_property_true():
    tl = TaggedLine(line="some line", tags=["error"])
    assert tl.tagged is True


def test_tagged_line_tagged_property_false():
    tl = TaggedLine(line="some line", tags=[])
    assert tl.tagged is False


def test_tagged_line_formatted_with_tags():
    tl = TaggedLine(line="disk full", tags=["error", "alert"])
    formatted = tl.formatted()
    assert "disk full" in formatted
    assert "error" in formatted
    assert "alert" in formatted


def test_tagged_line_formatted_no_tags_returns_plain():
    tl = TaggedLine(line="normal line", tags=[])
    assert tl.formatted() == "normal line"


def test_tagged_line_formatted_deduplicates_tags():
    tl = TaggedLine(line="x", tags=["a", "a", "b"])
    formatted = tl.formatted()
    assert formatted.count("a") == 1


# ---------------------------------------------------------------------------
# apply_rules
# ---------------------------------------------------------------------------

def test_apply_rules_returns_tagged_line():
    rules = [TagRule(tag="err", pattern="error")]
    result = apply_rules("error occurred", rules)
    assert isinstance(result, TaggedLine)
    assert "err" in result.tags


def test_apply_rules_multiple_rules_can_match():
    rules = [
        TagRule(tag="err", pattern="error"),
        TagRule(tag="disk", pattern="disk"),
    ]
    result = apply_rules("disk error", rules)
    assert "err" in result.tags
    assert "disk" in result.tags


def test_apply_rules_no_match_gives_empty_tags():
    rules = [TagRule(tag="err", pattern="error")]
    result = apply_rules("everything is fine", rules)
    assert result.tags == []


# ---------------------------------------------------------------------------
# tag_lines
# ---------------------------------------------------------------------------

def test_tag_lines_yields_all_by_default():
    lines = ["error here", "info only", "another error"]
    rules = [TagRule(tag="err", pattern="error")]
    results = list(tag_lines(lines, rules))
    assert len(results) == 3


def test_tag_lines_tagged_only_filters_untagged():
    lines = ["error here", "info only", "another error"]
    rules = [TagRule(tag="err", pattern="error")]
    results = list(tag_lines(lines, rules, tagged_only=True))
    assert len(results) == 2
    assert all(r.tagged for r in results)


def test_tag_lines_empty_rules_no_tags():
    lines = ["error here", "warn there"]
    results = list(tag_lines(lines, []))
    assert all(not r.tagged for r in results)


# ---------------------------------------------------------------------------
# count_by_tag
# ---------------------------------------------------------------------------

def test_count_by_tag_basic():
    tagged = [
        TaggedLine("a", ["err"]),
        TaggedLine("b", ["err", "warn"]),
        TaggedLine("c", ["warn"]),
    ]
    counts = count_by_tag(tagged)
    assert counts["err"] == 2
    assert counts["warn"] == 2


def test_count_by_tag_empty_input():
    assert count_by_tag([]) == {}


# ---------------------------------------------------------------------------
# rules_from_dict
# ---------------------------------------------------------------------------

def test_rules_from_dict_creates_tag_rules():
    raw = [{"tag": "error", "pattern": "error"}]
    rules = rules_from_dict(raw)
    assert len(rules) == 1
    assert rules[0].tag == "error"


def test_rules_from_dict_case_sensitive_flag():
    raw = [{"tag": "t", "pattern": "X", "case_sensitive": True}]
    rules = rules_from_dict(raw)
    assert rules[0].case_sensitive is True
    assert rules[0].matches("x") is False
    assert rules[0].matches("X") is True
