"""Prospective synthetic genetic check for EOG-R structural reachability.

This benchmark is development validation only. It creates two parallel island chains
with matched local environments and short Euclidean cross-chain distances, but no
cross-chain migration and a severe bottleneck in one chain. Neutral genetic drift and
migration are simulated from the declared truth network. The benchmark asks whether a
frozen EOG-R distance improves leave-one-population-out prediction of simulated FST
beyond Euclidean distance alone.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.neutral_genetics_simulator import simulate_neutral_drift_migration
from eog.reachability_genetics import pairwise_reachability_distances

CONFIRMATION_SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)


def _euclidean_matrix(coordinates: np.ndarray) -> np.ndarray:
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _leave_one_population_out_mse(response: np.ndarray, predictors: tuple[np.ndarray, ...]) -> float:
    n = response.shape[0]
    squared_errors: list[float] = []
    for held_out in range(n):
        training_rows: list[list[float]] = []
        test_rows: list[list[float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                row = [response[i, j], *[matrix[i, j] for matrix in predictors]]
                (test_rows if held_out in (i, j) else training_rows).append(row)
        train = np.asarray(training_rows, dtype=float)
        test = np.asarray(test_rows, dtype=float)
        design = np.column_stack([np.ones(len(train)), train[:, 1:]])
        coefficients = np.linalg.lstsq(design, train[:, 0], rcond=None)[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ coefficients
        squared_errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(squared_errors))


def _structural_truth_operator():
    node_ids = ("top0", "top1", "top2", "top3", "bottom0", "bottom1", "bottom2", "bottom3")
    edges: list[DynamicReachabilityEdge] = []

    def add_bidirectional(a: int, b: int, support: float) -> None:
        edges.append(DynamicReachabilityEdge(a, b, geographic_support=support))
        edges.append(DynamicReachabilityEdge(b, a, geographic_support=support))

    for a, b in ((0, 1), (1, 2), (2, 3)):
        add_bidirectional(a, b, 0.9)
    add_bidirectional(4, 5, 0.9)
    add_bidirectional(5, 6, 0.03)
    add_bidirectional(6, 7, 0.9)
    return build_dynamic_transition_operator(node_ids, edges, loss_support=0.5)


def evaluate() -> dict[str, object]:
    operator = _structural_truth_operator()
    coordinates = np.asarray(
        [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
        dtype=float,
    )
    geographic = _euclidean_matrix(coordinates)
    reachability = pairwise_reachability_distances(
        operator,
        max_steps=8,
        support_floor=1e-12,
        symmetrization="mean_log",
    )

    rows = []
    for seed in CONFIRMATION_SEEDS:
        simulated = simulate_neutral_drift_migration(
            operator.raw_support,
            migration_scale=0.06,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        )
        geographic_mse = _leave_one_population_out_mse(simulated.pairwise_fst, (geographic,))
        augmented_mse = _leave_one_population_out_mse(
            simulated.pairwise_fst,
            (geographic, reachability.symmetric_distance),
        )
        rows.append(
            {
                "seed": seed,
                "geographic_only_mse": geographic_mse,
                "geographic_plus_eog_mse": augmented_mse,
                "delta_mse": augmented_mse - geographic_mse,
                "genetic_fingerprint": simulated.fingerprint,
            }
        )

    deltas = np.asarray([row["delta_mse"] for row in rows], dtype=float)
    result = {
        "status": "development-known-truth-only",
        "operator_fingerprint": operator.fingerprint,
        "reachability_fingerprint": reachability.fingerprint,
        "seeds": list(CONFIRMATION_SEEDS),
        "mean_delta_mse": float(np.mean(deltas)),
        "all_seeds_improve": bool(np.all(deltas < 0.0)),
        "rows": rows,
    }
    assert result["all_seeds_improve"]
    assert result["mean_delta_mse"] < 0.0
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
