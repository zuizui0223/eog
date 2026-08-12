"""Finite development screen for adaptive EOG complexity margins.

This script reuses only the already-open noisy development seeds. It does not refit a
new biological result and it does not touch independent confirmation seeds. The model
family predictions are generated once at zero margins, then stricter margins can only
simplify the selected family: stacked -> probability gate -> environmental.

The finite margin grid is declared before this screen is inspected. The screen reports
null-regime safety and structural-regime retention separately so a later confirmation
contract can freeze one pair transparently.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.distribution_adaptive_development import run_adaptive_development


STRUCTURAL_MARGIN_GRID = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)
STACK_MARGIN_GRID = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25)
NULL_REGIMES = ("habitat_only", "long_jump")
STRUCTURAL_REGIMES = (
    "dispersal_limited",
    "graded_barrier",
    "stepping_stone",
    "mixed",
)


def _family_for_margins(loss: dict[str, float], structural_margin: float, stack_margin: float):
    env = float(loss["environmental"])
    probability = float(loss["probability_gate"])
    stacked = float(loss["stacked"])
    probability_eligible = env - probability >= structural_margin - 1e-15
    stack_eligible = (
        env - stacked >= structural_margin - 1e-15
        and probability - stacked >= stack_margin - 1e-15
    )
    if stack_eligible:
        return "stacked"
    if probability_eligible:
        return "probability_gate"
    return "environmental"


def _metric_value(row: dict[str, object], metric: str, family: str) -> float:
    values = row[metric]
    if family == "environmental":
        return float(values["environmental_support"])
    if family == "probability_gate":
        return float(values["eog_distribution_support"])
    if family == "stacked":
        if row["selected_family"] != "stacked":
            raise ValueError(
                "positive margins cannot promote stacked when the zero-margin model did not select it"
            )
        return float(values["adaptive_eog"])
    raise ValueError(f"unknown family: {family}")


def _evaluate_pair(development, structural_margin: float, stack_margin: float):
    per_regime = {}
    for regime, rows in development["per_regime"].items():
        family_counts = {"environmental": 0, "probability_gate": 0, "stacked": 0}
        metric_rows = {"auc": [], "brier": [], "log_loss": []}
        env_rows = {"auc": [], "brier": [], "log_loss": []}
        for row in rows:
            family = _family_for_margins(
                row["candidate_selection_log_loss"], structural_margin, stack_margin
            )
            family_counts[family] += 1
            for metric in metric_rows:
                metric_rows[metric].append(_metric_value(row, metric, family))
                env_rows[metric].append(
                    float(row[metric]["environmental_support"])
                )
        per_regime[regime] = {
            "family_counts": family_counts,
            "mean_auc": float(np.mean(metric_rows["auc"])),
            "mean_brier": float(np.mean(metric_rows["brier"])),
            "mean_log_loss": float(np.mean(metric_rows["log_loss"])),
            "minus_environmental_mean_auc": float(
                np.mean(np.asarray(metric_rows["auc"]) - np.asarray(env_rows["auc"]))
            ),
            "minus_environmental_mean_brier": float(
                np.mean(np.asarray(metric_rows["brier"]) - np.asarray(env_rows["brier"]))
            ),
            "minus_environmental_mean_log_loss": float(
                np.mean(
                    np.asarray(metric_rows["log_loss"])
                    - np.asarray(env_rows["log_loss"])
                )
            ),
        }

    null_logloss_harm = max(
        per_regime[regime]["minus_environmental_mean_log_loss"]
        for regime in NULL_REGIMES
    )
    structural_logloss_gains = {
        regime: -per_regime[regime]["minus_environmental_mean_log_loss"]
        for regime in STRUCTURAL_REGIMES
    }
    structural_auc_gains = {
        regime: per_regime[regime]["minus_environmental_mean_auc"]
        for regime in STRUCTURAL_REGIMES
    }
    null_environmental_fraction = float(
        np.mean(
            [
                per_regime[regime]["family_counts"]["environmental"] / 8.0
                for regime in NULL_REGIMES
            ]
        )
    )
    structural_selection_fraction = float(
        np.mean(
            [
                1.0
                - per_regime[regime]["family_counts"]["environmental"] / 8.0
                for regime in STRUCTURAL_REGIMES
            ]
        )
    )
    all_structural_logloss_positive = all(
        value > 0.0 for value in structural_logloss_gains.values()
    )
    safe_null_mean_logloss = null_logloss_harm <= 1e-12
    return {
        "minimum_structural_log_loss_gain": structural_margin,
        "minimum_stack_log_loss_gain": stack_margin,
        "safe_null_mean_logloss": safe_null_mean_logloss,
        "all_structural_regimes_improve_mean_logloss": all_structural_logloss_positive,
        "null_max_mean_logloss_harm": float(null_logloss_harm),
        "null_environmental_selection_fraction": null_environmental_fraction,
        "structural_selection_fraction": structural_selection_fraction,
        "minimum_structural_mean_logloss_gain": float(
            min(structural_logloss_gains.values())
        ),
        "minimum_structural_mean_auc_gain": float(min(structural_auc_gains.values())),
        "per_regime": per_regime,
    }


def run_margin_screen():
    development = run_adaptive_development()
    if not development["all_integrity_checks_pass"]:
        raise ValueError("adaptive development evidence failed integrity checks")
    rows = [
        _evaluate_pair(development, structural_margin, stack_margin)
        for structural_margin in STRUCTURAL_MARGIN_GRID
        for stack_margin in STACK_MARGIN_GRID
    ]
    eligible = [
        row
        for row in rows
        if row["safe_null_mean_logloss"]
        and row["all_structural_regimes_improve_mean_logloss"]
    ]
    # This is a development recommendation only. Prefer the least restrictive pair
    # satisfying both proper-score safety conditions; ties prefer the smaller stack
    # margin. Independent seeds remain unopened.
    recommended = None
    if eligible:
        recommended = min(
            eligible,
            key=lambda row: (
                row["minimum_structural_log_loss_gain"],
                row["minimum_stack_log_loss_gain"],
            ),
        )
    return {
        "schema": "adaptive_eog_margin_development_v0_1",
        "status": "development_screen_not_confirmation",
        "structural_margin_grid": list(STRUCTURAL_MARGIN_GRID),
        "stack_margin_grid": list(STACK_MARGIN_GRID),
        "null_regimes": list(NULL_REGIMES),
        "structural_regimes": list(STRUCTURAL_REGIMES),
        "n_pairs": len(rows),
        "n_eligible_pairs": len(eligible),
        "recommended_pair": None
        if recommended is None
        else {
            key: recommended[key]
            for key in (
                "minimum_structural_log_loss_gain",
                "minimum_stack_log_loss_gain",
                "null_max_mean_logloss_harm",
                "null_environmental_selection_fraction",
                "structural_selection_fraction",
                "minimum_structural_mean_logloss_gain",
                "minimum_structural_mean_auc_gain",
            )
        },
        "pairs": rows,
        "claim_boundary": (
            "development-only complexity-margin screen on previously opened seeds; "
            "the chosen pair must be frozen before any independent confirmation seeds run"
        ),
    }


def main():
    result = run_margin_screen()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["recommended_pair"] is None:
        raise SystemExit("no adaptive EOG margin pair passed the development safety screen")


if __name__ == "__main__":
    main()
