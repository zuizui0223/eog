"""Held-out synthetic ranking benchmark for the experimental EOG distribution model.

The benchmark builds repeated source modules.  Each module contains a reachable target
and a blocked target with the same environmental state and the same direct distance to
the known source.  Only the reachable target has intermediate landscape nodes.  Target
labels are never supplied to model fitting.

This is a proof-of-estimand benchmark: environmental-only and environmental-plus-
nearest-source scores are tied by construction, while source-conditioned graph
accessibility can distinguish the targets.  It is not a claim of general superiority.
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
    target_ids: list[str] = []
    target_response: list[int] = []
    source_for_target: dict[str, str] = {}

    for module in range(n_modules):
        latitude = -5.25 + module * 1.5
        prefix = f"m{module:02d}"
        source = f"{prefix}_source"
        negative = f"{prefix}_negative"
        open_1 = f"{prefix}_open_1"
        open_2 = f"{prefix}_open_2"
        reachable = f"{prefix}_reachable"
        blocked = f"{prefix}_blocked"
        nodes.extend(
            [
                BridgeNode(source, latitude, 0.00, (0.8,)),
                BridgeNode(open_1, latitude, 0.12, (0.8,)),
                BridgeNode(open_2, latitude, 0.24, (0.8,)),
                BridgeNode(reachable, latitude, 0.36, (0.8,)),
                BridgeNode(blocked, latitude, -0.36, (0.8,)),
                BridgeNode(negative, latitude, 0.90, (0.1,)),
            ]
        )
        observed_ids.extend([source, negative])
        observed_response.extend([1, 0])
        target_ids.extend([reachable, blocked])
        target_response.extend([1, 0])
        source_for_target[reachable] = source
        source_for_target[blocked] = source

    return nodes, observed_ids, observed_response, target_ids, target_response, source_for_target


def run_heldout_ranking_benchmark(n_modules: int = 8) -> dict[str, object]:
    (
        nodes,
        observed_ids,
        observed_response,
        target_ids,
        target_response,
        source_for_target,
    ) = build_replicated_landscape(n_modules)
    by_id = {node.node_id: node for node in nodes}
    model = fit_eog_distribution(
        nodes,
        observed_ids,
        observed_response,
        EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
            min_class_count=n_modules,
        ),
        reference_provenance="replicated held-out structural ranking benchmark",
    )
    prediction = model.predict(target_ids)
    labels = np.asarray(target_response, dtype=int)
    nearest_distance = np.asarray(
        [
            haversine_km(by_id[source_for_target[target]], by_id[target])
            for target in target_ids
        ],
        dtype=float,
    )

    # A simple nearest-source augmented score.  Its absolute scaling is irrelevant
    # here because reachable/blocked targets have exactly matched environmental
    # support and direct source distance within every repeated module, producing the
    # same score distribution in both classes.
    distance_scale = float(np.median(nearest_distance))
    support_distance_score = prediction.environmental_support * np.exp(
        -nearest_distance / distance_scale
    )

    environmental_auc = _auc(labels, prediction.environmental_support)
    support_distance_auc = _auc(labels, support_distance_score)
    eog_auc = _auc(labels, prediction.distribution_support)
    accessibility_auc = _auc(labels, prediction.structural_accessibility)

    checks = {
        "target_labels_are_held_out": set(target_ids).isdisjoint(observed_ids),
        "environmental_only_is_tied": abs(environmental_auc - 0.5) <= 1e-12,
        "support_plus_nearest_source_is_tied": abs(support_distance_auc - 0.5) <= 1e-12,
        "accessibility_separates_structural_state": accessibility_auc == 1.0,
        "distribution_support_separates_structural_state": eog_auc == 1.0,
        "eog_gain_over_environmental_auc": eog_auc - environmental_auc >= 0.49,
        "eog_gain_over_support_distance_auc": eog_auc - support_distance_auc >= 0.49,
    }
    return {
        "schema": "eog_distribution_heldout_ranking_v0",
        "n_modules": n_modules,
        "n_targets": len(target_ids),
        "model_fingerprint": model.fingerprint,
        "auc": {
            "environmental_support": environmental_auc,
            "environmental_plus_nearest_source": support_distance_auc,
            "structural_accessibility": accessibility_auc,
            "eog_distribution_support": eog_auc,
        },
        "checks": checks,
        "all_checks_pass": bool(all(checks.values())),
        "claim_boundary": (
            "proof-of-estimand synthetic benchmark; not evidence of universal predictive "
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
