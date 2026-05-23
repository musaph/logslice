"""Tag log lines with user-defined labels based on keyword or pattern rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class TagRule:
    """A rule that maps a pattern to a tag label."""
    tag: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class TaggedLine:
    """A log line together with the tags applied to it."""
    line: str
    tags: List[str] = field(default_factory=list)

    @property
    def tagged(self) -> bool:
        return len(self.tags) > 0

    def formatted(self, separator: str = "|") -> str:
        if not self.tags:
            return self.line
        label = separator.join(sorted(set(self.tags)))
        return f"[{label}] {self.line}"


def apply_rules(line: str, rules: List[TagRule]) -> TaggedLine:
    """Apply all matching rules to a single line and return a TaggedLine."""
    tags = [rule.tag for rule in rules if rule.matches(line)]
    return TaggedLine(line=line, tags=tags)


def tag_lines(
    lines: Iterable[str],
    rules: List[TagRule],
    tagged_only: bool = False,
) -> Iterator[TaggedLine]:
    """Yield TaggedLine objects for each input line.

    Args:
        lines: Input log lines.
        rules: Tag rules to evaluate against each line.
        tagged_only: If True, skip lines that match no rules.
    """
    for line in lines:
        result = apply_rules(line, rules)
        if tagged_only and not result.tagged:
            continue
        yield result


def count_by_tag(tagged: Iterable[TaggedLine]) -> dict:
    """Return a mapping of tag -> count across all tagged lines."""
    counts: dict = {}
    for tl in tagged:
        for tag in tl.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def rules_from_dict(raw: List[dict]) -> List[TagRule]:
    """Build TagRule objects from a list of plain dicts (e.g. parsed from JSON)."""
    result = []
    for item in raw:
        result.append(TagRule(
            tag=item["tag"],
            pattern=item["pattern"],
            case_sensitive=bool(item.get("case_sensitive", False)),
        ))
    return result
