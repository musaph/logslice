"""Entry-point shim for the logslice-diff console script.

This module serves as the entry point for the ``logslice-diff`` console
script defined in the project's packaging configuration. It delegates
all logic to :func:`logslice.cli_diff.main`.
"""
from logslice.cli_diff import main

if __name__ == "__main__":  # pragma: no cover
    main()
