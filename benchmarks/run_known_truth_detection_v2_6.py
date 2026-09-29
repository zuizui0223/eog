#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.known_truth_detection import run_detection_boundary_v26


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/known_truth_detection_v2_6/result_v2_6.json"),
    )
    args = parser.parse_args()
    result = run_detection_boundary_v26()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "failure_counts": result["failure_counts"],
                "strict_positive_falsified_states": result[
                    "strict_positive_falsified_states"
                ],
                "expanded_positive_falsified_states": result[
                    "expanded_positive_falsified_states"
                ],
                "strict_negative_falsified_states": result[
                    "strict_negative_falsified_states"
                ],
                "expanded_negative_falsified_states": result[
                    "expanded_negative_falsified_states"
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
