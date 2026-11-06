#!/usr/bin/env python3
"""Refresh USTFCCCA national poll snapshots (DIII + NAIA) from the live API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from ustfccca_poll import POLL_BY_DIVISION, write_all_snapshots, write_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--division",
        choices=["all", *POLL_BY_DIVISION.keys()],
        default="all",
        help="Which poll snapshot(s) to refresh (default: all)",
    )
    args = parser.parse_args()
    if args.division == "all":
        paths = write_all_snapshots()
    else:
        paths = [write_snapshot(division_key=args.division)]
    for path in paths:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
