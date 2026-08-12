"""Nested held-out ranking benchmark for the experimental EOG distribution model.

Each replicated module contains two nearby positive sources, two high-environment
structurally blocked training absences, two low-environment training absences, and a
held-out matched target pair. The target pair has the same environmental state and the
same direct distance to the nearest source, but only the positive target has a neutral
stepping-stone bridge.

Outer target labels are never supplied to fitting. The structural gate is estimated
from two inner folds. For every inner prediction, both pointwise environmental support
and structural accessibility are reconstructed without that fold's labels or sources.
"""
from __future__ import annotations

import json

import numpy as np

from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    EOGDistributionConfig,
    fit_eog_distribution,
    haversine_km,
)


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    if positives.size == 0 or negatives.size == 0:
        raise ValueError("AUC requires both classes")
    comparisons = positives[:, None] - negatives[None, :]
    return float(np.mean((comparisons > 0).astype(float) + 0.5 * (comparisons == 0)))


def build_replicated_landscape(n_modules: int = 8):
    if n_modules < 2:
        raise ValueError("n_modules must be at least two")
    nodes: list[BridgeNode] = []
    observed_ids: list[str] = []
    observed_response: list[int] = []
    gate_fold_ids: list[str] = []
    target_ids: list[str] = []
    target_response: list[int] = []
    source_ids_by_module: dict[str, tuple[str, str]] = {}

    for module in range(n_modules):
        latitude = -5.25 + module * 1.5
        prefix = f"m{module:02d}"
        source_a = f"{prefix}_source_a"
        source_b = f"{prefix}_source_b"
        blocked_train_a = f"{prefix}_blocked_train_a"
        blocked_train_b = f"{prefix}_blocked_train_b"
        low_negative_a = f"{prefix}_low_negative_a"
        low_negative_b = f"{prefix}_low_negative_b"
        open_1 = f"{prefix}_open_1"
        open_2 = f"{prefix}_open_2"
        reachable = f"{prefix}_reachable"
        blocked = f"{prefix}_blocked"
        nodes.extend(
            [
                BridgeNode(source_a, latitude + 0.005, 0.00, (0.8,)),
                BridgeNode(source_b, latitude - 0.005, 0.00, (0.8,)),
                BridgeNode(open_1, latitude, 0.12, (0.8,)),
                BridgeNode(open_2, latitude, 0.24, (0.8,)),
                BridgeNode(reachable, latitude, 0.36, (0.8,)),
                BridgeNode(blocked_train_a, latitude + 0.002, -0.24, (0.8,)),
                BridgeNode(blocked_train_b, latitude - 0.002, -0.30, (0.8,)),
                BridgeNode(blocked, latitude, -0.36, (0.8,)),
                BridgeNode(low_negative_a, latitude + 0.002, 0.90, (0.1,)),
                BridgeNode(low_negative_b, latitude - 0.002, 1.00, (0.1,)),
            ]
        )
        observed_ids.extend(
            [
                source_a,
                blocked_train_a,
                low_negative_a,
                source_b,
                blocked_train_b,
                low_negative_b,
            ]
        )
        observed_response.extend([1, 0, 0, 1, 0, 0])
        gate_fold_ids.extend(["inner_a", "inner_a", "inner_a", "inner_b", "inner_b", "inner_b"])
        target_ids.extend([reachable, blocked])
        target_response.extend([1, 0])
        source_ids_by_module[prefix] = (source_a, source_b)

    return (
        nodes,
        observed_ids,
        observed_response,
        gate_fold_ids,
        target_ids,
        target_response,
        source_ids_by_module,
    )


def run_heldout_ranking_benchmark(n_modules: int = 8) -> dict[str, object]:
    (
        nodes,
        observed_ids,
        observed_response,
        gate_fold_ids,
        target_ids,
        target_response,
        source_ids_by_module,
    ) = build_replicated_landscape(n_modules)
    by_id = {node.node_id: node for node in nodes}
    model = fit_eog_distribution(
        nodes,
        observed_ids,
        observed_response,
        EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
            structural_gate_penalty=0.01,
            min_class_count=n_modules,
        ),
        gate_fold_ids=gate_fold_ids,
        reference_provenance="nested held-out structural ranking benchmark",
    )
    prediction = model.predict(target_ids)
    labels = np.asarray(target_response, dtype=int)

    nearest_distance: list[float] = []
    for target in target_ids:
        prefix = target.split("_", 1)[0]
        source_a, source_b = source_ids_by_module[prefix]
        nearest_distance.append(
            min(
                haversine_km(by_id[source_a], by_id[target]),
                haversine_km(by_id[source_b], by_id[target]),
            )
        )
    nearest_distance_array = np.asarray(nearest_distance, dtype=float)
    distance_scale = float(np.median(nearest_distance_array))
    support_distance_score = prediction.environmental_support * np.exp(
        -nearest_distance_array / distance_scale
    )

    environmental_auc = _auc(labels, prediction.environmental_support)
    support_distance_auc = _auc(labels, support_distance_score)
    eog_auc = _auc(labels, prediction.distribution_support)
    accessibility_auc = _auc(labels, prediction.structural_accessibility)

    checks = {
        "target_labels_are_held_out": set(target_ids).isdisjoint(observed_ids),
        "structural_gate_is_training_fitted": model.structural_gate_fitted,
        "structural_gate_is_inner_cross_fitted": model.structural_gate_cross_fitted,
        "structural_gate_is_nontrivial": model.structural_gate_weight >= 0.5,
        "environmental_only_is_tied": abs(environmental_auc - 0.5) <= 1e-12,
        "support_plus_nearest_source_is_tied": abs(support_distance_auc - 0.5) <= 1e-12,
        "accessibility_separates_structural_state": accessibility_auc == 1.0,
        "distribution_support_separates_structural_state": eog_auc == 1.0,
        "eog_gain_over_environmental_auc": eog_auc - environmental_auc >= 0.49,
        "eog_gain_over_support_distance_auc": eog_auc - support_distance_auc >= 0.49,
    }
    return {
        "schema": "eog_distribution_heldout_ranking_v0_2",
        "n_modules": n_modules,
        "n_targets": len(target_ids),
        "model_fingerprint": model.fingerprint,
        "structural_gate_weight": model.structural_gate_weight,
        "structural_gate_cross_fitted": model.structural_gate_cross_fitted,
        "training_gate_log_loss": model.training_gate_log_loss,
        "auc": {
            "environmental_support": environmental_auc,
            "environmental_plus_nearest_source": support_distance_auc,
            "structural_accessibility": accessibility_auc,
            "eog_distribution_support": eog_auc,
        },
        "checks": checks,
        "all_checks_pass": bool(all(checks.values())),
        "claim_boundary": (
            "proof-of-estimand nested synthetic benchmark; not evidence of universal "
            "superiority over SDM or connectivity models"
        ),
    }


def main() -> None:
    result = run_heldout_ranking_benchmark()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit("held-out EOG distribution ranking benchmark failed")


if __name__ == "__main__":
    main()
