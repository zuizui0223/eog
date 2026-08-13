"""Reference-depth screen for EOG-R neutral-genetic validation.

The benchmark asks two deliberately different questions under known truth:

1. **geography-only null** — migration is a smooth function of Euclidean distance;
   a geography-only current-flow reference should already be sufficient and adding
   EOG-R must not manufacture a mean predictive gain;
2. **intermediate-structure regime** — the same coordinates contain separated chains
   and a severe within-chain bottleneck; a geography-only current-flow reference is
   intentionally incomplete, so a frozen EOG-R distance may add information.

This is development validation, not empirical genetic evidence and not a final choice
of the genetic-validation metric.
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

SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
COORDINATES = np.asarray(
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    dtype=float,
)
NODE_IDS = ("top0", "top1", "top2", "top3", "bottom0", "bottom1", "bottom2", "bottom3")


def _euclidean_matrix(coordinates: np.ndarray) -> np.ndarray:
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("conductance must be square")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError("current-flow reference requires symmetric conductance")
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pseudoinverse = np.linalg.pinv(laplacian)
    diagonal = np.diag(pseudoinverse)
    resistance = diagonal[:, None] + diagonal[None, :] - 2.0 * pseudoinverse
    resistance = np.maximum(resistance, 0.0)
    np.fill_diagonal(resistance, 0.0)
    return resistance


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
        coefficients = np.linalg.lstsq(
            np.column_stack([np.ones(len(train)), train[:, 1:]]),
            train[:, 0],
            rcond=None,
        )[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ coefficients
        squared_errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(squared_errors))


def _operator_from_symmetric_support(support: np.ndarray):
    edges: list[DynamicReachabilityEdge] = []
    n = support.shape[0]
    for i in range(n):
        for j in range(n):
            if i != j and support[i, j] > 0.0:
                edges.append(
                    DynamicReachabilityEdge(
                        i,
                        j,
                        geographic_support=float(support[i, j]),
                    )
                )
    return build_dynamic_transition_operator(NODE_IDS, edges, loss_support=0.5)


def _geography_only_support(geographic: np.ndarray) -> np.ndarray:
    support = np.exp(-geographic / 1.0)
    np.fill_diagonal(support, 0.0)
    return support


def _intermediate_structure_support() -> np.ndarray:
    support = np.zeros((len(NODE_IDS), len(NODE_IDS)), dtype=float)
    for a, b, value in (
        (0, 1, 0.9),
        (1, 2, 0.9),
        (2, 3, 0.9),
        (4, 5, 0.9),
        (5, 6, 0.03),
        (6, 7, 0.9),
    ):
        support[a, b] = support[b, a] = value
    return support


def _run_regime(
    truth_support: np.ndarray,
    geographic_reference: np.ndarray,
    *,
    migration_scale: float,
) -> dict[str, object]:
    operator = _operator_from_symmetric_support(truth_support)
    reachability = pairwise_reachability_distances(
        operator,
        max_steps=8,
        support_floor=1e-12,
        symmetrization="mean_log",
    )
    rows = []
    for seed in SEEDS:
        simulated = simulate_neutral_drift_migration(
            truth_support,
            migration_scale=migration_scale,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        )
        reference_mse = _leave_one_population_out_mse(
            simulated.pairwise_fst,
            (geographic_reference,),
        )
        augmented_mse = _leave_one_population_out_mse(
            simulated.pairwise_fst,
            (geographic_reference, reachability.symmetric_distance),
        )
        rows.append(
            {
                "seed": int(seed),
                "reference_mse": reference_mse,
                "reference_plus_eog_mse": augmented_mse,
                "delta_mse": augmented_mse - reference_mse,
                "genetic_fingerprint": simulated.fingerprint,
            }
        )
    deltas = np.asarray([row["delta_mse"] for row in rows], dtype=float)
    return {
        "operator_fingerprint": operator.fingerprint,
        "reachability_fingerprint": reachability.fingerprint,
        "mean_delta_mse": float(np.mean(deltas)),
        "favourable_seed_count": int(np.sum(deltas < 0.0)),
        "rows": rows,
    }


def evaluate() -> dict[str, object]:
    geographic = _euclidean_matrix(COORDINATES)
    geographic_support = _geography_only_support(geographic)
    geographic_current_flow = _effective_resistance(geographic_support)

    null_result = _run_regime(
        geographic_support,
        geographic_current_flow,
        migration_scale=0.03,
    )
    structural_result = _run_regime(
        _intermediate_structure_support(),
        geographic_current_flow,
        migration_scale=0.06,
    )

    # Predeclared development interpretation: on a geography-only truth network, EOG
    # must not produce a mean gain beyond the geography-only current-flow reference.
    # When an explicit intermediate bottleneck/disconnection is absent from that
    # reference, the same candidate EOG metric should add predictive information.
    null_no_added_information = bool(null_result["mean_delta_mse"] >= 0.0)
    structure_added_information = bool(
        structural_result["mean_delta_mse"] < 0.0
        and structural_result["favourable_seed_count"] == len(SEEDS)
    )
    assert null_no_added_information
    assert structure_added_information

    return {
        "status": "development-known-truth-reference-depth",
        "seeds": list(SEEDS),
        "reference": "geography-only effective resistance/current-flow",
        "geography_only_null": null_result,
        "intermediate_structure": structural_result,
        "null_no_added_information": null_no_added_information,
        "structure_added_information": structure_added_information,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
