"""Development screen for horizon-free EOG-R genetic distances.

The exact-eventual metric is evaluated before empirical genetics against geography-only,
smooth IBD+IBE, intermediate-structure, and asymmetric migration truths. Neutral-genetic
responses are generated once per regime and then reused across candidate distance
representations, so candidate comparison does not wastefully resimulate the same truth.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_reachability_genetics import pairwise_eventual_reachability_distances
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
    edges = [
        DynamicReachabilityEdge(i, j, geographic_support=float(support[i, j]))
        for i in range(len(NODE_IDS))
        for j in range(len(NODE_IDS))
        if i != j and support[i, j] > 0.0
    ]
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
    truth = np.zeros((8, 8), dtype=float)
    reference = np.zeros((8, 8), dtype=float)
    for a, b, value in (
        (0, 1, 0.8), (1, 2, 0.8), (2, 3, 0.8),
        (4, 5, 0.8), (5, 6, 0.8), (6, 7, 0.8),
        (0, 4, 0.6), (3, 7, 0.6),
    ):
        reference[a, b] = reference[b, a] = value
        truth[a, b] = truth[b, a] = value
    truth[1, 2] = 0.8
    truth[2, 1] = 0.05
    return truth, reference


def _lopo_mse(response: np.ndarray, predictors: tuple[np.ndarray, ...]) -> float:
    errors: list[float] = []
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
        errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(errors))


def _simulate_responses(truth: np.ndarray, migration_scale: float) -> dict[int, np.ndarray]:
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


def _prepare_regime(truth: np.ndarray, reference: np.ndarray, migration_scale: float) -> dict[str, object]:
    responses = _simulate_responses(truth, migration_scale)
    reference_mse = {seed: _lopo_mse(response, (reference,)) for seed, response in responses.items()}
    return {
        "operator": _operator(truth),
        "reference": reference,
        "responses": responses,
        "reference_mse": reference_mse,
    }


def _evaluate_candidate(
    prepared: dict[str, object],
    *,
    support_floor: float,
    symmetrisation: str,
) -> dict[str, object]:
    reachability = pairwise_eventual_reachability_distances(
        prepared["operator"],
        support_floor=support_floor,
        symmetrization=symmetrisation,
    )
    rows = []
    for seed in SEEDS:
        base = float(prepared["reference_mse"][seed])
        augmented = _lopo_mse(
            prepared["responses"][seed],
            (prepared["reference"], reachability.symmetric_distance),
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
        "operator_fingerprint": prepared["operator"].fingerprint,
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
    directional_truth, directional_reference_support = _directional_truth()

    raw_regimes = {
        "geography_null": (geo_support, _effective_resistance(geo_support), 0.03),
        "ibe_reference_complete": (ibe_support, _effective_resistance(ibe_support), 0.03),
        "intermediate_structure": (_structure_support(), _effective_resistance(geo_support), 0.06),
        "directional_structure": (
            directional_truth,
            _effective_resistance(directional_reference_support),
            0.05,
        ),
    }
    prepared = {
        regime_id: _prepare_regime(truth, reference, migration_scale)
        for regime_id, (truth, reference, migration_scale) in raw_regimes.items()
    }

    candidates = []
    for floor in SUPPORT_FLOORS:
        for symmetrisation in SYMMETRISATIONS:
            candidates.append(
                {
                    "support_floor": float(floor),
                    "symmetrisation": symmetrisation,
                    "regimes": {
                        regime_id: _evaluate_candidate(
                            value,
                            support_floor=floor,
                            symmetrisation=symmetrisation,
                        )
                        for regime_id, value in prepared.items()
                    },
                }
            )

    return {
        "status": "development-exact-eventual-genetic-distance-before-empirical-genetics",
        "seeds": list(SEEDS),
        "support_floors": list(SUPPORT_FLOORS),
        "symmetrisations": list(SYMMETRISATIONS),
        "simulation_reuse_policy": "one neutral-genetic response set per regime and seed reused across candidate distance definitions",
        "n_candidates": len(candidates),
        "candidates": candidates,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
