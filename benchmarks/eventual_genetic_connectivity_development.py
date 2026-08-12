"""Development check for the hyperparameter-free eventual genetic EOG summary.

The candidate has no propagation horizon or numerical zero-support floor in its primary
symmetric predictors. It uses exact eventual first-passage support, arithmetic mean
reciprocal exchange support, continuous -log distance among exchange-supported pairs,
and a separate bidirectional-disconnection indicator.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity
from eog.neutral_genetics_simulator import simulate_neutral_drift_migration

SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
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
    laplacian = np.diag(np.sum(conductance, axis=1)) - conductance
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
        truth[a, b] = truth[b, a] = value
        reference[a, b] = reference[b, a] = value
    truth[1, 2] = 0.8
    truth[2, 1] = 0.05
    return truth, reference


def _lopo_mse(response: np.ndarray, predictors: tuple[np.ndarray, ...]) -> float:
    errors: list[float] = []
    n = response.shape[0]
    for held_out in range(n):
        training: list[list[float]] = []
        testing: list[list[float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                row = [response[i, j], *[matrix[i, j] for matrix in predictors]]
                (testing if held_out in (i, j) else training).append(row)
        train = np.asarray(training, dtype=float)
        test = np.asarray(testing, dtype=float)
        beta = np.linalg.lstsq(
            np.column_stack([np.ones(len(train)), train[:, 1:]]), train[:, 0], rcond=None
        )[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ beta
        errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(errors))


def _run(
    truth: np.ndarray,
    reference: np.ndarray,
    *,
    migration_scale: float,
) -> dict[str, object]:
    connectivity = infer_eventual_genetic_connectivity(_operator(truth))
    disconnect = connectivity.disconnected.astype(float)
    rows = []
    for seed in SEEDS:
        fst = simulate_neutral_drift_migration(
            truth,
            migration_scale=migration_scale,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        ).pairwise_fst
        reference_mse = _lopo_mse(fst, (reference,))
        augmented_mse = _lopo_mse(
            fst,
            (reference, connectivity.continuous_distance, disconnect),
        )
        rows.append(
            {
                "seed": int(seed),
                "reference_mse": reference_mse,
                "reference_plus_eog_mse": augmented_mse,
                "delta_mse": augmented_mse - reference_mse,
            }
        )
    deltas = np.asarray([row["delta_mse"] for row in rows], dtype=float)
    return {
        "connectivity_fingerprint": connectivity.fingerprint,
        "disconnected_pair_entries": int(np.sum(connectivity.disconnected)),
        "distance_cap": connectivity.disconnected_distance_cap,
        "mean_delta_mse": float(np.mean(deltas)),
        "favourable_seed_count": int(np.sum(deltas < 0.0)),
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

    result = {
        "status": "development-hyperparameter-free-eventual-genetic-connectivity",
        "seeds": list(SEEDS),
        "method": (
            "exact eventual first-passage; reciprocal arithmetic-mean support; "
            "continuous connected-pair distance plus explicit bidirectional-disconnection indicator"
        ),
        "regimes": {
            "geography_null": _run(
                geo_support,
                _effective_resistance(geo_support),
                migration_scale=0.03,
            ),
            "ibe_reference_complete": _run(
                ibe_support,
                _effective_resistance(ibe_support),
                migration_scale=0.03,
            ),
            "intermediate_structure": _run(
                _structure_support(),
                _effective_resistance(geo_support),
                migration_scale=0.06,
            ),
            "directional_structure_fst_boundary": _run(
                directional_truth,
                _effective_resistance(directional_reference_support),
                migration_scale=0.05,
            ),
        },
    }

    # Development boundaries. Directional FST is deliberately not required to improve:
    # FST is symmetric and is not promoted as a validator of migration direction.
    assert result["regimes"]["geography_null"]["mean_delta_mse"] >= -1e-5
    assert result["regimes"]["ibe_reference_complete"]["mean_delta_mse"] >= -1e-5
    assert result["regimes"]["intermediate_structure"]["mean_delta_mse"] < -5e-4
    assert result["regimes"]["intermediate_structure"]["favourable_seed_count"] >= 6
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
