"""Frozen synthetic confirmation for the FST-oriented eventual EOG-R candidate.

The method, truth regimes, references, seeds and gates in this file are frozen before
confirmation outcomes are inspected. Failure is a result, not a reason to retune this
confirmation.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity
from eog.neutral_genetics_simulator import simulate_neutral_drift_migration

CONFIRMATION_SEEDS = (2503, 2609, 2707, 2801, 2903, 3001, 3109, 3203)
EXPECTED_CONTRACT_FINGERPRINT = "9781b171f703010fe16efdd5adc7f12daaa5a3b0be72986438c2bd63e78db1d7"
NODE_IDS = (
    "top0", "top1", "top2", "top3",
    "bottom0", "bottom1", "bottom2", "bottom3",
)
COORDINATES = np.asarray(
    [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    dtype=float,
)
ENVIRONMENT = np.asarray((0.0, 0.2, 0.4, 0.6, 1.5, 1.7, 1.9, 2.1), dtype=float)


def _contract() -> dict[str, object]:
    return {
        "status": "frozen-before-confirmation-outcomes",
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "n_loci": 2048,
        "generations": 120,
        "effective_population_size": 80,
        "ancestral_beta": [0.8, 0.8],
        "operator_loss_support": 0.5,
        "geographic_kernel_scale": 1.0,
        "environmental_kernel_scale": 0.5,
        "regimes": {
            "geography_null": {
                "migration_scale": 0.03,
                "reference": "geography-only effective resistance/current-flow",
            },
            "ibe_reference_complete": {
                "migration_scale": 0.03,
                "reference": "geography-times-environment effective resistance/current-flow",
            },
            "intermediate_structure": {
                "migration_scale": 0.06,
                "reference": "geography-only effective resistance/current-flow",
                "truth": "two four-node chains; one chain has middle-edge support 0.03; no cross-chain migration",
            },
            "directional_structure_fst_boundary": {
                "migration_scale": 0.05,
                "reference": "effective resistance on the matched undirected topology",
                "truth": "connected two-row network with one middle edge 0.8 forward and 0.05 reverse",
                "decision_role": "record-only boundary",
            },
        },
        "method": (
            "exact eventual first-passage under frozen sub-stochastic operator; "
            "reciprocal arithmetic-mean exchange support; continuous negative-log "
            "exchange distance for connected pairs; explicit bidirectional-disconnection "
            "indicator; no propagation horizon and no numerical support-floor parameter"
        ),
        "primary_metric": "leave-one-population-out pairwise FST prediction MSE",
        "predictive_contrast": (
            "reference plus EOG continuous distance plus EOG disconnection indicator minus reference"
        ),
        "gates": {
            "geography_null_min_delta_mse": -1e-5,
            "ibe_reference_complete_min_delta_mse": -1e-5,
            "intermediate_structure_max_delta_mse": -5e-4,
            "intermediate_structure_min_favourable_seeds": 6,
        },
        "directional_fst_policy": (
            "record only; symmetric pairwise FST is not used to confirm migration direction"
        ),
        "failure_policy": (
            "retain failed confirmation; do not change seeds, gates, truth, references or method to rescue it"
        ),
    }


def _fingerprint(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


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
            np.column_stack([np.ones(len(train)), train[:, 1:]]),
            train[:, 0],
            rcond=None,
        )[0]
        prediction = np.column_stack([np.ones(len(test)), test[:, 1:]]) @ beta
        errors.extend(np.square(test[:, 0] - prediction).tolist())
    return float(np.mean(errors))


def _run_regime(
    truth: np.ndarray,
    reference: np.ndarray,
    *,
    migration_scale: float,
) -> dict[str, object]:
    operator = _operator(truth)
    connectivity = infer_eventual_genetic_connectivity(operator)
    disconnect = connectivity.disconnected.astype(float)
    rows = []
    for seed in CONFIRMATION_SEEDS:
        fst = simulate_neutral_drift_migration(
            truth,
            migration_scale=migration_scale,
            effective_population_size=80,
            generations=120,
            n_loci=2048,
            seed=seed,
            ancestral_beta=(0.8, 0.8),
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
        "operator_fingerprint": operator.fingerprint,
        "connectivity_fingerprint": connectivity.fingerprint,
        "disconnected_pair_entries": int(np.sum(connectivity.disconnected)),
        "mean_delta_mse": float(np.mean(deltas)),
        "favourable_seed_count": int(np.sum(deltas < 0.0)),
        "rows": rows,
    }


def evaluate() -> dict[str, object]:
    contract = _contract()
    contract_fingerprint = _fingerprint(contract)
    if contract_fingerprint != EXPECTED_CONTRACT_FINGERPRINT:
        raise RuntimeError("frozen confirmation contract fingerprint changed")

    d_geo = _distance(COORDINATES)
    d_env = _distance(ENVIRONMENT)
    geo_support = np.exp(-d_geo / 1.0)
    env_support = np.exp(-d_env / 0.5)
    np.fill_diagonal(geo_support, 0.0)
    np.fill_diagonal(env_support, 0.0)
    ibe_support = geo_support * env_support
    directional_truth, directional_reference = _directional_truth()

    regimes = {
        "geography_null": _run_regime(
            geo_support,
            _effective_resistance(geo_support),
            migration_scale=0.03,
        ),
        "ibe_reference_complete": _run_regime(
            ibe_support,
            _effective_resistance(ibe_support),
            migration_scale=0.03,
        ),
        "intermediate_structure": _run_regime(
            _structure_support(),
            _effective_resistance(geo_support),
            migration_scale=0.06,
        ),
        "directional_structure_fst_boundary": _run_regime(
            directional_truth,
            _effective_resistance(directional_reference),
            migration_scale=0.05,
        ),
    }

    gates = contract["gates"]
    checks = {
        "geography_null_no_added_information": {
            "value": regimes["geography_null"]["mean_delta_mse"],
            "relation": ">=",
            "threshold": gates["geography_null_min_delta_mse"],
        },
        "ibe_reference_complete_no_added_information": {
            "value": regimes["ibe_reference_complete"]["mean_delta_mse"],
            "relation": ">=",
            "threshold": gates["ibe_reference_complete_min_delta_mse"],
        },
        "intermediate_structure_added_information": {
            "value": regimes["intermediate_structure"]["mean_delta_mse"],
            "relation": "<=",
            "threshold": gates["intermediate_structure_max_delta_mse"],
        },
        "intermediate_structure_favourable_seeds": {
            "value": regimes["intermediate_structure"]["favourable_seed_count"],
            "relation": ">=",
            "threshold": gates["intermediate_structure_min_favourable_seeds"],
        },
    }
    for check in checks.values():
        if check["relation"] == ">=":
            check["passed"] = bool(check["value"] >= check["threshold"])
        else:
            check["passed"] = bool(check["value"] <= check["threshold"])

    return {
        "status": "frozen-synthetic-genetic-confirmation",
        "contract": contract,
        "contract_fingerprint": contract_fingerprint,
        "regimes": regimes,
        "directional_fst_boundary_is_record_only": True,
        "decision": {
            "passed": bool(all(check["passed"] for check in checks.values())),
            "checks": checks,
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
