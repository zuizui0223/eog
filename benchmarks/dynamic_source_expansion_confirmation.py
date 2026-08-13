"""Frozen fresh-seed confirmation for nested source expansion in EOG v2.

This imports the already-audited development implementation. The workflow freezes the
source blobs before executing these new seeds, so later method changes cannot reuse this
confirmation.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

import dynamic_source_expansion_sensitivity as dev

CONFIRMATION_SEEDS = (1709, 1801, 1901, 2003, 2111, 2203, 2309, 2401)
EXPECTED_CONTRACT_FINGERPRINT = "387118b1de858514f0734c989b97d1559d020abcc9965098892dd8bb85fc2ac4"
REFERENCE_MODELS = ("fixed_dynamic", "expanded_nearest", "expanded_pressure")


def _contract() -> dict[str, object]:
    return {
        "status": "frozen-before-source-expansion-confirmation-outcomes",
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "n_rows": 8,
        "n_target_columns": 6,
        "max_steps": 6,
        "source_scale": 1.5,
        "loss_support": 0.55,
        "outer_source_policy": (
            "base sources plus positive outer-training targets only; outer-test labels unavailable"
        ),
        "inner_calibration_policy": (
            "source-derived training features are generated out-of-fold; each inner-heldout "
            "positive target is excluded from its own source set"
        ),
        "models": [
            "environment",
            "fixed_dynamic",
            "expanded_nearest",
            "expanded_pressure",
            "expanded_dynamic",
            "leaky_expanded_dynamic",
        ],
        "primary_metric": "outer-fold held-out log loss",
        "primary_reference_set": list(REFERENCE_MODELS),
        "gates": {
            "outer_label_invariance_max_abs": 0.0,
            "require_self_excluded_positive_rows": True,
            "mean_log_loss_gain_over_best_reference_min": 0.05,
            "favourable_seed_count_over_seedwise_best_reference_min": 6,
        },
        "leaky_model_policy": (
            "audit only; not a scientific reference and not part of the promotion gate"
        ),
        "failure_policy": (
            "retain failed confirmation; do not change seeds, gates, graph, folds or source rules to rescue it"
        ),
    }


def _fingerprint(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate() -> dict[str, object]:
    contract = _contract()
    fingerprint = _fingerprint(contract)
    if fingerprint != EXPECTED_CONTRACT_FINGERPRINT:
        raise RuntimeError("frozen source-expansion contract fingerprint changed")

    node_ids, coordinates, viability, raw, operator, base_sources, candidates, folds = dev._build_graph()
    prepared = {
        "node_ids": node_ids,
        "coordinates": coordinates,
        "viability": viability,
        "raw": raw,
        "operator": operator,
        "base_sources": base_sources,
        "candidates": candidates,
        "folds": folds,
        "distance": dev._pairwise_distance(coordinates),
        "first_passage": dev._finite_first_passage_matrix(operator),
    }
    rows = [dev._evaluate_seed(seed, prepared) for seed in CONFIRMATION_SEEDS]
    model_names = tuple(rows[0]["models"])
    means = {
        name: {
            "mean_log_loss": float(
                np.mean([row["models"][name]["log_loss"] for row in rows])
            ),
            "mean_brier": float(
                np.mean([row["models"][name]["brier"] for row in rows])
            ),
        }
        for name in model_names
    }

    seedwise = []
    favourable = 0
    for row in rows:
        dynamic_loss = float(row["models"]["expanded_dynamic"]["log_loss"])
        best_name = min(
            REFERENCE_MODELS,
            key=lambda name: float(row["models"][name]["log_loss"]),
        )
        best_loss = float(row["models"][best_name]["log_loss"])
        gain = best_loss - dynamic_loss
        favourable += int(gain > 0.0)
        seedwise.append(
            {
                "seed": int(row["seed"]),
                "best_reference": best_name,
                "best_reference_log_loss": best_loss,
                "expanded_dynamic_log_loss": dynamic_loss,
                "gain": gain,
            }
        )

    mean_seedwise_best = float(np.mean([row["best_reference_log_loss"] for row in seedwise]))
    mean_dynamic = float(means["expanded_dynamic"]["mean_log_loss"])
    mean_gain = mean_seedwise_best - mean_dynamic
    max_invariance = float(max(row["outer_label_invariance_max_abs"] for row in rows))
    all_self_excluded = bool(all(row["self_excluded_positive_rows"] > 0 for row in rows))
    gates = contract["gates"]
    checks = {
        "outer_label_invariance": {
            "value": max_invariance,
            "relation": "==",
            "threshold": gates["outer_label_invariance_max_abs"],
            "passed": bool(max_invariance == gates["outer_label_invariance_max_abs"]),
        },
        "inner_positive_self_exclusion": {
            "value": all_self_excluded,
            "relation": "is",
            "threshold": True,
            "passed": all_self_excluded,
        },
        "mean_gain_over_seedwise_best_reference": {
            "value": mean_gain,
            "relation": ">=",
            "threshold": gates["mean_log_loss_gain_over_best_reference_min"],
            "passed": bool(
                mean_gain >= gates["mean_log_loss_gain_over_best_reference_min"]
            ),
        },
        "favourable_seed_count": {
            "value": int(favourable),
            "relation": ">=",
            "threshold": gates["favourable_seed_count_over_seedwise_best_reference_min"],
            "passed": bool(
                favourable
                >= gates["favourable_seed_count_over_seedwise_best_reference_min"]
            ),
        },
    }

    return {
        "status": "frozen-source-expansion-confirmation",
        "contract": contract,
        "contract_fingerprint": fingerprint,
        "operator_fingerprint": operator.fingerprint,
        "mean_models": means,
        "mean_seedwise_best_reference_log_loss": mean_seedwise_best,
        "mean_expanded_dynamic_log_loss": mean_dynamic,
        "mean_gain_over_seedwise_best_reference": mean_gain,
        "favourable_seed_count": int(favourable),
        "seedwise_comparison": seedwise,
        "rows": rows,
        "decision": {
            "passed": bool(all(check["passed"] for check in checks.values())),
            "checks": checks,
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
