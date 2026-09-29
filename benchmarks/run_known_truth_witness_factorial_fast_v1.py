#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_biogeography_fast import (
    FROZEN_REFERENCE_FINGERPRINT,
    run_witness_factorial_benchmark_fast,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/known_truth_biogeography_v1/"
            "fast_backend_result_v1.json"
        ),
    )
    args = parser.parse_args()
    result = run_witness_factorial_benchmark_fast()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "runtime_seconds": result["runtime_seconds"],
                "fingerprint": result["fingerprint"],
                "reference_fingerprint": FROZEN_REFERENCE_FINGERPRINT,
                "reference_fingerprint_match": result[
                    "reference_fingerprint_match"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not result["reference_fingerprint_match"]:
        raise SystemExit("fast backend does not match frozen scientific result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
