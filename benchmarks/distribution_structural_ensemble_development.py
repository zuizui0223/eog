"""Finite probability-gate / stacked-EOG ensemble development screen.

Hard family selection showed complementary failure modes on the already-open noisy
development seeds: the stacked model can overconfidently miscalibrate dispersal-limited
cases, whereas the conservative probability gate can overconfidently fail some
stepping-stone cases. This screen therefore evaluates a fixed convex ensemble without
adding a new response fit:

    D_alpha = (1 - alpha) * D_probability + alpha * D_stack

The alpha grid is finite and declared in source. Development eligibility requires:

- no mean log-loss harm in the two null regimes;
- mean log-loss improvement in every structural regime;
- no individual development seed with more than +0.05 log-loss harm versus the
  environmental baseline.

The screen also records nearest-source and single-cumulative-path comparators using the
same already-declared leakage-safe implementation, but does not retroactively optimize
alpha against those comparator outcomes. Independent confirmation seeds remain
untouched.
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
    _fit_comparator_predictions,
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
MAXIMUM_DEVELOPMENT_SEED_LOG_LOSS_HARM = 0.05


def _log_loss(labels, scores):
    labels = np.asarray(labels, dtype=float)
    scores = np.clip(np.asarray(scores, dtype=float), 1e-12, 1.0 - 1e-12)
    return float(
        np.mean(-(labels * np.log(scores) + (1.0 - labels) * np.log1p(-scores)))
    )


def _metrics(labels, scores):
    return {
        "auc": _auc(labels, scores),
        "brier": _brier(labels, scores),
        "log_loss": _log_loss(labels, scores),
    }


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
        "comparator_contract_reused": True,
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
            comparator_scores = _fit_comparator_predictions(bundle, probability)

            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_probability_models_cross_fitted"] &= bool(
                probability.structural_gate_cross_fitted
            )
            integrity["all_stack_models_cross_fitted"] &= bool(stack.gate_fold_ids)
            integrity["all_predictions_finite"] &= bool(
                np.isfinite(p).all()
                and np.isfinite(s).all()
                and np.isfinite(h).all()
                and all(
                    np.isfinite(np.asarray(values, dtype=float)).all()
                    for values in comparator_scores.values()
                )
            )

            metrics = {}
            for alpha in ALPHA_GRID:
                ensemble = (1.0 - alpha) * p + alpha * s
                metrics[str(alpha)] = _metrics(labels, ensemble)
            per_regime[regime].append(
                {
                    "seed": seed,
                    "environmental": _metrics(labels, h),
                    "nearest_source": _metrics(
                        labels, comparator_scores["environmental_plus_nearest_source"]
                    ),
                    "single_path": _metrics(
                        labels, comparator_scores["environmental_plus_single_path"]
                    ),
                    "probability_gate": _metrics(labels, p),
                    "stack": _metrics(labels, s),
                    "alpha_metrics": metrics,
                }
            )

    summary = {}
    for regime, rows in per_regime.items():
        baselines = {}
        for baseline in (
            "environmental",
            "nearest_source",
            "single_path",
            "probability_gate",
            "stack",
        ):
            baselines[baseline] = {
                metric: float(np.mean([row[baseline][metric] for row in rows]))
                for metric in ("auc", "brier", "log_loss")
            }
        env = baselines["environmental"]
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
                    "minus_nearest_source_log_loss": values["log_loss"]
                    - baselines["nearest_source"]["log_loss"],
                    "minus_single_path_log_loss": values["log_loss"]
                    - baselines["single_path"]["log_loss"],
                    "minus_probability_gate_log_loss": values["log_loss"]
                    - baselines["probability_gate"]["log_loss"],
                    "minus_stack_log_loss": values["log_loss"]
                    - baselines["stack"]["log_loss"],
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
            "baselines": baselines,
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
        maximum_seed_harm = float(
            max(
                summary[regime]["alpha"][key]["worst_seed_log_loss_harm"]
                for regime in REGIMES
            )
        )
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
                "maximum_seed_log_loss_harm": maximum_seed_harm,
                "safe_null_mean_log_loss": null_max_harm <= 1e-12,
                "all_structural_regimes_improve_mean_log_loss": all(
                    value > 0.0 for value in structural_gains.values()
                ),
                "seed_tail_within_development_cap": maximum_seed_harm
                <= MAXIMUM_DEVELOPMENT_SEED_LOG_LOSS_HARM,
            }
        )

    eligible = [
        item
        for item in candidates
        if item["safe_null_mean_log_loss"]
        and item["all_structural_regimes_improve_mean_log_loss"]
        and item["seed_tail_within_development_cap"]
    ]
    recommended = None
    if eligible:
        # Among candidates that satisfy null, structural, and seed-tail safety, maximize
        # the average structural proper-score gain, then the weakest structural gain,
        # then prefer the smaller stack weight.
        recommended = max(
            eligible,
            key=lambda item: (
                item["mean_structural_log_loss_gain"],
                item["minimum_structural_mean_log_loss_gain"],
                -item["alpha"],
            ),
        )

    return {
        "schema": "eog_structural_ensemble_development_v0_2",
        "status": "development_screen_not_confirmation",
        "alpha_grid": list(ALPHA_GRID),
        "null_regimes": list(NULL_REGIMES),
        "structural_regimes": list(STRUCTURAL_REGIMES),
        "maximum_development_seed_log_loss_harm": MAXIMUM_DEVELOPMENT_SEED_LOG_LOSS_HARM,
        "integrity_checks": integrity,
        "all_integrity_checks_pass": bool(all(integrity.values())),
        "summary": summary,
        "candidates": candidates,
        "recommended_alpha": recommended,
        "per_regime": per_regime,
        "claim_boundary": (
            "fixed convex-ensemble development on already-open seeds only; any chosen "
            "alpha and confirmation gates must be frozen before independent confirmation "
            "seeds are executed"
        ),
    }


def main():
    result = run_structural_ensemble_development()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_integrity_checks_pass"]:
        raise SystemExit("EOG structural ensemble development failed integrity checks")
    if result["recommended_alpha"] is None:
        raise SystemExit("no structural ensemble candidate passed development safety")


if __name__ == "__main__":
    main()
