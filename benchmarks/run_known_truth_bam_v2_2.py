#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_direct_evidence import run_direct_evidence_v22


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2_2/result_v2_2.json"),
    )
    args = parser.parse_args()
    result = run_direct_evidence_v22()
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
                    "exact_bam_state_count",
                    "exact_parameter_alias_count",
                    "bam_state_unique_fraction_E0",
                    "bam_state_unique_fraction_E1",
                    "bam_state_unique_fraction_E2",
                    "bam_state_unique_fraction_E3",
                    "bam_state_unique_fraction_E4",
                    "parameter_unique_fraction_E4",
                    "residual_nonidentifiable_cases_after_E4",
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
