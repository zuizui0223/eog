"""Development comparison of probability- and odds-scale EOG accessibility gates.

This benchmark uses exactly the already-declared noisy development seeds and regimes.
It is therefore eligible for model development but not for confirmation. No promotion
threshold is introduced here; the purpose is to decide which fusion operator should be
frozen before an independent-seed confirmation.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

# Direct script execution places ``benchmarks/`` rather than the repository root on
# sys.path. Add the root explicitly so this development runner can reuse the frozen
# noisy-generator module both locally and in GitHub Actions.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eog import fit_eog_distribution
from eog.distribution_odds import EOGOddsGateConfig, fit_eog_odds_distribution
from benchmarks.distribution_model_noisy_regimes import (
    DEVELOPMENT_SEEDS,
    REGIMES,
    _auc,
    _brier,
    _fit_comparator_predictions,
    build_noisy_landscape,
)


def run_fusion_development(
    *,
    seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
    n_modules: int = 24,
) -> dict[str, object]:
    per_regime: dict[str, list[dict[str, object]]] = {regime: [] for regime in REGIMES}
    integrity = {
        "same_declared_development_seeds": seeds == DEVELOPMENT_SEEDS,
        "all_target_labels_held_out": True,
        "all_probability_gates_inner_cross_fitted": True,
        "all_odds_gates_inner_cross_fitted": True,
        "all_scores_finite": True,
    }

    for regime in REGIMES:
        for seed in seeds:
            bundle = build_noisy_landscape(regime, seed, n_modules=n_modules)
            probability_model = fit_eog_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                bundle.config,
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"fusion development probability {regime} seed {seed}",
            )
            odds_model = fit_eog_odds_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                EOGOddsGateConfig(
                    base_config=bundle.config,
                    maximum_strength=4.0,
                    strength_grid_size=201,
                    structural_gate_penalty=0.02,
                ),
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"fusion development odds {regime} seed {seed}",
            )
            scores = _fit_comparator_predictions(bundle, probability_model)
            scores["eog_probability_gate"] = scores.pop("eog_distribution_support")
            scores["eog_odds_gate"] = odds_model.predict(
                bundle.target_ids
            ).distribution_support
            labels = np.asarray(bundle.target_response, dtype=int)

            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_probability_gates_inner_cross_fitted"] &= bool(
                probability_model.structural_gate_cross_fitted
            )
            integrity["all_odds_gates_inner_cross_fitted"] &= bool(
                odds_model.structural_gate_cross_fitted
            )
            integrity["all_scores_finite"] &= all(
                np.isfinite(np.asarray(values, dtype=float)).all()
                for values in scores.values()
            )

            per_regime[regime].append(
                {
                    "seed": seed,
                    "probability_gate_weight": probability_model.structural_gate_weight,
                    "odds_gate_strength": odds_model.structural_gate_strength,
                    "probability_gate_training_log_loss": probability_model.training_gate_log_loss,
                    "odds_gate_training_log_loss": odds_model.training_gate_log_loss,
                    "auc": {name: _auc(labels, values) for name, values in scores.items()},
                    "brier": {name: _brier(labels, values) for name, values in scores.items()},
                }
            )

    summary: dict[str, object] = {}
    for regime, rows in per_regime.items():
        methods = tuple(rows[0]["auc"])
        probability_auc = np.asarray(
            [row["auc"]["eog_probability_gate"] for row in rows], dtype=float
        )
        odds_auc = np.asarray(
            [row["auc"]["eog_odds_gate"] for row in rows], dtype=float
        )
        probability_brier = np.asarray(
            [row["brier"]["eog_probability_gate"] for row in rows], dtype=float
        )
        odds_brier = np.asarray(
            [row["brier"]["eog_odds_gate"] for row in rows], dtype=float
        )
        summary[regime] = {
            "mean_probability_gate_weight": float(
                np.mean([row["probability_gate_weight"] for row in rows])
            ),
            "mean_odds_gate_strength": float(
                np.mean([row["odds_gate_strength"] for row in rows])
            ),
            "mean_auc": {
                method: float(np.mean([row["auc"][method] for row in rows]))
                for method in methods
            },
            "mean_brier": {
                method: float(np.mean([row["brier"][method] for row in rows]))
                for method in methods
            },
            "odds_minus_probability_mean_auc": float(
                np.mean(odds_auc - probability_auc)
            ),
            "odds_minus_probability_mean_brier": float(
                np.mean(odds_brier - probability_brier)
            ),
            "odds_auc_better_seed_fraction": float(np.mean(odds_auc > probability_auc)),
            "odds_brier_better_seed_fraction": float(
                np.mean(odds_brier < probability_brier)
            ),
        }

    return {
        "schema": "eog_distribution_fusion_development_v0_1",
        "status": "development_screen_not_confirmation",
        "seeds": list(seeds),
        "regimes": list(REGIMES),
        "integrity_checks": integrity,
        "all_integrity_checks_pass": bool(all(integrity.values())),
        "summary": summary,
        "per_regime": per_regime,
        "claim_boundary": (
            "same-seed development comparison only; any selected fusion and promotion "
            "thresholds must be frozen before an independent-seed confirmation"
        ),
    }


def main() -> None:
    result = run_fusion_development()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_integrity_checks_pass"]:
        raise SystemExit("EOG fusion development screen failed integrity checks")


if __name__ == "__main__":
    main()
