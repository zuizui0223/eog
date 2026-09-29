#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_direct_movement import run_direct_movement_v23


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2_3/result_v2_3.json"),
    )
    args = parser.parse_args()
    result = run_direct_movement_v23()
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
                    "candidate_world_count",
                    "eligible_truth_worlds",
                    "bam_state_unique_fraction_E4",
                    "bam_state_unique_fraction_E5",
                    "bam_state_unique_fraction_E6",
                    "parameter_unique_fraction_E6",
                    "residual_nonidentifiable_cases_after_E6",
                    "minimal_direct_M_accessibility_measurements_distribution",
                    "minimal_direct_M_arrival_measurements_distribution",
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
