#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "eligible_truth_worlds": result["eligible_truth_worlds"],
                "unique_truth_fractions": result["unique_truth_fractions"],
                "complete_state_equivalence_class_size_distribution": result[
                    "complete_state_equivalence_class_size_distribution"
                ],
                "verdicts": result["verdicts"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
