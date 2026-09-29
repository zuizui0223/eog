#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.falsification_driven_design import plan_v24


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/falsification_driven_design_v2_4/result_v2_4.json"
        ),
    )
    args = parser.parse_args()
    result = plan_v24()
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
                    "world_count",
                    "passive_unresolved_pair_count",
                    "ranked_interventions",
                    "minimum_separating_set",
                    "minimum_set_size",
                    "all_worlds_separated",
                    "pair_cover_mismatches",
                    "final_class_size_distribution",
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
