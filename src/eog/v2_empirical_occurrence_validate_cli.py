"""CLI for scoring a frozen EOG v2 occurrence feature bundle."""
from __future__ import annotations

import argparse
from pathlib import Path

from .v2_empirical_occurrence_io import (
    read_feature_bundle,
    read_occurrence_response_csv,
    write_validation_result,
)
from .v2_empirical_occurrence_validation import (
    evaluate_fixed_source_occurrence_validation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eog-v2-occurrence-validate",
        description=(
            "Attach surveyed incidence outcomes to a previously frozen EOG v2 feature "
            "bundle and run predeclared held-out evaluation."
        ),
    )
    parser.add_argument("--features", type=Path, required=True, help="Frozen feature-bundle JSON")
    parser.add_argument(
        "--responses",
        type=Path,
        required=True,
        help="CSV with exactly node_id,response,fold_id; use blank/NA for unsurveyed nodes",
    )
    parser.add_argument("--l2-penalty", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True, help="Validation result JSON")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    features = read_feature_bundle(args.features)
    response, folds = read_occurrence_response_csv(args.responses, features.node_ids)
    result = evaluate_fixed_source_occurrence_validation(
        features,
        response,
        folds,
        l2_penalty=args.l2_penalty,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_validation_result(args.output, result)
    print(f"feature_fingerprint={result.feature_fingerprint}")
    print(f"n_evaluated={result.n_evaluated}")
    print(f"n_missing_response={result.n_missing_response}")


if __name__ == "__main__":
    main()
