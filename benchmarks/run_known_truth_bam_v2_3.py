#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_v2_3 import run_bam_intervention_v23


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v2_3/result_v2_3.json"),
    )
    args = parser.parse_args()
    result = run_bam_intervention_v23()
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
                    "number_of_passive_equivalence_classes",
                    "P_only_alias_classes",
                    "H_only_alias_classes",
                    "P_alias_classes_split",
                    "H_alias_classes_split",
                    "axis_specificity_violations",
                    "number_of_intervention_augmented_classes",
                    "intervention_augmented_class_size_distribution",
                    "world_fraction_uniquely_identified_after_intervention",
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
