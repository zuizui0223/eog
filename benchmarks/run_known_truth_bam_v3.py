#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eog.v2.known_truth_bam_v3 import run_bam_active_intervention_v3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v3/result_v3.json"),
    )
    args = parser.parse_args()
    result = run_bam_active_intervention_v3()
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
                    "candidate_world_count",
                    "distinct_complete_intervention_signatures",
                    "axis_orthogonality_audit",
                    "unique_truth_fraction_before_intervention",
                    "unique_truth_fraction_after_active_intervention",
                    "median_interventions_to_terminal",
                    "max_interventions_to_terminal",
                    "terminal_signature_equivalence_class_size_distribution",
                    "axis_first_frequency",
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
