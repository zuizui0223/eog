"""Command-line entry point for prospective EOG v2 genetic validation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .genetic_validation import GeneticValidationConfig
from .genetic_validation_io import run_genetic_validation_from_csv


def _result_payload(bundle) -> dict[str, object]:
    validation = bundle.validation
    return {
        "status": "prospective-eog-v2-independent-genetic-validation",
        "population_ids": [record.population_id for record in bundle.populations],
        "n_populations": len(bundle.populations),
        "n_observed_genetic_pairs": bundle.response.n_observed_pairs,
        "predictor_fingerprint": bundle.predictors.fingerprint,
        "response_fingerprint": bundle.response.fingerprint,
        "validation_fingerprint": validation.fingerprint,
        "bundle_fingerprint": bundle.fingerprint,
        "config": asdict(validation.config),
        "models": [
            {
                "model_id": model.model_id,
                "predictor_names": list(model.predictor_names),
                "n_estimable_folds": model.n_estimable_folds,
                "n_total_folds": model.n_total_folds,
                "n_predictions": model.n_predictions,
                "mse": model.mse,
                "mae": model.mae,
                "folds": [asdict(fold) for fold in model.folds],
            }
            for model in validation.models
        ],
        "contrasts": [asdict(contrast) for contrast in validation.contrasts],
        "interpretation": (
            "predictive leave-one-population-out comparison of independently frozen "
            "IBD/IBE/EOG predictors against a symmetric genetic-distance response; "
            "negative augmented-minus-reference contrasts indicate lower prediction error"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run prospective EOG v2 leave-one-population-out genetic validation from "
            "separately fingerprinted predictor and response CSV files."
        )
    )
    parser.add_argument("--populations", required=True, type=Path)
    parser.add_argument("--predictors", required=True, type=Path)
    parser.add_argument("--genetic-response", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--response-transform",
        choices=("identity", "linearized_fst"),
        default="identity",
    )
    parser.add_argument("--ridge-penalty", type=float, default=1.0)
    args = parser.parse_args(argv)

    bundle = run_genetic_validation_from_csv(
        args.populations,
        args.predictors,
        args.genetic_response,
        config=GeneticValidationConfig(
            response_transform=args.response_transform,
            ridge_penalty=args.ridge_penalty,
        ),
    )
    payload = _result_payload(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
