#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.bam_targeted_measurement_audit import (
    run_targeted_measurement_exact_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/bam_identifiability_theory_v1/"
            "targeted_measurement_exact_audit_v1.json"
        ),
    )
    args = parser.parse_args()
    result = run_targeted_measurement_exact_audit()
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
                    "systems_scored",
                    "truth_cases",
                    "greedy_equal_to_exact_count",
                    "greedy_suboptimal_count",
                    "max_exact_A",
                    "max_exact_B",
                    "max_exact_AB_joint",
                    "max_exact_M",
                    "max_exact_tau",
                    "max_exact_M_tau_joint",
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
