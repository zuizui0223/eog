#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam import run_bam_factorial_v2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2/factorial_result_v2.json"),
    )
    args = parser.parse_args()
    result = run_bam_factorial_v2()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "eligible_truth_worlds",
                    "candidate_world_count",
                    "truth_retention_failures",
                    "axis_witness_mismatches",
                    "equivalence_violations",
                    "positive_superset_violations",
                    "negative_rescue_failures",
                    "temporal_rescue_failures",
                    "fraction_truth_unique_positive_only",
                    "fraction_truth_unique_with_negatives",
                    "fraction_truth_unique_with_temporal_evidence",
                    "negative_rescue_fraction",
                    "temporal_M_rescue_fraction",
                    "axis_witness_counts",
                    "verdicts",
                    "fingerprint",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
