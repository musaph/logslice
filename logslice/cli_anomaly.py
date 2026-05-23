"""CLI entry-point for anomaly detection in log files."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.anomaly_detector import detect_anomalies, format_anomaly
from logslice.reader import LogReadError, iter_lines


def build_anomaly_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=prog or "logslice-anomaly",
        description="Detect anomalous bursts in a log file using z-score on time buckets.",
    )
    p.add_argument("file", nargs="?", default="-", help="Log file path (default: stdin).")
    p.add_argument(
        "--bucket",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Bucket width in seconds (default: 60).",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        metavar="Z",
        help="Z-score threshold to flag a bucket (default: 2.0).",
    )
    p.add_argument(
        "--count",
        action="store_true",
        help="Print only the number of anomalous lines.",
    )
    return p


def _stdin_lines() -> List[str]:
    return sys.stdin.read().splitlines()


def run_anomaly(argv: Optional[List[str]] = None, out=None, err=None) -> int:
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    parser = build_anomaly_parser()
    args = parser.parse_args(argv)

    try:
        if args.file == "-":
            raw_lines = _stdin_lines()
        else:
            raw_lines = list(iter_lines(args.file))
    except LogReadError as exc:
        err.write(f"error: {exc}\n")
        return 1

    results = list(
        detect_anomalies(
            raw_lines,
            bucket_seconds=args.bucket,
            z_threshold=args.threshold,
        )
    )

    if args.count:
        out.write(f"{len(results)}\n")
        return 0

    for result in results:
        out.write(format_anomaly(result) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_anomaly())


if __name__ == "__main__":  # pragma: no cover
    main()
