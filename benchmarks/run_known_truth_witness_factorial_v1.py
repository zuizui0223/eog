#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_biogeography import run_witness_factorial_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/known_truth_biogeography_v1/"
            "witness_factorial_result_v1.json"
        ),
    )
    args = parser.parse_args()
    result = run_witness_factorial_benchmark()
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
                    "eligible_exact_cases",
                    "truth_retention_failures",
                    "f1_criterion_mismatches",
                    "f2_monotonicity_violations",
                    "f3_equivalence_violations",
                    "f4_boundary_violations",
                    "identifiable_at_full_coverage_fraction",
                    "observational_equivalence_fraction",
                    "identification_rate_by_sampling_coverage",
                    "omitted_truth_falsification_fraction",
                    "omitted_truth_survival_fraction",
                    "runtime_seconds",
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
