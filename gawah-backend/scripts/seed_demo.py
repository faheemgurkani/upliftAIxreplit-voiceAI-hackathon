#!/usr/bin/env python3
"""CLI wrapper — seed three demo statements + cluster + calls.

Usage (from gawah-backend):
  python scripts/seed_demo.py
  python scripts/seed_demo.py --replace
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.demo_seed import CLUSTER_ID, REF_A, seed_demo_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Gawah demo store for judge tour")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove previous seed refs/calls/cluster before writing",
    )
    args = parser.parse_args()

    result = seed_demo_store(replace=args.replace)
    print("Demo seed ready.")
    print(f"  Store: {result['store']}")
    print(f"  Open first:  /dashboard → {REF_A}")
    print(f"  Cluster:     /clusters/{CLUSTER_ID}")
    print("  Then:        /calls  (3 completed sessions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
