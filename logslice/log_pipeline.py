"""log_pipeline.py — Composable pipeline for chaining log processing steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, List, Optional

Line = str
Step = Callable[[Iterable[Line]], Iterator[Line]]


@dataclass
class Pipeline:
    """An ordered sequence of processing steps applied lazily to log lines."""

    steps: List[Step] = field(default_factory=list)

    def pipe(self, step: Step) -> "Pipeline":
        """Append *step* and return *self* for fluent chaining."""
        self.steps.append(step)
        return self

    def run(self, source: Iterable[Line]) -> Iterator[Line]:
        """Apply all steps in order and yield the resulting lines."""
        stream: Iterable[Line] = source
        for step in self.steps:
            stream = step(stream)
        yield from stream

    def __len__(self) -> int:
        return len(self.steps)


def make_pipeline(*steps: Step) -> Pipeline:
    """Create a :class:`Pipeline` pre-loaded with *steps*."""
    p = Pipeline()
    for s in steps:
        p.pipe(s)
    return p


def run_pipeline(
    source: Iterable[Line],
    *steps: Step,
    limit: Optional[int] = None,
) -> List[Line]:
    """Convenience wrapper: build a pipeline, run it, return a list.

    Args:
        source: Iterable of raw log lines.
        *steps: Processing callables to apply in order.
        limit: If given, truncate output to at most *limit* lines.

    Returns:
        List of processed lines.
    """
    pipeline = make_pipeline(*steps)
    result: List[Line] = []
    for line in pipeline.run(source):
        result.append(line)
        if limit is not None and len(result) >= limit:
            break
    return result
