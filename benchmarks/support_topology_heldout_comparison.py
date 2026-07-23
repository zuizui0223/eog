"""Frozen held-out comparator benchmark for spatial support topology.

This benchmark fixes one synthetic fragmented landscape, one historical anchor,
one candidate set, and binary held-out detections. It compares five predeclared
scoring rules without fitting to the held-out labels:

1. local support;
2. inverse distance to the historical anchor;
3. equal-weight support plus inverse distance;
4. detached membership at one threshold;
5. persistent detached membership across thresholds.

The benchmark is a contract and counterexample, not empirical evidence that
support topology improves ecological prediction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog import SupportTopologyConfig, infer_support_topology


def frozen_field() -> tuple[np.ndarray, np.ndarray, dict[str, tuple[int, int]], tuple[dict[str, object], ...]]:
    support = np.full((5, 11), 0.05, dtype=float)
    unavailable = np.ones_like(support, dtype=bool)

    west = np.array(
        [
            [0.82, 0.84, 0.80],
            [0.86, 0.88, 0.83],
            [0.79, 0.81, 0.78],
        ]
    )
    east = west.copy()
    unavailable[1:4, 0:3] = False
    unavailable[1:4, 5:8] = False
    support[1:4, 0:3] = west
    support[1:4, 5:8] = east

    # Two isolated patches appear at 0.70 but persist for only two of the three
    # thresholds, so they are transient under minimum_persistence_steps=3.
    unavailable[1, 10] = False
    unavailable[3, 10] = False
    support[1, 10] = 0.75
    support[3, 10] = 0.74

    anchors = {"historical_west": (2, 1)}
    candidates = (
        {"candidate_id": "east_01", "cell": (1, 5), "detected": 1},
        {"candidate_id": "east_02", "cell": (1, 6), "detected": 1},
        {"candidate_id": "east_03", "cell": (2, 5), "detected": 1},
        {"candidate_id": "east_04", "cell": (2, 6), "detected": 1},
        {"candidate_id": "west_01", "cell": (1, 0), "detected": 0},
        {"candidate_id": "west_02", "cell": (1, 1), "detected": 0},
        {"candidate_id": "west_03", "cell": (2, 0), "detected": 0},
        {"candidate_id": "west_04", "cell": (2, 1), "detected": 0},
        {"candidate_id": "transient_01", "cell": (1, 10), "detected": 0},
        {"candidate_id": "transient_02", "cell": (3, 10), "detected": 0},
    )
    return support, unavailable, anchors, candidates


def _minmax(values: np.ndarray) -> np.ndarray:
    low = float(values.min())
    high = float(values.max())
    if high == low:
        return np.zeros_like(values, dtype=float)
    return (values - low) / (high - low)


def _roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    if not len(positives) or not len(negatives):
        raise ValueError("ROC AUC requires positive and negative held-out labels")
    comparisons = [
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    ]
    return float(np.mean(comparisons))


def _brier(labels: np.ndarray, scores: np.ndarray) -> float:
    return float(np.mean((scores - labels) ** 2))


def _birth_class_by_cell(result) -> dict[tuple[int, int], str]:
    classes: dict[tuple[int, int], str] = {}
    for component in result.components:
        for cell in component.birth_cells:
            classes[cell] = component.component_class
    return classes


def run_benchmark() -> dict[str, object]:
    support, unavailable, anchors, candidates = frozen_field()
    labels = np.asarray([row["detected"] for row in candidates], dtype=int)
    cells = [tuple(row["cell"]) for row in candidates]

    local_support = np.asarray([support[cell] for cell in cells], dtype=float)
    anchor_cell = next(iter(anchors.values()))
    distance = np.asarray(
        [np.hypot(cell[0] - anchor_cell[0], cell[1] - anchor_cell[1]) for cell in cells],
        dtype=float,
    )
    inverse_distance = 1.0 - _minmax(distance)
    support_scaled = _minmax(local_support)
    support_plus_distance = 0.5 * support_scaled + 0.5 * inverse_distance

    single = infer_support_topology(
        support,
        anchors,
        SupportTopologyConfig((0.70,), minimum_persistence_steps=1),
        missing_mask=unavailable,
    )
    persistent = infer_support_topology(
        support,
        anchors,
        SupportTopologyConfig((0.80, 0.70, 0.60), minimum_persistence_steps=3),
        missing_mask=unavailable,
    )
    single_classes = _birth_class_by_cell(single)
    persistent_classes = _birth_class_by_cell(persistent)

    single_threshold = np.asarray(
        [
            1.0
            if single_classes.get(cell) == "persistent_detached_component"
            else 0.0
            for cell in cells
        ],
        dtype=float,
    )
    multi_threshold = np.asarray(
        [
            1.0
            if persistent_classes.get(cell) == "persistent_detached_component"
            else 0.0
            for cell in cells
        ],
        dtype=float,
    )

    methods = {
        "support_only": support_scaled,
        "distance_only": inverse_distance,
        "support_plus_distance": support_plus_distance,
        "single_threshold_detached": single_threshold,
        "multi_threshold_persistent": multi_threshold,
    }
    metrics = {
        method: {
            "roc_auc": _roc_auc(labels, scores),
            "brier_score": _brier(labels, scores),
        }
        for method, scores in methods.items()
    }
    candidate_rows = []
    for index, candidate in enumerate(candidates):
        candidate_rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "cell": list(candidate["cell"]),
                "detected": int(candidate["detected"]),
                "support": float(local_support[index]),
                "distance_to_anchor": float(distance[index]),
                "single_threshold_class": single_classes.get(cells[index]),
                "multi_threshold_class": persistent_classes.get(cells[index]),
                "scores": {method: float(scores[index]) for method, scores in methods.items()},
            }
        )

    return {
        "benchmark": "support_topology_heldout_comparison_v1",
        "thresholds": [0.80, 0.70, 0.60],
        "single_threshold": 0.70,
        "minimum_persistence_steps": 3,
        "candidate_count": len(candidates),
        "positive_count": int(labels.sum()),
        "metrics": metrics,
        "candidates": candidate_rows,
        "claim_limit": (
            "This frozen synthetic comparison demonstrates a constructed failure mode for local support, "
            "distance, and a single threshold. It does not establish empirical predictive superiority, "
            "occupancy probability, colonisation, dispersal connectivity, or transfer to real taxa."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
