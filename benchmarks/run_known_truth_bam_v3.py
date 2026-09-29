#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_generality import run_bam_generality_v3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_bam_v3/result_v3.json"),
    )
    args = parser.parse_args()
    result = run_bam_generality_v3()
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
                    "system_roster_size",
                    "scored_system_count",
                    "design_stop_count",
                    "eligible_truth_count",
                    "pooled_bam_state_unique_fraction",
                    "verdicts",
                    "runtime_seconds",
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
