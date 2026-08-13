"""Development sensitivity for the final EOG-R genetic-distance contract.

This screen is deliberately run before any empirical genetic outcome. It compares a
small predeclared grid of finite-horizon reachability-distance definitions against three
known-truth regimes: geography-only null, smooth IBD+IBE reference-complete truth, and an
intermediate-structure truth omitted from the geography-only current-flow reference.

The output is development evidence for choosing a single candidate to freeze in a later
synthetic confirmation. It is not itself confirmatory or empirical genetic evidence.
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
MAX_STEPS = (4, 6, 8, 12)
SUPPORT_FLOORS = (1e-6, 1e-9, 1e-12)
SYMMETRISATIONS = ("mean_log", "max_log")
NODE_IDS = (
    "top0", "top1", "top2", "top3",
    "bottom0", "bottom1", "bottom2", "bottom3",
)
COORDINATES = np.asarray(
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    dtype=float,
)
ENVIRONMENT = np.asarray((0.0, 0.2, 0.4, 0.6, 1.5, 1.7, 1.9, 2.1), dtype=float)

# Development eligibility boundaries are intentionally modest. They ask that a candidate
# not manufacture a material gain in reference-complete regimes while retaining a clear
# gain when intermediate structure is missing from the reference.
NULL_MIN_DELTA = -1e-5
STRUCTURE_MAX_DELTA = -5e-4
MIN_STRUCTURE_FAVOURABLE_SEEDS = 6


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


def _leave_one_population_out_mse(
    response: np.ndarray, predictors: tuple[np.ndarray, ...]
) -> float:
    n = response.shape[0]
    squared_errors: list[float] = []
    for held_out in range(n):
        training: list[list[float]] = []
        testing: list[list[float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                row = [response[i, j], *[matrix[i, j] for matrix in predictors]]
                (testing if held_out in (i, j) else training).append(row)
        train = np.asarray(training, dtype=float)
        test = np.asarray(testing, dtype=float)
        coefficients = np.linalg.lstsq(
            np.column_stack([np.ones(len(train)), train[:, 1:]]),
            train[:, 0],
            rcond=None,
        )[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ coefficients
        squared_errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(squared_errors))


def _responses(
    truth_support: np.ndarray, *, migration_scale: float
) -> dict[int, np.ndarray]:
    return {
        seed: simulate_neutral_drift_migration(
            truth_support,
            migration_scale=migration_scale,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
        ).pairwise_fst
        for seed in SEEDS
    }


def _reference_mse_by_seed(
    responses: dict[int, np.ndarray], reference: np.ndarray
) -> dict[int, float]:
    return {
        seed: _leave_one_population_out_mse(response, (reference,))
        for seed, response in responses.items()
    }


def _candidate_increment(
    responses: dict[int, np.ndarray],
    reference: np.ndarray,
    reference_mse: dict[int, float],
    eog_distance: np.ndarray,
) -> tuple[float, int, list[dict[str, float | int]]]:
    rows: list[dict[str, float | int]] = []
    for seed in SEEDS:
        augmented = _leave_one_population_out_mse(
            responses[seed],
            (reference, eog_distance),
        )
        delta = augmented - reference_mse[seed]
        rows.append(
            {
                "seed": int(seed),
                "reference_mse": float(reference_mse[seed]),
                "reference_plus_eog_mse": float(augmented),
                "delta_mse": float(delta),
            }
        )
    deltas = np.asarray([row["delta_mse"] for row in rows], dtype=float)
    return float(np.mean(deltas)), int(np.sum(deltas < 0.0)), rows


def evaluate() -> dict[str, object]:
    d_geo = _distance(COORDINATES)
    d_env = _distance(ENVIRONMENT)
    geo_support = np.exp(-d_geo / 1.0)
    env_support = np.exp(-d_env / 0.5)
    np.fill_diagonal(geo_support, 0.0)
    np.fill_diagonal(env_support, 0.0)
    ibe_support = geo_support * env_support
    structural_support = _structure_support()

    geo_reference = _effective_resistance(geo_support)
    ibe_reference = _effective_resistance(ibe_support)

    regime = {
        "geography_null": {
            "operator": _operator(geo_support),
            "responses": _responses(geo_support, migration_scale=0.03),
            "reference": geo_reference,
        },
        "ibe_reference_complete": {
            "operator": _operator(ibe_support),
            "responses": _responses(ibe_support, migration_scale=0.03),
            "reference": ibe_reference,
        },
        "intermediate_structure": {
            "operator": _operator(structural_support),
            "responses": _responses(structural_support, migration_scale=0.06),
            "reference": geo_reference,
        },
    }
    for value in regime.values():
        value["reference_mse"] = _reference_mse_by_seed(
            value["responses"], value["reference"]
        )

    rows: list[dict[str, object]] = []
    for max_steps in MAX_STEPS:
        for support_floor in SUPPORT_FLOORS:
            for symmetrisation in SYMMETRISATIONS:
                record: dict[str, object] = {
                    "max_steps": int(max_steps),
                    "support_floor": float(support_floor),
                    "symmetrisation": symmetrisation,
                    "regimes": {},
                }
                for regime_id, value in regime.items():
                    reachability = pairwise_reachability_distances(
                        value["operator"],
                        max_steps=max_steps,
                        support_floor=support_floor,
                        symmetrization=symmetrisation,
                    )
                    mean_delta, favourable, seed_rows = _candidate_increment(
                        value["responses"],
                        value["reference"],
                        value["reference_mse"],
                        reachability.symmetric_distance,
                    )
                    record["regimes"][regime_id] = {
                        "mean_delta_mse": mean_delta,
                        "favourable_seed_count": favourable,
                        "reachability_fingerprint": reachability.fingerprint,
                        "rows": seed_rows,
                    }

                geo_delta = record["regimes"]["geography_null"]["mean_delta_mse"]
                ibe_delta = record["regimes"]["ibe_reference_complete"]["mean_delta_mse"]
                structure_delta = record["regimes"]["intermediate_structure"]["mean_delta_mse"]
                structure_favourable = record["regimes"]["intermediate_structure"]["favourable_seed_count"]
                record["eligible"] = bool(
                    geo_delta >= NULL_MIN_DELTA
                    and ibe_delta >= NULL_MIN_DELTA
                    and structure_delta <= STRUCTURE_MAX_DELTA
                    and structure_favourable >= MIN_STRUCTURE_FAVOURABLE_SEEDS
                )
                rows.append(record)

    eligible = [row for row in rows if row["eligible"]]
    # Development selection policy: among candidates satisfying all three scientific
    # boundaries, prefer the shortest horizon, then the least extreme floor, then
    # mean-log symmetrisation. This reduces tuning complexity rather than selecting the
    # largest favourable effect.
    selected = None
    if eligible:
        selected = min(
            eligible,
            key=lambda row: (
                row["max_steps"],
                -np.log10(row["support_floor"]),
                0 if row["symmetrisation"] == "mean_log" else 1,
            ),
        )

    return {
        "status": "development-genetic-distance-sensitivity-before-empirical-genetics",
        "seeds": list(SEEDS),
        "grid": {
            "max_steps": list(MAX_STEPS),
            "support_floors": list(SUPPORT_FLOORS),
            "symmetrisations": list(SYMMETRISATIONS),
        },
        "eligibility": {
            "null_min_delta_mse": NULL_MIN_DELTA,
            "structure_max_delta_mse": STRUCTURE_MAX_DELTA,
            "min_structure_favourable_seeds": MIN_STRUCTURE_FAVOURABLE_SEEDS,
        },
        "n_candidates": len(rows),
        "n_eligible": len(eligible),
        "selected_candidate": None if selected is None else {
            "max_steps": selected["max_steps"],
            "support_floor": selected["support_floor"],
            "symmetrisation": selected["symmetrisation"],
            "regimes": selected["regimes"],
        },
        "candidates": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
