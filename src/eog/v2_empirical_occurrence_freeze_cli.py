"""CLI for freezing response-free EOG v2 empirical occurrence predictors."""
from __future__ import annotations

import argparse
from pathlib import Path

from .v2_empirical_occurrence_io import (
    freeze_occurrence_features_from_csv,
    write_feature_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eog-v2-occurrence-freeze",
        description=(
            "Freeze fixed-source EOG v2 occurrence predictors before empirical target "
            "responses are attached."
        ),
    )
    parser.add_argument("--nodes", type=Path, required=True, help="Response-free nodes CSV")
    parser.add_argument("--edges", type=Path, required=True, help="Directed edge-support CSV")
    parser.add_argument("--max-steps", type=int, required=True, help="Frozen propagation depth")
    parser.add_argument(
        "--loss-support",
        type=float,
        default=1.0,
        help="Positive explicit loss support used to build the sub-stochastic operator",
    )
    parser.add_argument("--output", type=Path, required=True, help="Feature-bundle JSON")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    features = freeze_occurrence_features_from_csv(
        args.nodes,
        args.edges,
        max_steps=args.max_steps,
        loss_support=args.loss_support,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_feature_bundle(args.output, features)
    print(f"feature_fingerprint={features.feature_fingerprint}")
    print(f"operator_fingerprint={features.operator_fingerprint}")


if __name__ == "__main__":
    main()
