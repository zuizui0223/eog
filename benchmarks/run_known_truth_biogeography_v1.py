#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_biogeography import run_canonical_known_truth_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_biogeography_v1/canonical_result_v1.json"),
    )
    args = parser.parse_args()
    result = run_canonical_known_truth_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
