"""Synthetic structural-discrimination contract for the experimental EOG distribution model.

The three target nodes are constructed to have the same environmental state and the
same direct geographic distance to the only training source.  They differ only in the
intermediate landscape structure available under the frozen graph:

- ``open_target`` has a two-step bridge;
- ``barrier_target`` has an otherwise symmetric bridge with one large declared barrier;
- ``blocked_target`` has no admissible intermediate bridge.

The benchmark therefore tests a question that pointwise environmental support and
nearest-source distance cannot distinguish by construction.
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


def build_synthetic_landscape() -> list[BridgeNode]:
    state = (0.8,)
    return [
        BridgeNode("source", 0.00, 0.00, state),
        BridgeNode("open_1", 0.00, 0.12, state),
        BridgeNode("open_2", 0.00, 0.24, state),
        BridgeNode("open_target", 0.00, 0.36, state),
        BridgeNode("barrier_1", 0.12, 0.00, state),
        BridgeNode("barrier_2", 0.24, 0.00, state),
        BridgeNode("barrier_target", 0.36, 0.00, state),
        BridgeNode("blocked_target", 0.00, -0.36, state),
        BridgeNode("negative", 1.00, 1.00, (0.1,)),
    ]


def run_synthetic_contract() -> dict[str, object]:
    nodes = build_synthetic_landscape()
    by_id = {node.node_id: node for node in nodes}
    barriers = {("barrier_1", "barrier_2"): 100.0}
    model = fit_eog_distribution(
        nodes,
        ["source", "negative"],
        [1, 0],
        EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
            min_class_count=1,
        ),
        barriers=barriers,
        reference_provenance="synthetic structural-discrimination benchmark",
    )
    target_ids = ("open_target", "barrier_target", "blocked_target")
    prediction = model.predict(target_ids)
    direct_distances = np.asarray(
        [haversine_km(by_id["source"], by_id[node_id]) for node_id in target_ids],
        dtype=float,
    )

    checks = {
        "equal_environmental_support": bool(
            np.allclose(
                prediction.environmental_support,
                prediction.environmental_support[0],
                rtol=0.0,
                atol=1e-12,
            )
        ),
        "equal_direct_source_distance": bool(
            np.allclose(direct_distances, direct_distances[0], rtol=0.0, atol=1e-9)
        ),
        "open_beats_barrier_accessibility": bool(
            prediction.structural_accessibility[0] > prediction.structural_accessibility[1]
        ),
        "barrier_beats_blocked_accessibility": bool(
            prediction.structural_accessibility[1] > prediction.structural_accessibility[2]
        ),
        "blocked_is_structurally_unreachable": bool(
            prediction.structural_accessibility[2] == 0.0
            and np.isinf(prediction.minimum_cumulative_cost[2])
        ),
        "distribution_support_preserves_structural_order": bool(
            prediction.distribution_support[0]
            > prediction.distribution_support[1]
            > prediction.distribution_support[2]
        ),
    }
    return {
        "schema": "eog_distribution_structural_discrimination_v0",
        "model_fingerprint": model.fingerprint,
        "target_ids": list(target_ids),
        "direct_source_distance_km": direct_distances.tolist(),
        "prediction": prediction.to_dict(),
        "checks": checks,
        "all_checks_pass": bool(all(checks.values())),
        "claim_boundary": (
            "synthetic estimand separation only; not evidence of empirical predictive "
            "superiority or realised movement"
        ),
    }


def main() -> None:
    result = run_synthetic_contract()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit("synthetic EOG distribution-model contract failed")


if __name__ == "__main__":
    main()
