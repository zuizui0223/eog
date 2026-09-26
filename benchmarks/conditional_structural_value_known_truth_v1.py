"""Known-truth 2x2 factorial for conditional structural added value."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/conditional_structural_value/known_truth_factorial_contract_v1.json"
OUT = ROOT / "build/conditional_structural_value_known_truth_v1.json"
EPS = 1e-6

def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))

def _fit_score(x, y, train, heldout, hp):
    model = LogisticRegression(
        C=float(hp["C"]),
        solver=str(hp["solver"]),
        max_iter=int(hp["max_iter"]),
    )
    model.fit(x[train], y[train])
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(f"unexpected class order: {list(model.classes_)}")
    p = np.clip(model.predict_proba(x[heldout])[:, 1], EPS, 1.0 - EPS)
    return float(log_loss(y[heldout], p, labels=[0, 1]))

def _replicate(seed, contract):
    d = contract["design"]
    rng = np.random.default_rng(int(seed))
    n_nodes = int(d["node_count"])
    n_contexts = int(d["contexts_per_node"])
    train_nodes_n = int(d["train_node_count"])
    train_context_n = int(d["train_context_count"])

    x_node = rng.uniform(-1.0, 1.0, n_nodes)
    y_node = rng.uniform(-1.0, 1.0, n_nodes)
    phase = 2.0 * np.pi * np.arange(n_contexts, dtype=float) / n_contexts

    node = np.repeat(np.arange(n_nodes), n_contexts)
    context = np.tile(np.arange(n_contexts), n_nodes)
    x = x_node[node]
    y = y_node[node]
    ph = phase[context]
    s = np.sin(ph)
    c = np.cos(ph)

    local = 0.35*x - 0.25*y + 0.45*s - 0.20*c
    latent = np.sin(1.7*x - 1.2*y + 0.65*ph) + 0.5*np.cos(
        0.8*x + 1.5*y - 0.35*ph
    )
    response = rng.binomial(1, _sigmoid(local + 1.50*latent)).astype(int)

    weak = np.column_stack([x, y, s, c])
    saturated = np.column_stack([weak, latent])
    aligned = latent[:, None]

    static = np.empty_like(aligned)
    for i in range(n_nodes):
        rows = node == i
        fit_rows = rows & (context < train_context_n)
        static[rows, 0] = float(np.mean(latent[fit_rows]))

    train = (node < train_nodes_n) & (context < train_context_n)
    heldout = (node >= train_nodes_n) & (context >= train_context_n)
    if len(np.unique(response[train])) != 2 or len(np.unique(response[heldout])) != 2:
        raise RuntimeError("known-truth replicate lost a response class")

    hp = d["learner_hyperparameters"]
    cells = {}
    for ref_name, ref in (("weak", weak), ("saturated", saturated)):
        baseline_loss = _fit_score(ref, response, train, heldout, hp)
        for align_name, feature in (("aligned", aligned), ("static", static)):
            aug = np.column_stack([ref, feature])
            aug_loss = _fit_score(aug, response, train, heldout, hp)
            cells[f"{ref_name}_{align_name}"] = {
                "baseline_log_loss": baseline_loss,
                "augmented_log_loss": aug_loss,
                "delta": aug_loss - baseline_loss,
            }
    return {"seed": int(seed), "cells": cells}

def _summary(values):
    a = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "q025": float(np.quantile(a, 0.025)),
        "q975": float(np.quantile(a, 0.975)),
        "favorable_fraction": float(np.mean(a < 0.0)),
        "positive_fraction": float(np.mean(a > 0.0)),
    }

def run():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    reps = [_replicate(seed, c) for seed in c["design"]["replicate_seeds"]]
    keys = ["weak_aligned", "weak_static", "saturated_aligned", "saturated_static"]
    cell = {k: np.asarray([r["cells"][k]["delta"] for r in reps], dtype=float) for k in keys}
    saturation_penalty = cell["saturated_aligned"] - cell["weak_aligned"]
    static_penalty = cell["weak_static"] - cell["weak_aligned"]

    checks = {
        "weak_reference_aligned_median_delta_below_minus_0_05":
            bool(np.median(cell["weak_aligned"]) < -0.05),
        "weak_reference_aligned_favorable_fraction_at_least_0_90":
            bool(np.mean(cell["weak_aligned"] < 0.0) >= 0.90),
        "weak_reference_static_median_delta_strictly_positive":
            bool(np.median(cell["weak_static"]) > 0.0),
        "saturated_reference_aligned_absolute_median_delta_at_most_0_005":
            bool(abs(np.median(cell["saturated_aligned"])) <= 0.005),
        "reference_saturation_penalty_median_strictly_positive":
            bool(np.median(saturation_penalty) > 0.0),
        "static_alignment_penalty_under_weak_reference_median_strictly_positive":
            bool(np.median(static_penalty) > 0.0),
    }
    result = {
        "schema": "eog.conditional_structural_value.known_truth_factorial_result.v1",
        "uses_biological_response": False,
        "counts_as_fresh_predictive_endpoint": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "cell_delta_summaries": {k: _summary(v) for k, v in cell.items()},
        "reference_saturation_penalty": _summary(saturation_penalty),
        "static_alignment_penalty_under_weak_reference": _summary(static_penalty),
        "checks": checks,
        "predeclared_checks_all_passed": bool(all(checks.values())),
        "interpretation": (
            "Known truth separates two causes of conditional structural added value: "
            "structural augmentation is useful when the reference omits the generating "
            "structural state and the feature is context-aligned; its added value collapses "
            "when the reference already contains that state, and static reuse loses value "
            "when the structural truth changes across contexts."
        ),
        "forbidden_interpretations": c["forbidden_interpretations"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["predeclared_checks_all_passed"]:
        raise AssertionError(f"predeclared checks failed: {checks}")
    return result

if __name__ == "__main__":
    run()
