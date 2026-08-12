"""Finite probability-gate / stacked-EOG ensemble development screen.

Hard family selection showed complementary failure modes on the already-open noisy
development seeds: the stacked model can overconfidently miscalibrate dispersal-limited
cases, whereas the conservative probability gate can overconfidently fail some
stepping-stone cases. This screen therefore evaluates a fixed convex ensemble without
adding a new response fit:

    D_alpha = (1 - alpha) * D_probability + alpha * D_stack

The alpha grid is finite and declared in source. This is development evidence only;
independent confirmation seeds remain untouched.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eog import fit_eog_distribution
from eog.distribution_stack import EOGStackedFusionConfig, fit_eog_stacked_distribution
from benchmarks.distribution_model_noisy_regimes import (
    DEVELOPMENT_SEEDS,
    REGIMES,
    _auc,
    _brier,
    build_noisy_landscape,
)


ALPHA_GRID = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
NULL_REGIMES = ("habitat_only", "long_jump")
STRUCTURAL_REGIMES = (
    "dispersal_limited",
    "graded_barrier",
    "stepping_stone",
    "mixed",
)


def _log_loss(labels, scores):
    labels = np.asarray(labels, dtype=float)
    scores = np.clip(np.asarray(scores, dtype=float), 1e-12, 1.0 - 1e-12)
    return float(
        np.mean(-(labels * np.log(scores) + (1.0 - labels) * np.log1p(-scores)))
    )


def run_structural_ensemble_development(
    *,
    seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
    n_modules: int = 24,
):
    per_regime = {regime: [] for regime in REGIMES}
    integrity = {
        "same_declared_development_seeds": seeds == DEVELOPMENT_SEEDS,
        "all_target_labels_held_out": True,
        "all_probability_models_cross_fitted": True,
        "all_stack_models_cross_fitted": True,
        "all_predictions_finite": True,
    }

    for regime in REGIMES:
        for seed in seeds:
            bundle = build_noisy_landscape(regime, seed, n_modules=n_modules)
            probability = fit_eog_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                bundle.config,
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"ensemble probability {regime} seed {seed}",
            )
            stack = fit_eog_stacked_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                EOGStackedFusionConfig(
                    base_config=bundle.config,
                    fusion_l2_penalty=1.0,
                ),
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"ensemble stack {regime} seed {seed}",
            )
            probability_prediction = probability.predict(bundle.target_ids)
            stack_prediction = stack.predict(bundle.target_ids)
            labels = np.asarray(bundle.target_response, dtype=int)
            p = np.asarray(probability_prediction.distribution_support, dtype=float)
            s = np.asarray(stack_prediction.distribution_support, dtype=float)
            h = np.asarray(probability_prediction.environmental_support, dtype=float)

            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_probability_models_cross_fitted"] &= bool(
                probability.structural_gate_cross_fitted
            )
            integrity["all_stack_models_cross_fitted"] &= bool(stack.gate_fold_ids)
            integrity["all_predictions_finite"] &= bool(
                np.isfinite(p).all() and np.isfinite(s).all() and np.isfinite(h).all()
            )

            metrics = {}
            for alpha in ALPHA_GRID:
                ensemble = (1.0 - alpha) * p + alpha * s
                metrics[str(alpha)] = {
                    "auc": _auc(labels, ensemble),
                    "brier": _brier(labels, ensemble),
                    "log_loss": _log_loss(labels, ensemble),
                }
            per_regime[regime].append(
                {
                    "seed": seed,
                    "environmental": {
                        "auc": _auc(labels, h),
                        "brier": _brier(labels, h),
                        "log_loss": _log_loss(labels, h),
                    },
                    "alpha_metrics": metrics,
                }
            )

    summary = {}
    for regime, rows in per_regime.items():
        env = {
            metric: float(np.mean([row["environmental"][metric] for row in rows]))
            for metric in ("auc", "brier", "log_loss")
        }
        alpha_summary = {}
        for alpha in ALPHA_GRID:
            key = str(alpha)
            values = {
                metric: float(
                    np.mean([row["alpha_metrics"][key][metric] for row in rows])
                )
                for metric in ("auc", "brier", "log_loss")
            }
            values.update(
                {
                    "minus_environmental_auc": values["auc"] - env["auc"],
                    "minus_environmental_brier": values["brier"] - env["brier"],
                    "minus_environmental_log_loss": values["log_loss"]
                    - env["log_loss"],
                    "worst_seed_log_loss_harm": float(
                        max(
                            row["alpha_metrics"][key]["log_loss"]
                            - row["environmental"]["log_loss"]
                            for row in rows
                        )
                    ),
                }
            )
            alpha_summary[key] = values
        summary[regime] = {
            "environmental": env,
            "alpha": alpha_summary,
        }

    candidates = []
    for alpha in ALPHA_GRID:
        key = str(alpha)
        null_max_harm = max(
            summary[regime]["alpha"][key]["minus_environmental_log_loss"]
            for regime in NULL_REGIMES
        )
        structural_gains = {
            regime: -summary[regime]["alpha"][key]["minus_environmental_log_loss"]
            for regime in STRUCTURAL_REGIMES
        }
        candidates.append(
            {
                "alpha": alpha,
                "null_max_mean_log_loss_harm": float(null_max_harm),
                "minimum_structural_mean_log_loss_gain": float(
                    min(structural_gains.values())
                ),
                "mean_structural_log_loss_gain": float(
                    np.mean(list(structural_gains.values()))
                ),
                "maximum_seed_log_loss_harm": float(
                    max(
                        summary[regime]["alpha"][key]["worst_seed_log_loss_harm"]
                        for regime in REGIMES
                    )
                ),
                "safe_null_mean_log_loss": null_max_harm <= 1e-12,
                "all_structural_regimes_improve_mean_log_loss": all(
                    value > 0.0 for value in structural_gains.values()
                ),
            }
        )

    eligible = [
        item
        for item in candidates
        if item["safe_null_mean_log_loss"]
        and item["all_structural_regimes_improve_mean_log_loss"]
    ]
    recommended = None
    if eligible:
        # Development recommendation: maximize the weakest structural proper-score
        # gain, then minimize worst seed harm, then prefer the smaller stack weight.
        recommended = max(
            eligible,
            key=lambda item: (
                item["minimum_structural_mean_log_loss_gain"],
                -item["maximum_seed_log_loss_harm"],
                -item["alpha"],
            ),
        )

    return {
        "schema": "eog_structural_ensemble_development_v0_1",
        "status": "development_screen_not_confirmation",
        "alpha_grid": list(ALPHA_GRID),
        "null_regimes": list(NULL_REGIMES),
        "structural_regimes": list(STRUCTURAL_REGIMES),
        "integrity_checks": integrity,
        "all_integrity_checks_pass": bool(all(integrity.values())),
        "summary": summary,
        "candidates": candidates,
        "recommended_alpha": recommended,
        "per_regime": per_regime,
        "claim_boundary": (
            "fixed convex-ensemble development on already-open seeds only; any chosen "
            "alpha must be frozen before independent confirmation seeds are executed"
        ),
    }


def main():
    result = run_structural_ensemble_development()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_integrity_checks_pass"]:
        raise SystemExit("EOG structural ensemble development failed integrity checks")


if __name__ == "__main__":
    main()
