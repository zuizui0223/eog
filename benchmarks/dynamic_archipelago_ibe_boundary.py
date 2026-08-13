"""IBD/IBE reference ladder under smooth known-truth migration.

This development benchmark deliberately creates a case where geography and endpoint
environmental differences are sufficient to construct a strong conventional
connectivity reference. EOG-R should not be promoted merely because it can re-express
the same smooth IBD/IBE structure.
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
NODE_IDS = ("top0", "top1", "top2", "top3", "bottom0", "bottom1", "bottom2", "bottom3")
COORDINATES = np.asarray(
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    dtype=float,
)
ENVIRONMENT = np.asarray((0.0, 0.2, 0.4, 0.6, 1.5, 1.7, 1.9, 2.1), dtype=float)


def _euclidean_matrix(values: np.ndarray) -> np.ndarray:
    if values.ndim == 1:
        return np.abs(values[:, None] - values[None, :])
    delta = values[:, None, :] - values[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    laplacian = np.diag(np.sum(conductance, axis=1)) - conductance
    pseudoinverse = np.linalg.pinv(laplacian)
    diagonal = np.diag(pseudoinverse)
    result = diagonal[:, None] + diagonal[None, :] - 2.0 * pseudoinverse
    result = np.maximum(result, 0.0)
    np.fill_diagonal(result, 0.0)
    return result


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


def evaluate() -> dict[str, object]:
    d_geo = _euclidean_matrix(COORDINATES)
    d_env = _euclidean_matrix(ENVIRONMENT)
    geographic_support = np.exp(-d_geo / 1.0)
    environmental_support = np.exp(-d_env / 0.5)
    np.fill_diagonal(geographic_support, 0.0)
    np.fill_diagonal(environmental_support, 0.0)
    truth_support = geographic_support * environmental_support

    edges: list[DynamicReachabilityEdge] = []
    for i in range(len(NODE_IDS)):
        for j in range(len(NODE_IDS)):
            if i == j:
                continue
            edges.append(
                DynamicReachabilityEdge(
                    i,
                    j,
                    geographic_support=float(geographic_support[i, j]),
                    environmental_support=float(environmental_support[i, j]),
                )
            )
    operator = build_dynamic_transition_operator(NODE_IDS, edges, loss_support=0.5)
    reachability = pairwise_reachability_distances(
        operator,
        max_steps=8,
        support_floor=1e-12,
        symmetrization="mean_log",
    )
    combined_current_flow = _effective_resistance(truth_support)

    rows = []
    for seed in SEEDS:
        simulated = simulate_neutral_drift_migration(
            truth_support,
            migration_scale=0.03,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        )
        ibd = _leave_one_population_out_mse(simulated.pairwise_fst, (d_geo,))
        ibd_ibe = _leave_one_population_out_mse(simulated.pairwise_fst, (d_geo, d_env))
        current_flow = _leave_one_population_out_mse(
            simulated.pairwise_fst,
            (combined_current_flow,),
        )
        current_flow_eog = _leave_one_population_out_mse(
            simulated.pairwise_fst,
            (combined_current_flow, reachability.symmetric_distance),
        )
        rows.append(
            {
                "seed": int(seed),
                "ibd_mse": ibd,
                "ibd_ibe_mse": ibd_ibe,
                "geo_env_current_flow_mse": current_flow,
                "geo_env_current_flow_plus_eog_mse": current_flow_eog,
                "eog_increment_over_strong_reference": current_flow_eog - current_flow,
                "genetic_fingerprint": simulated.fingerprint,
            }
        )

    mean_ibd = float(np.mean([row["ibd_mse"] for row in rows]))
    mean_ibd_ibe = float(np.mean([row["ibd_ibe_mse"] for row in rows]))
    mean_current_flow = float(np.mean([row["geo_env_current_flow_mse"] for row in rows]))
    mean_current_flow_eog = float(
        np.mean([row["geo_env_current_flow_plus_eog_mse"] for row in rows])
    )
    mean_increment = mean_current_flow_eog - mean_current_flow

    # Required development boundary: IBE improves over IBD; the stronger smooth
    # geography+environment current-flow reference improves further; EOG must not be
    # promoted from this regime because its mean increment beyond that reference is
    # non-favourable.
    assert mean_ibd_ibe < mean_ibd
    assert mean_current_flow < mean_ibd_ibe
    assert mean_increment >= 0.0

    return {
        "status": "development-known-truth-ibd-ibe-boundary",
        "seeds": list(SEEDS),
        "operator_fingerprint": operator.fingerprint,
        "reachability_fingerprint": reachability.fingerprint,
        "mean_ibd_mse": mean_ibd,
        "mean_ibd_ibe_mse": mean_ibd_ibe,
        "mean_geo_env_current_flow_mse": mean_current_flow,
        "mean_geo_env_current_flow_plus_eog_mse": mean_current_flow_eog,
        "mean_eog_increment_over_strong_reference": mean_increment,
        "eog_added_information_beyond_strong_reference": bool(mean_increment < 0.0),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
