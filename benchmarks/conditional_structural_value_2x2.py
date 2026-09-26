"""Known-truth 2x2 test of conditional structural predictive value.

Contract is frozen in:
validation/conditional_structural_value/known_truth_2x2_contract_v1.json

This benchmark uses no biological response. It crosses:
1) weak vs structurally saturated reference;
2) refreshed vs static-reused structural representation.

All outcome realizations, coordinates, contexts, learner settings and splits are paired
within replicate.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/conditional_structural_value/known_truth_2x2_contract_v1.json"
DEFAULT_OUTPUT = ROOT / "build/conditional_structural_value/known_truth_2x2_result.json"
EPS = 1e-6


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


def _rf(contract: dict) -> RandomForestClassifier:
    hp = contract["design"]["learner_hyperparameters"]
    return RandomForestClassifier(
        n_estimators=int(hp["n_estimators"]),
        max_features=str(hp["max_features"]),
        min_samples_leaf=int(hp["min_samples_leaf"]),
        class_weight=None,
        random_state=int(hp["random_state"]),
        n_jobs=int(hp["n_jobs"]),
    )


def _p1(model: RandomForestClassifier, x: np.ndarray) -> np.ndarray:
    classes = list(model.classes_)
    if classes != [0, 1]:
        raise RuntimeError(f"unexpected class order: {classes}")
    return np.clip(model.predict_proba(x)[:, 1], EPS, 1.0 - EPS)


def _replicate(seed: int, contract: dict) -> dict:
    d = contract["design"]
    rng = np.random.default_rng(seed)

    n_nodes = int(d["node_count"])
    n_contexts = int(d["contexts_per_node"])
    train_nodes = int(d["train_node_count"])
    train_contexts = int(d["train_context_count"])

    node_x = rng.uniform(-1.0, 1.0, n_nodes)
    node_y = rng.uniform(-1.0, 1.0, n_nodes)
    phase_by_context = 2.0 * np.pi * np.arange(n_contexts, dtype=float) / n_contexts

    node_index = np.repeat(np.arange(n_nodes), n_contexts)
    context_index = np.tile(np.arange(n_contexts), n_nodes)

    x = node_x[node_index]
    y = node_y[node_index]
    phase = phase_by_context[context_index]
    context_sin = np.sin(phase)
    context_cos = np.cos(phase)

    local_lp = 0.30 * x - 0.20 * y + 0.35 * context_sin - 0.15 * context_cos
    latent = np.sin(1.5 * x - 1.1 * y + 0.70 * phase) + 0.55 * np.cos(
        0.9 * x + 1.4 * y - 0.40 * phase
    )
    probability = _sigmoid(local_lp + 1.35 * latent)
    response = rng.binomial(1, probability).astype(int)

    weak_baseline = np.column_stack([x, y, context_sin, context_cos])
    strong_baseline = np.column_stack([weak_baseline, latent])

    refreshed = np.column_stack([
        latent,
        latent ** 2,
        np.sin(latent),
        np.cos(latent),
        x * latent,
        y * latent,
        context_sin * latent,
        context_cos * latent,
    ])
    if refreshed.shape[1] != int(d["layer_b_feature_count"]):
        raise RuntimeError("Layer-B feature-count drift")

    static_reused = np.empty_like(refreshed)
    for node in range(n_nodes):
        node_rows = node_index == node
        fit_rows = node_rows & (context_index < train_contexts)
        static_reused[node_rows] = np.mean(refreshed[fit_rows], axis=0)

    train_mask = (node_index < train_nodes) & (context_index < train_contexts)
    heldout_mask = (node_index >= train_nodes) & (context_index >= train_contexts)
    y_train = response[train_mask]
    y_test = response[heldout_mask]
    if len(np.unique(y_train)) != 2 or len(np.unique(y_test)) != 2:
        raise RuntimeError(f"seed {seed} lost a response class")

    cells = {}
    for ref_name, baseline in (("weak", weak_baseline), ("strong", strong_baseline)):
        baseline_model = _rf(contract)
        baseline_model.fit(baseline[train_mask], y_train)
        baseline_prob = _p1(baseline_model, baseline[heldout_mask])
        baseline_loss = float(log_loss(y_test, baseline_prob, labels=[0, 1]))
        baseline_brier = float(np.mean((baseline_prob - y_test) ** 2))

        for align_name, layer_b in (("refreshed", refreshed), ("static", static_reused)):
            aug_model = _rf(contract)
            aug_model.fit(
                np.column_stack([baseline[train_mask], layer_b[train_mask]]),
                y_train,
            )
            aug_prob = _p1(
                aug_model,
                np.column_stack([baseline[heldout_mask], layer_b[heldout_mask]]),
            )
            aug_loss = float(log_loss(y_test, aug_prob, labels=[0, 1]))
            aug_brier = float(np.mean((aug_prob - y_test) ** 2))
            key = f"{ref_name}_{align_name}"
            cells[key] = {
                "baseline_log_loss": baseline_loss,
                "augmented_log_loss": aug_loss,
                "added_value_log_loss": aug_loss - baseline_loss,
                "baseline_brier": baseline_brier,
                "augmented_brier": aug_brier,
                "added_value_brier": aug_brier - baseline_brier,
            }

    return {"seed": seed, "cells": cells}


def _summary(values: np.ndarray) -> dict:
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "q025": float(np.quantile(values, 0.025)),
        "q975": float(np.quantile(values, 0.975)),
        "favorable_fraction": float(np.mean(values < 0.0)),
        "positive_fraction": float(np.mean(values > 0.0)),
    }


def _replicate_task(payload: tuple[int, dict]) -> dict:
    seed, contract = payload
    return _replicate(int(seed), contract)


def run_benchmark() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    payloads = [(int(seed), contract) for seed in contract["design"]["replicate_seeds"]]
    workers = min(4, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        reps = list(executor.map(_replicate_task, payloads))

    keys = ["weak_refreshed", "weak_static", "strong_refreshed", "strong_static"]
    added = {
        key: np.asarray([float(r["cells"][key]["added_value_log_loss"]) for r in reps])
        for key in keys
    }

    saturation = added["strong_refreshed"] - added["weak_refreshed"]
    alignment = added["weak_static"] - added["weak_refreshed"]
    joint = added["strong_static"] - added["weak_refreshed"]

    medians = {key: float(np.median(values)) for key, values in added.items()}
    best_key = min(medians, key=medians.get)

    checks = {
        "weak_refreshed_median_added_value_strictly_negative":
            bool(np.median(added["weak_refreshed"]) < 0.0),
        "weak_refreshed_favorable_fraction_at_least_0_90":
            bool(np.mean(added["weak_refreshed"] < 0.0) >= 0.90),
        "saturation_moderation_median_strictly_positive":
            bool(np.median(saturation) > 0.0),
        "saturation_moderation_positive_fraction_at_least_0_80":
            bool(np.mean(saturation > 0.0) >= 0.80),
        "alignment_moderation_median_strictly_positive":
            bool(np.median(alignment) > 0.0),
        "alignment_moderation_positive_fraction_at_least_0_80":
            bool(np.mean(alignment > 0.0) >= 0.80),
        "weak_refreshed_is_best_median_cell":
            bool(best_key == "weak_refreshed"),
    }

    result = {
        "schema": "eog.conditional_structural_value.known_truth_2x2_result.v1",
        "uses_biological_response": False,
        "counts_as_fresh_predictive_endpoint": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "cell_added_value_log_loss": {key: _summary(values) for key, values in added.items()},
        "moderation_estimands": {
            "reference_saturation_strong_minus_weak_under_refreshed": _summary(saturation),
            "response_alignment_static_minus_refreshed_under_weak_reference": _summary(alignment),
            "joint_strong_static_minus_weak_refreshed": _summary(joint),
        },
        "median_cell_ranking_best_to_worst": [
            key for key, _ in sorted(medians.items(), key=lambda kv: kv[1])
        ],
        "checks": checks,
        "all_predeclared_checks_passed": bool(all(checks.values())),
        "scientific_status": (
            contract["interpretation_if_all_checks_pass"]
            if all(checks.values())
            else contract["interpretation_if_any_check_fail"]
        ),
        "interpretation": (
            "Known-truth paired intervention result only. It tests whether reference "
            "saturation and response alignment can causally moderate structural added "
            "value under the frozen generator; it does not assign causes to historical "
            "ecological endpoint signs."
        ),
        "forbidden_interpretations": contract["forbidden_interpretations"],
    }
    return result


def main(output_path: Path = DEFAULT_OUTPUT) -> dict:
    result = run_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
