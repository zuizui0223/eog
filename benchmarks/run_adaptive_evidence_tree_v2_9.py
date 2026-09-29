#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.adaptive_evidence_tree import run_adaptive_evidence_v29


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/adaptive_evidence_tree_v2_9/result_v2_9.json"
        ),
    )
    args = parser.parse_args()
    result = run_adaptive_evidence_v29()
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
                    "minimum_worst_case_depth",
                    "optimal_first_actions",
                    "canonical_first_action",
                    "first_action_worst_case_depths",
                    "known_truth_realized_depth",
                    "ablation_without_calibration",
                    "ablation_without_state_assay",
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
