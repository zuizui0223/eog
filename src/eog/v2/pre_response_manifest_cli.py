"""CLI for the declarative EOG-WF v2 pre-response manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from eog.v2.pre_response_manifest import write_pre_response_manifest_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eog-v2-pre-response-certify",
        description=(
            "Build a response-locked EOG-WF v2 pre-response certificate from a "
            "local declarative manifest. This command never opens biological responses."
        ),
    )
    parser.add_argument("manifest", type=Path, help="UTF-8 JSON manifest")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path for the deterministic JSON certificate result",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = write_pre_response_manifest_result(args.manifest, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "certificate_fingerprint": result["certificate"]["fingerprint"],
                "structural_status": result["certificate"]["structural_status"],
                "predictive_status": result["certificate"]["predictive_status"],
                "predictive_outcome_access_allowed": result["certificate"][
                    "predictive_outcome_access_allowed"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
