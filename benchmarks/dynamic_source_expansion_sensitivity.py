"""Nested self-excluded source-expansion sensitivity for EOG v2 occurrence support.

The benchmark asks whether additional *training* positives can be used as contemporary
sources without response leakage. Every outer-test label is unavailable during source
construction. Every outer-training row receives source-derived calibration features only
from an inner fold in which that row is excluded from the source set.

This is development sensitivity, not a frozen empirical result.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)
from dynamic_occurrence_comparator_ladder import (
    _brier,
    _log_loss,
    _ridge_logistic_fit,
    _ridge_logistic_predict,
)

SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
N_ROWS = 8
N_TARGET_COLUMNS = 6
MAX_STEPS = 6
SOURCE_SCALE = 1.5
LOSS_SUPPORT = 0.55


def _build_graph():
    coordinates = []
    viability = []
    node_ids = []
    for x in range(N_TARGET_COLUMNS + 1):
        for row in range(N_ROWS):
            node_ids.append(f"x{x}_r{row}")
            coordinates.append((float(x), float(row)))
            viability.append(0.62 + 0.18 * np.sin(0.8 * row + 0.35 * x))
    coordinates = np.asarray(coordinates, dtype=float)
    viability = np.clip(np.asarray(viability, dtype=float), 0.25, 0.95)

    def index(x: int, row: int) -> int:
        return x * N_ROWS + row

    raw = np.zeros((len(node_ids), len(node_ids)), dtype=float)
    for x in range(N_TARGET_COLUMNS):
        for row in range(N_ROWS):
            a, b = index(x, row), index(x + 1, row)
            support = 0.72
            if x == 2:
                support *= (0.45, 0.60, 0.80, 1.0)[row % 4]
            raw[a, b] = raw[b, a] = support
    for x in range(N_TARGET_COLUMNS + 1):
        for row in range(N_ROWS - 1):
            a, b = index(x, row), index(x, row + 1)
            raw[a, b] = raw[b, a] = 0.10

    edges = [
        DynamicReachabilityEdge(i, j, geographic_support=float(raw[i, j]))
        for i in range(len(node_ids))
        for j in range(len(node_ids))
        if i != j and raw[i, j] > 0.0
    ]
    operator = build_dynamic_transition_operator(
        tuple(node_ids), edges, loss_support=LOSS_SUPPORT
    )
    base_sources = np.asarray([index(0, row) for row in range(N_ROWS)], dtype=int)
    candidates = np.asarray(
        [index(x, row) for x in range(1, N_TARGET_COLUMNS + 1) for row in range(N_ROWS)],
        dtype=int,
    )
    folds = np.asarray(
        [x - 1 for x in range(1, N_TARGET_COLUMNS + 1) for _ in range(N_ROWS)],
        dtype=int,
    )
    return tuple(node_ids), coordinates, viability, raw, operator, base_sources, candidates, folds


def _pairwise_distance(coordinates: np.ndarray) -> np.ndarray:
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _finite_first_passage_matrix(operator) -> np.ndarray:
    n = len(operator.node_ids)
    result = np.zeros((n, n), dtype=float)
    np.fill_diagonal(result, 1.0)
    for i, source in enumerate(operator.node_ids):
        for j, target in enumerate(operator.node_ids):
            if i == j:
                continue
            result[i, j] = summarize_first_passage(
                operator,
                [source],
                target,
                max_steps=MAX_STEPS,
            ).horizon_support
    return result


def _source_features(
    sources: np.ndarray,
    targets: np.ndarray,
    distance: np.ndarray,
    first_passage: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if sources.size == 0:
        raise ValueError("at least one source is required")
    dist = distance[np.ix_(sources, targets)]
    nearest = np.exp(-np.min(dist, axis=0) / SOURCE_SCALE)
    pressure = np.sum(np.exp(-dist / SOURCE_SCALE), axis=0)
    support = first_passage[np.ix_(sources, targets)]
    dynamic_union = 1.0 - np.prod(1.0 - np.clip(support, 0.0, 1.0), axis=0)
    return nearest, pressure, dynamic_union


def _simulate_current_occurrence(raw: np.ndarray, viability: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    occupied = np.zeros(raw.shape[0], dtype=bool)
    occupied[:N_ROWS] = True
    for _ in range(MAX_STEPS):
        pressure = occupied.astype(float) @ raw
        probability = (1.0 - np.exp(-0.95 * pressure)) * viability
        probability[occupied] = 1.0
        newly = rng.random(len(occupied)) < probability
        occupied |= newly
    return occupied


def _fit_predict(train_x, train_y, test_x):
    model = _ridge_logistic_fit(np.asarray(train_x, dtype=float), np.asarray(train_y, dtype=int))
    return _ridge_logistic_predict(model, np.asarray(test_x, dtype=float))


def _evaluate_seed(seed: int, prepared: dict[str, object]) -> dict[str, object]:
    viability = prepared["viability"]
    candidates = prepared["candidates"]
    folds = prepared["folds"]
    base_sources = prepared["base_sources"]
    distance = prepared["distance"]
    first_passage = prepared["first_passage"]
    labels_all = _simulate_current_occurrence(prepared["raw"], viability, seed)
    response = labels_all[candidates].astype(int)

    prediction = {
        "environment": np.full(len(candidates), np.nan),
        "fixed_dynamic": np.full(len(candidates), np.nan),
        "expanded_nearest": np.full(len(candidates), np.nan),
        "expanded_pressure": np.full(len(candidates), np.nan),
        "expanded_dynamic": np.full(len(candidates), np.nan),
        "leaky_expanded_dynamic": np.full(len(candidates), np.nan),
    }
    fixed = _source_features(base_sources, candidates, distance, first_passage)[2]
    outer_invariance_max_abs = 0.0
    self_exclusion_positive_count = 0
    leaky_positive_source_count = 0

    for outer_fold in range(N_TARGET_COLUMNS):
        test_mask = folds == outer_fold
        train_mask = ~test_mask
        train_positions = np.flatnonzero(train_mask)
        test_positions = np.flatnonzero(test_mask)
        train_nodes = candidates[train_positions]
        test_nodes = candidates[test_positions]
        train_labels = response[train_positions]

        expanded_outer_sources = np.unique(
            np.concatenate([base_sources, train_nodes[train_labels == 1]])
        )
        outer_nearest, outer_pressure, outer_dynamic = _source_features(
            expanded_outer_sources, test_nodes, distance, first_passage
        )

        # Explicit outer-label invariance audit: flipping every test label cannot change
        # source construction because only outer-training labels are used.
        flipped_response = response.copy()
        flipped_response[test_positions] = 1 - flipped_response[test_positions]
        expanded_flipped_sources = np.unique(
            np.concatenate([base_sources, train_nodes[train_labels == 1]])
        )
        flipped_features = _source_features(
            expanded_flipped_sources, test_nodes, distance, first_passage
        )
        outer_invariance_max_abs = max(
            outer_invariance_max_abs,
            *[
                float(np.max(np.abs(left - right)))
                for left, right in zip(
                    (outer_nearest, outer_pressure, outer_dynamic), flipped_features
                )
            ],
        )

        inner_nearest = np.full(len(train_positions), np.nan)
        inner_pressure = np.full(len(train_positions), np.nan)
        inner_dynamic = np.full(len(train_positions), np.nan)
        for inner_fold in sorted(set(folds[train_positions].tolist())):
            inner_hold_local = folds[train_positions] == inner_fold
            inner_fit_local = ~inner_hold_local
            hold_positions = train_positions[inner_hold_local]
            fit_positions = train_positions[inner_fit_local]
            fit_nodes = candidates[fit_positions]
            fit_labels = response[fit_positions]
            inner_sources = np.unique(
                np.concatenate([base_sources, fit_nodes[fit_labels == 1]])
            )
            # Every held-out positive training row is explicitly absent as a source.
            positive_hold_nodes = candidates[hold_positions][response[hold_positions] == 1]
            if positive_hold_nodes.size:
                assert not np.intersect1d(positive_hold_nodes, inner_sources).size
                self_exclusion_positive_count += int(positive_hold_nodes.size)
            values = _source_features(
                inner_sources,
                candidates[hold_positions],
                distance,
                first_passage,
            )
            local_slots = np.flatnonzero(inner_hold_local)
            inner_nearest[local_slots] = values[0]
            inner_pressure[local_slots] = values[1]
            inner_dynamic[local_slots] = values[2]

        assert np.isfinite(inner_nearest).all()
        assert np.isfinite(inner_pressure).all()
        assert np.isfinite(inner_dynamic).all()

        # Deliberately leaky calibration feature for audit only: positive outer-training
        # rows are included as their own sources, so their first-passage union is exactly 1.
        leaky_sources = expanded_outer_sources
        leaky_train_dynamic = _source_features(
            leaky_sources, train_nodes, distance, first_passage
        )[2]
        if np.any(train_labels == 1):
            assert np.allclose(leaky_train_dynamic[train_labels == 1], 1.0)
            leaky_positive_source_count += int(np.sum(train_labels == 1))

        train_v = viability[train_nodes]
        test_v = viability[test_nodes]
        prediction["environment"][test_positions] = _fit_predict(
            train_v[:, None], train_labels, test_v[:, None]
        )
        prediction["fixed_dynamic"][test_positions] = _fit_predict(
            np.column_stack([train_v, fixed[train_positions]]),
            train_labels,
            np.column_stack([test_v, fixed[test_positions]]),
        )
        prediction["expanded_nearest"][test_positions] = _fit_predict(
            np.column_stack([train_v, inner_nearest]),
            train_labels,
            np.column_stack([test_v, outer_nearest]),
        )
        prediction["expanded_pressure"][test_positions] = _fit_predict(
            np.column_stack([train_v, inner_pressure]),
            train_labels,
            np.column_stack([test_v, outer_pressure]),
        )
        prediction["expanded_dynamic"][test_positions] = _fit_predict(
            np.column_stack([train_v, inner_dynamic]),
            train_labels,
            np.column_stack([test_v, outer_dynamic]),
        )
        prediction["leaky_expanded_dynamic"][test_positions] = _fit_predict(
            np.column_stack([train_v, leaky_train_dynamic]),
            train_labels,
            np.column_stack([test_v, outer_dynamic]),
        )

    models = {}
    for name, score in prediction.items():
        assert np.isfinite(score).all()
        models[name] = {
            "log_loss": _log_loss(response, score),
            "brier": _brier(response, score),
        }
    return {
        "seed": int(seed),
        "prevalence": float(np.mean(response)),
        "outer_label_invariance_max_abs": outer_invariance_max_abs,
        "self_excluded_positive_rows": int(self_exclusion_positive_count),
        "leaky_positive_source_rows": int(leaky_positive_source_count),
        "models": models,
    }


def evaluate() -> dict[str, object]:
    node_ids, coordinates, viability, raw, operator, base_sources, candidates, folds = _build_graph()
    prepared = {
        "node_ids": node_ids,
        "coordinates": coordinates,
        "viability": viability,
        "raw": raw,
        "operator": operator,
        "base_sources": base_sources,
        "candidates": candidates,
        "folds": folds,
        "distance": _pairwise_distance(coordinates),
        "first_passage": _finite_first_passage_matrix(operator),
    }
    rows = [_evaluate_seed(seed, prepared) for seed in SEEDS]
    names = tuple(rows[0]["models"])
    means = {
        name: {
            "mean_log_loss": float(np.mean([row["models"][name]["log_loss"] for row in rows])),
            "mean_brier": float(np.mean([row["models"][name]["brier"] for row in rows])),
        }
        for name in names
    }
    assert max(row["outer_label_invariance_max_abs"] for row in rows) == 0.0
    assert all(row["self_excluded_positive_rows"] > 0 for row in rows)
    assert all(row["leaky_positive_source_rows"] > 0 for row in rows)
    return {
        "status": "development-nested-self-excluded-source-expansion",
        "seeds": list(SEEDS),
        "n_candidates": int(len(candidates)),
        "n_outer_folds": int(N_TARGET_COLUMNS),
        "max_steps": int(MAX_STEPS),
        "operator_fingerprint": operator.fingerprint,
        "leakage_contract": {
            "outer_test_labels_never_construct_sources": True,
            "outer_label_invariance_max_abs": float(
                max(row["outer_label_invariance_max_abs"] for row in rows)
            ),
            "inner_positive_rows_self_excluded": True,
            "leaky_audit_positive_rows_are_exact_sources": True,
        },
        "mean_models": means,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
