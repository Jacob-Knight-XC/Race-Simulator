#!/usr/bin/env python3
"""Refresh data/ustfccca_national_poll.json from the live USTFCCCA API."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from ustfccca_poll import write_snapshot  # noqa: E402


def main() -> int:
    path = write_snapshot(ROOT / "data" / "ustfccca_national_poll.json")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
