"""Known-truth causal factorial for Layer-B representation failure modes.

This benchmark uses no biological response.  Its contract was committed before this
runner.  It switches three synthetic representation defects independently while holding
the outcome realization, baseline, split and learner fixed within each replicate.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/layer_b_mechanism_v2/causal_factorial_contract_v1.json"
DEFAULT_OUTPUT = ROOT / "build/layer_b_v2_causal_factorial_result.json"
EPS = 1e-6


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


def _rf(contract: dict[str, object]) -> RandomForestClassifier:
    hp = contract["design"]["learner_hyperparameters"]
    return RandomForestClassifier(
        n_estimators=int(hp["n_estimators"]),
        max_features=str(hp["max_features"]),
        min_samples_leaf=int(hp["min_samples_leaf"]),
        class_weight=None,
        random_state=int(hp["random_state"]),
        n_jobs=int(hp["n_jobs"]),
    )


def _positive_probability(model: RandomForestClassifier, x: np.ndarray) -> np.ndarray:
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(f"unexpected RF class order: {list(model.classes_)}")
    return np.clip(model.predict_proba(x)[:, 1], EPS, 1.0 - EPS)


def _build_replication(seed: int, contract: dict[str, object]) -> dict[str, object]:
    d = contract["design"]
    rng = np.random.default_rng(seed)
    n_nodes = int(d["node_count"])
    n_contexts = int(d["contexts_per_node"])
    train_nodes_n = int(d["train_node_count"])
    train_context_n = int(d["train_context_count"])

    node_ids = np.asarray([f"N{i:03d}" for i in range(n_nodes)], dtype=object)
    x_node = rng.uniform(-1.0, 1.0, n_nodes)
    y_node = rng.uniform(-1.0, 1.0, n_nodes)
    context = np.arange(n_contexts, dtype=float)
    phase = 2.0 * np.pi * context / n_contexts

    node_index = np.repeat(np.arange(n_nodes), n_contexts)
    context_index = np.tile(np.arange(n_contexts), n_nodes)
    x = x_node[node_index]
    y = y_node[node_index]
    ph = phase[context_index]
    s = np.sin(ph)
    c = np.cos(ph)

    baseline_lp = 0.35 * x - 0.25 * y + 0.45 * s - 0.20 * c
    latent = np.sin(1.7 * x - 1.2 * y + 0.65 * ph) + 0.5 * np.cos(
        0.8 * x + 1.5 * y - 0.35 * ph
    )
    p = _sigmoid(baseline_lp + 1.20 * latent)
    response = rng.binomial(1, p).astype(int)

    baseline = np.column_stack([x, y, s, c])
    clean = np.column_stack(
        [
            latent,
            latent**2,
            np.sin(latent),
            np.cos(latent),
            x * latent,
            y * latent,
            s * latent,
            c * latent,
            x * x - y * y,
            latent + 0.20 * x - 0.10 * y,
        ]
    )
    if clean.shape[1] != int(d["layer_b_feature_count"]):
        raise RuntimeError("Layer-B feature-count drift")

    train_mask = (node_index < train_nodes_n) & (context_index < train_context_n)
    heldout_mask = (node_index >= train_nodes_n) & (context_index >= train_context_n)
    if not np.any(train_mask) or not np.any(heldout_mask):
        raise RuntimeError("empty frozen train/heldout partition")
    y_train = response[train_mask]
    y_test = response[heldout_mask]
    if len(np.unique(y_train)) != 2 or len(np.unique(y_test)) != 2:
        raise RuntimeError("known-truth realization lost a response class")

    baseline_model = _rf(contract)
    baseline_model.fit(baseline[train_mask], y_train)
    baseline_prob = _positive_probability(baseline_model, baseline[heldout_mask])
    baseline_loss = float(log_loss(y_test, baseline_prob, labels=[0, 1]))
    baseline_brier = float(np.mean((baseline_prob - y_test) ** 2))

    # Static reuse is generated without outcomes: for each node, average the clean
    # state over the declared fitting contexts, then reuse that vector in all contexts.
    static = np.empty_like(clean)
    for node in range(n_nodes):
        rows = node_index == node
        fit_rows = rows & (context_index < train_context_n)
        mean_vector = np.mean(clean[fit_rows], axis=0)
        static[rows] = mean_vector

    cell_results: dict[str, dict[str, float]] = {}
    for g, sflag, aflag in itertools.product((0, 1), repeat=3):
        rep = static.copy() if sflag else clean.copy()

        # Label-dependent single-source analogue.  In the defect condition the
        # prediction-facing vector changes sign solely because of arbitrary node label.
        # N000-N039 are flipped; heldout N060-N079 are not.  The source-symmetric clean
        # condition has no such label dependence.
        if aflag:
            flip = np.asarray([str(node_ids[i]) < "N040" for i in node_index])
            rep[flip] *= -1.0

        train_b = rep[train_mask].copy()
        test_b = rep[heldout_mask].copy()

        # Train/serve generator shift acts only at serving time and is fixed by contract.
        if g:
            test_b[:, 0] *= -1.0
            test_b[:, 1] += 1.5
            test_b[:, 2] *= -1.0
            test_b[:, 3] += 1.0
            test_b[:, 5] *= -1.0
            test_b[:, 6] += 0.75
            test_b[:, 8] *= -1.0
            test_b[:, 9] += 0.5

        model = _rf(contract)
        model.fit(np.column_stack([baseline[train_mask], train_b]), y_train)
        prob = _positive_probability(
            model, np.column_stack([baseline[heldout_mask], test_b])
        )
        key = f"{g}{sflag}{aflag}"
        cell_results[key] = {
            "log_loss": float(log_loss(y_test, prob, labels=[0, 1])),
            "brier": float(np.mean((prob - y_test) ** 2)),
        }

    return {
        "seed": seed,
        "baseline_log_loss": baseline_loss,
        "baseline_brier": baseline_brier,
        "cells": cell_results,
    }


def _main_effect(rep: dict[str, object], factor_index: int, metric: str) -> float:
    cells = rep["cells"]
    diffs: list[float] = []
    other = [i for i in range(3) if i != factor_index]
    for values in itertools.product((0, 1), repeat=2):
        low = [0, 0, 0]
        high = [0, 0, 0]
        high[factor_index] = 1
        for index, value in zip(other, values, strict=True):
            low[index] = value
            high[index] = value
        low_key = "".join(str(v) for v in low)
        high_key = "".join(str(v) for v in high)
        diffs.append(float(cells[high_key][metric]) - float(cells[low_key][metric]))
    return float(np.mean(diffs))


def run_benchmark() -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    reps = [_build_replication(int(seed), contract) for seed in contract["design"]["replicate_seeds"]]

    generator = np.asarray([_main_effect(r, 0, "log_loss") for r in reps])
    static = np.asarray([_main_effect(r, 1, "log_loss") for r in reps])
    source = np.asarray([_main_effect(r, 2, "log_loss") for r in reps])
    full = np.asarray(
        [float(r["cells"]["111"]["log_loss"]) - float(r["cells"]["000"]["log_loss"]) for r in reps]
    )
    clean_minus_baseline = np.asarray(
        [float(r["cells"]["000"]["log_loss"]) - float(r["baseline_log_loss"]) for r in reps]
    )

    effects = {
        "generator_shift": generator,
        "static_reuse": static,
        "label_dependent_single_source": source,
        "full_defect": full,
    }
    summaries = {
        name: {
            "mean_log_loss_penalty": float(np.mean(values)),
            "median_log_loss_penalty": float(np.median(values)),
            "q025": float(np.quantile(values, 0.025)),
            "q975": float(np.quantile(values, 0.975)),
            "positive_replicate_fraction": float(np.mean(values > 0.0)),
        }
        for name, values in effects.items()
    }
    checks = {
        "generator_shift_median_positive": bool(np.median(generator) > 0.0),
        "static_reuse_median_positive": bool(np.median(static) > 0.0),
        "single_source_median_positive": bool(np.median(source) > 0.0),
        "full_defect_median_positive": bool(np.median(full) > 0.0),
        "clean_augmented_median_better_than_baseline": bool(
            np.median(clean_minus_baseline) < 0.0
        ),
    }
    if not all(checks.values()):
        raise AssertionError(f"predeclared causal-factorial check failed: {checks}")

    return {
        "schema": "eog.layer_b_mechanism_v2.causal_factorial_result.v1",
        "counts_as_fresh_predictive_endpoint": False,
        "uses_biological_response": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "primary_estimand": "paired within-replicate log-loss penalty under one-factor interventions",
        "effect_summaries": summaries,
        "clean_augmented_minus_baseline": {
            "mean": float(np.mean(clean_minus_baseline)),
            "median": float(np.median(clean_minus_baseline)),
            "favorable_fraction": float(np.mean(clean_minus_baseline < 0.0)),
        },
        "checks": checks,
        "cell_macro_log_loss": {
            key: float(np.mean([float(r["cells"][key]["log_loss"]) for r in reps]))
            for key in sorted(reps[0]["cells"])
        },
        "interpretation": "In this frozen synthetic known-truth system, each representation defect has a causal intervention effect on heldout transfer because all other data, outcomes, learner, baseline and split are paired and fixed. Effect magnitudes are benchmark-specific and cannot be assigned to Tampa.",
        "forbidden_interpretations": contract["forbidden_interpretations"],
    }


def main(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    result = run_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
