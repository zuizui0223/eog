#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_v2_1 import run_bam_v21


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2_1/result_v2_1.json"),
    )
    args = parser.parse_args()
    result = run_bam_v21()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: result.get(key)
                for key in (
                    "status",
                    "scoring_performed",
                    "candidate_world_count",
                    "eligible_truth_worlds",
                    "fraction_truth_unique_positive_only",
                    "fraction_truth_unique_with_negatives",
                    "fraction_truth_unique_with_temporal_evidence",
                    "negative_rescue_fraction",
                    "temporal_M_rescue_fraction",
                    "verdicts",
                    "fingerprint",
                )
                if key in result
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(json.dumps({"activation": result["activation"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
