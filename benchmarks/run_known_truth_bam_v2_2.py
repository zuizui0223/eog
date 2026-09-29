#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eog.v2.known_truth_bam_v2_2 import run_bam_v22


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2_2/result_v2_2.json"),
    )
    args = parser.parse_args()
    result = run_bam_v22()
    result["fingerprint"] = hashlib.sha256(
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
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
                    "status",
                    "activation_audit",
                    "candidate_world_count",
                    "eligible_truth_worlds",
                    "fraction_truth_unique_positive_only",
                    "fraction_truth_unique_with_negatives",
                    "fraction_truth_unique_with_temporal_evidence",
                    "negative_rescue_fraction",
                    "temporal_M_rescue_fraction",
                    "partner_dependency_diagnostic_cases",
                    "partner_no_B_survives_positive",
                    "partner_no_B_eliminated_by_negatives",
                    "antagonist_dependency_diagnostic_cases",
                    "antagonist_no_B_survives_positive",
                    "antagonist_no_B_eliminated_by_negatives",
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
