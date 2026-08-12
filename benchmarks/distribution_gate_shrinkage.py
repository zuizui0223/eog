"""Nested synthetic fallback benchmark for the experimental EOG distribution model.

This generator makes structural accessibility deliberately uninformative: every node
inside a module is connected through zero-cost structural edges, so accessibility is
identically one for positives and negatives. Occurrence is instead determined by a
single environmental predictor. Environmental support and accessibility used to fit
the structural gate are both generated in two inner folds.

The gate should therefore shrink to zero and EOG should reduce exactly to the fitted
environmental support model. This is a method-safety contract, not evidence about any
empirical species.
"""
from __future__ import annotations

import json

import numpy as np

from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    BridgeWeights,
    EOGDistributionConfig,
    fit_eog_distribution,
)


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    comparisons = positives[:, None] - negatives[None, :]
    return float(np.mean((comparisons > 0).astype(float) + 0.5 * (comparisons == 0)))


def build_environment_only_landscape(n_modules: int = 6):
    if n_modules < 2:
        raise ValueError("n_modules must be at least two")
    nodes: list[BridgeNode] = []
    observed_ids: list[str] = []
    observed_response: list[int] = []
    gate_fold_ids: list[str] = []
    target_ids: list[str] = []
    target_response: list[int] = []

    for module in range(n_modules):
        latitude = -5.0 + module * 2.0
        prefix = f"m{module:02d}"
        rows = [
            (f"{prefix}_source_a", 0.00, 0.90, 1, True, "inner_a"),
            (f"{prefix}_source_b", 0.05, 0.90, 1, True, "inner_b"),
            (f"{prefix}_negative_a", 0.10, 0.10, 0, True, "inner_a"),
            (f"{prefix}_negative_b", 0.15, 0.10, 0, True, "inner_b"),
            (f"{prefix}_heldout_positive", 0.20, 0.90, 1, False, "heldout"),
            (f"{prefix}_heldout_negative", 0.25, 0.10, 0, False, "heldout"),
        ]
        for node_id, longitude, environment, label, training, fold in rows:
            nodes.append(BridgeNode(node_id, latitude, longitude, (environment,)))
            if training:
                observed_ids.append(node_id)
                observed_response.append(label)
                gate_fold_ids.append(fold)
            else:
                target_ids.append(node_id)
                target_response.append(label)

    return (
        nodes,
        observed_ids,
        observed_response,
        gate_fold_ids,
        target_ids,
        target_response,
    )


def run_gate_shrinkage_benchmark(n_modules: int = 6) -> dict[str, object]:
    (
        nodes,
        observed_ids,
        observed_response,
        gate_fold_ids,
        target_ids,
        target_response,
    ) = build_environment_only_landscape(n_modules)
    model = fit_eog_distribution(
        nodes,
        observed_ids,
        observed_response,
        EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=20.0),
            # Barrier-only cost with no declared barriers makes every admitted edge
            # structurally cost-free. Accessibility is therefore one everywhere in
            # each connected module and carries no response information.
            bridge_weights=BridgeWeights(geographic=0.0, environmental=0.0, barrier=1.0),
            structural_gate_penalty=0.01,
            min_class_count=n_modules,
        ),
        gate_fold_ids=gate_fold_ids,
        reference_provenance="nested environment-only structural gate shrinkage benchmark",
    )
    prediction = model.predict(target_ids)
    labels = np.asarray(target_response, dtype=int)
    environmental_auc = _auc(labels, prediction.environmental_support)
    eog_auc = _auc(labels, prediction.distribution_support)

    checks = {
        "target_labels_are_held_out": set(target_ids).isdisjoint(observed_ids),
        "accessibility_is_uninformative": bool(
            np.allclose(prediction.structural_accessibility, 1.0, rtol=0.0, atol=1e-12)
        ),
        "structural_gate_is_training_fitted": model.structural_gate_fitted,
        "structural_gate_is_inner_cross_fitted": model.structural_gate_cross_fitted,
        "structural_gate_shrinks_to_zero": model.structural_gate_weight == 0.0,
        "distribution_reduces_to_environmental_support": bool(
            np.array_equal(prediction.distribution_support, prediction.environmental_support)
        ),
        "environmental_signal_is_retained": environmental_auc == 1.0 and eog_auc == 1.0,
    }
    return {
        "schema": "eog_distribution_gate_shrinkage_v0_2",
        "n_modules": n_modules,
        "n_targets": len(target_ids),
        "model_fingerprint": model.fingerprint,
        "structural_gate_weight": model.structural_gate_weight,
        "structural_gate_cross_fitted": model.structural_gate_cross_fitted,
        "training_gate_log_loss": model.training_gate_log_loss,
        "auc": {
            "environmental_support": environmental_auc,
            "eog_distribution_support": eog_auc,
        },
        "checks": checks,
        "all_checks_pass": bool(all(checks.values())),
        "claim_boundary": (
            "nested synthetic fallback contract only; demonstrates exact reduction to "
            "the environmental model when the structural field is uninformative"
        ),
    }


def main() -> None:
    result = run_gate_shrinkage_benchmark()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit("EOG structural-gate shrinkage benchmark failed")


if __name__ == "__main__":
    main()
