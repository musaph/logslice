"""Thin __main__-style entry point registered in setup / pyproject for
``logslice-pattern`` console script.

Keeping this separate from cli_pattern.py mirrors the pattern used by
cli_field.py / __main__.py so each sub-command can be invoked directly.
"""
from __future__ import annotations

import sys

from logslice.cli_pattern import main

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
