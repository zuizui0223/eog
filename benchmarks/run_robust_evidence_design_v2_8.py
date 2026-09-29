#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.robust_evidence_design import run_robust_set_valued_v28


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/robust_set_valued_evidence_v2_8/result_v2_8.json"
        ),
    )
    args = parser.parse_args()
    result = run_robust_set_valued_v28()
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
                    "active_joint_hypotheses",
                    "unresolved_pair_count",
                    "robust_split_pair_count_by_action",
                    "minimum_robust_separating_set",
                    "minimum_robust_set_size",
                    "known_truth_after_calibration",
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
