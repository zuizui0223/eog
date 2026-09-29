#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.joint_ecology_observation import run_joint_ecology_observation_v27


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/joint_ecology_observation_v2_7/result_v2_7.json"
        ),
    )
    args = parser.parse_args()
    result = run_joint_ecology_observation_v27()
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
                    "selected_target_node",
                    "target_present_world_count",
                    "target_absent_world_count",
                    "truth_ecological_world_id",
                    "strict_ecological_projection_count",
                    "broad_ecological_projection_count",
                    "resurrected_ecological_world_count",
                    "calibrated_ecological_projection_count",
                    "target_present_survivors_by_nondetection_count",
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
