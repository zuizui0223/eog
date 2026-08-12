"""Development screen for horizon-free EOG-R genetic distances.

The exact-eventual metric is evaluated before empirical genetics against geography-only,
smooth IBD+IBE, intermediate-structure, and asymmetric migration truths. The screen is
used only to choose a later frozen synthetic-confirmation contract.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.eventual_reachability_genetics import (
    pairwise_eventual_reachability_distances,
)
from eog.neutral_genetics_simulator import simulate_neutral_drift_migration

SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
SUPPORT_FLOORS = (1e-6, 1e-9, 1e-12)
SYMMETRISATIONS = ("mean_log", "max_log", "mean_support")
NODE_IDS = (
    "top0", "top1", "top2", "top3",
    "bottom0", "bottom1", "bottom2", "bottom3",
)
COORDINATES = np.asarray(
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    dtype=float,
)
ENVIRONMENT = np.asarray((0.0, 0.2, 0.4, 0.6, 1.5, 1.7, 1.9, 2.1), dtype=float)


def _distance(values: np.ndarray) -> np.ndarray:
    if values.ndim == 1:
        return np.abs(values[:, None] - values[None, :])
    delta = values[:, None, :] - values[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pinv = np.linalg.pinv(laplacian)
    diagonal = np.diag(pinv)
    result = diagonal[:, None] + diagonal[None, :] - 2.0 * pinv
    result = np.maximum(result, 0.0)
    np.fill_diagonal(result, 0.0)
    return result


def _operator(support: np.ndarray):
    edges: list[DynamicReachabilityEdge] = []
    for i in range(len(NODE_IDS)):
        for j in range(len(NODE_IDS)):
            if i != j and support[i, j] > 0.0:
                edges.append(
                    DynamicReachabilityEdge(
                        i,
                        j,
                        geographic_support=float(support[i, j]),
                    )
                )
    return build_dynamic_transition_operator(NODE_IDS, edges, loss_support=0.5)


def _structure_support() -> np.ndarray:
    support = np.zeros((8, 8), dtype=float)
    for a, b, value in (
        (0, 1, 0.9), (1, 2, 0.9), (2, 3, 0.9),
        (4, 5, 0.9), (5, 6, 0.03), (6, 7, 0.9),
    ):
        support[a, b] = support[b, a] = value
    return support


def _directional_truth() -> tuple[np.ndarray, np.ndarray]:
    """Return directed truth and undirected reference conductance with same topology."""
    truth = np.zeros((8, 8), dtype=float)
    reference = np.zeros((8, 8), dtype=float)
    undirected_edges = (
        (0, 1, 0.8), (1, 2, 0.8), (2, 3, 0.8),
        (4, 5, 0.8), (5, 6, 0.8), (6, 7, 0.8),
        (0, 4, 0.6), (3, 7, 0.6),
    )
    for a, b, value in undirected_edges:
        reference[a, b] = reference[b, a] = value
        truth[a, b] = truth[b, a] = value
    # Only one edge is directionally biased; the undirected topology/reference is fixed.
    truth[1, 2] = 0.8
    truth[2, 1] = 0.05
    return truth, reference


def _lopo_mse(response: np.ndarray, predictors: tuple[np.ndarray, ...]) -> float:
    squared_errors: list[float] = []
    n = response.shape[0]
    for held_out in range(n):
        train_rows: list[list[float]] = []
        test_rows: list[list[float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                row = [response[i, j], *[matrix[i, j] for matrix in predictors]]
                (test_rows if held_out in (i, j) else train_rows).append(row)
        train = np.asarray(train_rows, dtype=float)
        test = np.asarray(test_rows, dtype=float)
        beta = np.linalg.lstsq(
            np.column_stack([np.ones(len(train)), train[:, 1:]]),
            train[:, 0],
            rcond=None,
        )[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ beta
        squared_errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(squared_errors))


def _simulate_rows(
    truth: np.ndarray,
    *,
    migration_scale: float,
) -> dict[int, np.ndarray]:
    return {
        seed: simulate_neutral_drift_migration(
            truth,
            migration_scale=migration_scale,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        ).pairwise_fst
        for seed in SEEDS
    }


def _evaluate_regime(
    truth: np.ndarray,
    reference: np.ndarray,
    *,
    migration_scale: float,
    support_floor: float,
    symmetrisation: str,
) -> dict[str, object]:
    operator = _operator(truth)
    reachability = pairwise_eventual_reachability_distances(
        operator,
        support_floor=support_floor,
        symmetrization=symmetrisation,
    )
    responses = _simulate_rows(truth, migration_scale=migration_scale)
    rows = []
    for seed in SEEDS:
        base = _lopo_mse(responses[seed], (reference,))
        augmented = _lopo_mse(
            responses[seed],
            (reference, reachability.symmetric_distance),
        )
        rows.append(
            {
                "seed": int(seed),
                "reference_mse": base,
                "reference_plus_eog_mse": augmented,
                "delta_mse": augmented - base,
            }
        )
    deltas = np.asarray([row["delta_mse"] for row in rows], dtype=float)
    return {
        "operator_fingerprint": operator.fingerprint,
        "reachability_fingerprint": reachability.fingerprint,
        "mean_delta_mse": float(np.mean(deltas)),
        "favourable_seed_count": int(np.sum(deltas < 0.0)),
        "zero_directional_pair_count": int(np.sum(reachability.zero_support)),
        "rows": rows,
    }


def evaluate() -> dict[str, object]:
    d_geo = _distance(COORDINATES)
    d_env = _distance(ENVIRONMENT)
    geo_support = np.exp(-d_geo / 1.0)
    env_support = np.exp(-d_env / 0.5)
    np.fill_diagonal(geo_support, 0.0)
    np.fill_diagonal(env_support, 0.0)
    ibe_support = geo_support * env_support
    structural_support = _structure_support()
    directional_truth, directional_reference_support = _directional_truth()

    regimes = {
        "geography_null": (geo_support, _effective_resistance(geo_support), 0.03),
        "ibe_reference_complete": (ibe_support, _effective_resistance(ibe_support), 0.03),
        "intermediate_structure": (structural_support, _effective_resistance(geo_support), 0.06),
        "directional_structure": (
            directional_truth,
            _effective_resistance(directional_reference_support),
            0.05,
        ),
    }

    candidates = []
    for floor in SUPPORT_FLOORS:
        for symmetrisation in SYMMETRISATIONS:
            record = {
                "support_floor": float(floor),
                "symmetrisation": symmetrisation,
                "regimes": {},
            }
            for regime_id, (truth, reference, migration_scale) in regimes.items():
                record["regimes"][regime_id] = _evaluate_regime(
                    truth,
                    reference,
                    migration_scale=migration_scale,
                    support_floor=floor,
                    symmetrisation=symmetrisation,
                )
            candidates.append(record)

    return {
        "status": "development-exact-eventual-genetic-distance-before-empirical-genetics",
        "seeds": list(SEEDS),
        "support_floors": list(SUPPORT_FLOORS),
        "symmetrisations": list(SYMMETRISATIONS),
        "n_candidates": len(candidates),
        "candidates": candidates,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
