"""Command-line interface for audited hypothesis survey prioritization."""
from __future__ import annotations

import argparse
from pathlib import Path

from .hypothesis_discrimination import HypothesisDiscriminationWeights
from .hypothesis_survey_io import run_hypothesis_survey_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eog-hypothesis-survey",
        description="Rank survey candidates from declared bridge-scenario families.",
    )
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--families", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--support-range-weight", type=float, default=1.0)
    parser.add_argument("--pairwise-separation-weight", type=float, default=1.0)
    parser.add_argument("--survey-deficit-weight", type=float, default=1.0)
    parser.add_argument("--accessibility-penalty-weight", type=float, default=1.0)
    parser.add_argument(
        "--allow-unassigned-scenarios",
        action="store_true",
        help="Allow sensitivity scenarios that are absent from the family declaration.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    weights = HypothesisDiscriminationWeights(
        support_range=args.support_range_weight,
        pairwise_separation=args.pairwise_separation_weight,
        survey_deficit=args.survey_deficit_weight,
        accessibility_penalty=args.accessibility_penalty_weight,
    )
    bundle = run_hypothesis_survey_csv(
        args.scenarios,
        args.families,
        args.candidates,
        args.output_dir,
        weights=weights,
        require_complete_assignment=not args.allow_unassigned_scenarios,
    )
    print(f"ranking_csv={bundle.ranking_csv_path}")
    print(f"manifest_json={bundle.manifest_json_path}")
    print(f"bundle_fingerprint={bundle.fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
