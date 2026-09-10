"""Known-truth validation of calibration-only selective Layer-B promotion.

The contract was committed before this runner. No biological response is used. The
selector sees only inner-calibration outcomes; outer heldout outcomes are untouched until
a baseline-only or baseline-plus-Layer-B choice has been frozen within each replicate.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/layer_b_mechanism_v2/selective_promotion_known_truth_contract_v1.json"
DEFAULT_OUTPUT = ROOT / "build/selective_layer_b_promotion_known_truth_result.json"
EPS = 1e-6


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


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


def _macro_log_loss(y: np.ndarray, p: np.ndarray, contexts: np.ndarray, context_values: range) -> float:
    values: list[float] = []
    for context in context_values:
        mask = contexts == context
        values.append(float(log_loss(y[mask], p[mask], labels=[0, 1])))
    return float(np.mean(values))


def _fit_predict(
    contract: dict[str, object],
    x: np.ndarray,
    y: np.ndarray,
    train_mask: np.ndarray,
    score_mask: np.ndarray,
) -> np.ndarray:
    model = _rf(contract)
    model.fit(x[train_mask], y[train_mask])
    return np.clip(model.predict_proba(x[score_mask])[:, 1], EPS, 1.0 - EPS)


def _coefficient(regime: str, context: int) -> float:
    if regime == "helpful_stable":
        return 1.20
    if regime == "neutral":
        return 0.0
    if regime == "harmful_shift_visible_in_calibration":
        return 1.20 if context <= 14 else -1.20
    raise ValueError(f"unknown regime: {regime}")


def _one_replicate(regime: str, seed: int, contract: dict[str, object]) -> dict[str, object]:
    d = contract["design"]
    rng = np.random.default_rng(seed)
    n_nodes = int(d["node_count"])
    n_contexts = int(d["context_count"])
    x_node = rng.uniform(-1.0, 1.0, n_nodes)
    y_node = rng.uniform(-1.0, 1.0, n_nodes)

    baseline_rows: list[np.ndarray] = []
    layer_rows: list[np.ndarray] = []
    responses: list[np.ndarray] = []
    context_rows: list[np.ndarray] = []

    for context in range(n_contexts):
        phase = 2.0 * math.pi * context / n_contexts
        s = math.sin(phase)
        c = math.cos(phase)
        z = np.sin(1.6 * x_node - 1.1 * y_node + 0.45 * phase) + 0.45 * np.cos(
            0.7 * x_node + 1.3 * y_node - 0.25 * phase
        )
        baseline = np.column_stack(
            [
                x_node,
                y_node,
                np.full(n_nodes, s),
                np.full(n_nodes, c),
            ]
        )
        layer = np.column_stack([z, z**2, np.sin(z), np.cos(z)])
        baseline_lp = 0.35 * x_node - 0.30 * y_node + 0.40 * s - 0.20 * c
        p = _sigmoid(baseline_lp + _coefficient(regime, context) * z)
        y = rng.binomial(1, p).astype(int)
        baseline_rows.append(baseline)
        layer_rows.append(layer)
        responses.append(y)
        context_rows.append(np.full(n_nodes, context, dtype=int))

    x_base = np.vstack(baseline_rows)
    x_aug = np.hstack([x_base, np.vstack(layer_rows)])
    y_all = np.concatenate(responses)
    contexts = np.concatenate(context_rows)

    inner_train = contexts <= 14
    inner_val = (contexts >= 15) & (contexts <= 22)
    full_calibration = contexts <= 22
    outer = contexts >= 23
    if len(np.unique(y_all[inner_train])) != 2 or len(np.unique(y_all[inner_val])) != 2 or len(np.unique(y_all[outer])) != 2:
        raise RuntimeError("known-truth split lost a response class")

    p_inner_base = _fit_predict(contract, x_base, y_all, inner_train, inner_val)
    p_inner_aug = _fit_predict(contract, x_aug, y_all, inner_train, inner_val)
    inner_contexts = contexts[inner_val]
    inner_base_loss = _macro_log_loss(y_all[inner_val], p_inner_base, inner_contexts, range(15, 23))
    inner_aug_loss = _macro_log_loss(y_all[inner_val], p_inner_aug, inner_contexts, range(15, 23))
    promoted = inner_aug_loss < inner_base_loss

    p_outer_base = _fit_predict(contract, x_base, y_all, full_calibration, outer)
    p_outer_aug = _fit_predict(contract, x_aug, y_all, full_calibration, outer)
    outer_contexts = contexts[outer]
    outer_base_loss = _macro_log_loss(y_all[outer], p_outer_base, outer_contexts, range(23, 30))
    outer_aug_loss = _macro_log_loss(y_all[outer], p_outer_aug, outer_contexts, range(23, 30))
    selective_loss = outer_aug_loss if promoted else outer_base_loss
    oracle_loss = min(outer_base_loss, outer_aug_loss)

    return {
        "regime": regime,
        "seed": seed,
        "promoted": promoted,
        "inner_validation": {
            "baseline_macro_log_loss": inner_base_loss,
            "augmented_macro_log_loss": inner_aug_loss,
            "augmented_minus_baseline": inner_aug_loss - inner_base_loss,
        },
        "outer": {
            "baseline_macro_log_loss": outer_base_loss,
            "always_augmented_macro_log_loss": outer_aug_loss,
            "selective_macro_log_loss": selective_loss,
            "oracle_macro_log_loss": oracle_loss,
            "selective_minus_baseline": selective_loss - outer_base_loss,
            "selective_minus_always_augmented": selective_loss - outer_aug_loss,
            "selective_oracle_regret": selective_loss - oracle_loss,
        },
    }


def _summary(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "q025": float(np.quantile(values, 0.025)),
        "q975": float(np.quantile(values, 0.975)),
    }


def run_benchmark() -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    reps: list[dict[str, object]] = []
    for regime, spec in contract["regimes"].items():
        reps.extend(_one_replicate(regime, int(seed), contract) for seed in spec["seeds"])

    regime_summaries: dict[str, object] = {}
    for regime in contract["regimes"]:
        subset = [rep for rep in reps if rep["regime"] == regime]
        promotion_rate = float(np.mean([bool(rep["promoted"]) for rep in subset]))
        regret = np.asarray([float(rep["outer"]["selective_oracle_regret"]) for rep in subset])
        selective_vs_base = np.asarray([float(rep["outer"]["selective_minus_baseline"]) for rep in subset])
        selective_vs_aug = np.asarray([float(rep["outer"]["selective_minus_always_augmented"]) for rep in subset])
        regime_summaries[regime] = {
            "replicate_count": len(subset),
            "promotion_rate": promotion_rate,
            "selective_oracle_regret": _summary(regret),
            "selective_minus_baseline": _summary(selective_vs_base),
            "selective_minus_always_augmented": _summary(selective_vs_aug),
        }

    all_regret = np.asarray([float(rep["outer"]["selective_oracle_regret"]) for rep in reps])
    selective_losses = np.asarray([float(rep["outer"]["selective_macro_log_loss"]) for rep in reps])
    baseline_losses = np.asarray([float(rep["outer"]["baseline_macro_log_loss"]) for rep in reps])
    augmented_losses = np.asarray([float(rep["outer"]["always_augmented_macro_log_loss"]) for rep in reps])

    helpful_rate = float(regime_summaries["helpful_stable"]["promotion_rate"])
    harmful_rate = float(regime_summaries["harmful_shift_visible_in_calibration"]["promotion_rate"])
    checks = {
        "helpful_promotion_rate_at_least_0_75": helpful_rate >= 0.75,
        "harmful_promotion_rate_at_most_0_25": harmful_rate <= 0.25,
        "overall_median_oracle_regret_at_most_0_005": float(np.median(all_regret)) <= 0.005,
        "overall_mean_selective_loss_not_worse_than_always_augmented": float(np.mean(selective_losses)) <= float(np.mean(augmented_losses)),
        "overall_mean_selective_loss_not_worse_than_baseline": float(np.mean(selective_losses)) <= float(np.mean(baseline_losses)),
    }
    all_pass = all(checks.values())
    status = (
        "known_truth_support_for_calibration_only_selective_promotion"
        if all_pass
        else "known_truth_refutation_or_non_support_for_selective_promotion"
    )
    return {
        "schema": "eog.layer_b_mechanism_v2.selective_promotion_known_truth_result.v1",
        "uses_biological_response": False,
        "counts_as_fresh_predictive_endpoint": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "scientific_status": status,
        "predeclared_checks_all_passed": all_pass,
        "checks": checks,
        "regime_summaries": regime_summaries,
        "overall": {
            "selective_oracle_regret": _summary(all_regret),
            "mean_selective_macro_log_loss": float(np.mean(selective_losses)),
            "mean_baseline_macro_log_loss": float(np.mean(baseline_losses)),
            "mean_always_augmented_macro_log_loss": float(np.mean(augmented_losses)),
            "selective_minus_baseline_mean": float(np.mean(selective_losses - baseline_losses)),
            "selective_minus_always_augmented_mean": float(np.mean(selective_losses - augmented_losses)),
        },
        "interpretation": "The selector uses only inner-calibration outcomes to decide whether Layer B is promoted. Outer heldout outcomes are used only for the final evaluation of the frozen choice.",
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
