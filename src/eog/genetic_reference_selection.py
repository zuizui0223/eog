"""Nested conventional-reference selection for future EOG v2.1 genetic validation.

This module is intentionally future-dataset-only.  It was designed after the frozen
Zhoushan exact-genetic result and must not be used to replace or rescue that result.

The outer validation unit is a population.  For each outer held-out population, all
pairs involving that population are excluded from reference selection and fitting.
A conventional reference is then chosen by inner leave-one-population-out validation
within the remaining populations.  EOG predictors are never used to select the
conventional reference.  The selected reference and the same reference augmented by
frozen EOG predictors are finally evaluated on the untouched outer population.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .genetic_validation import (
    GeneticValidationConfig,
    _fit_ridge,
    _predict_ridge,
    _transform_response,
    _validate_disconnected,
    _validate_distance_matrix,
    _validate_response_matrix,
)


@dataclass(frozen=True)
class NestedReferenceInnerScore:
    reference_id: str
    n_inner_folds: int
    mean_population_mse: float
    mean_population_mae: float


@dataclass(frozen=True)
class NestedReferenceOuterFold:
    held_out_population: str
    selected_reference: str
    inner_scores: tuple[NestedReferenceInnerScore, ...]
    n_train_pairs: int
    n_test_pairs: int
    baseline_mse: float
    augmented_mse: float
    delta_mse: float
    baseline_mae: float
    augmented_mae: float
    delta_mae: float


@dataclass(frozen=True)
class NestedGeneticReferenceResult:
    node_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    config: GeneticValidationConfig
    n_observed_pairs: int
    folds: tuple[NestedReferenceOuterFold, ...]
    selection_counts: tuple[tuple[str, int], ...]
    baseline_pooled_mse: float
    augmented_pooled_mse: float
    pooled_delta_mse: float
    baseline_pooled_mae: float
    augmented_pooled_mae: float
    pooled_delta_mae: float
    mean_population_delta_mse: float
    mean_population_delta_mae: float
    fingerprint: str


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_candidate_id(value: object) -> str:
    candidate_id = str(value)
    if not candidate_id.strip():
        raise ValueError("reference candidate IDs must be non-empty")
    return candidate_id


def evaluate_nested_genetic_reference_selection(
    node_ids: Sequence[str],
    genetic_distance: np.ndarray,
    reference_distances: Mapping[str, np.ndarray],
    eog_continuous_distance: np.ndarray,
    eog_disconnected: np.ndarray,
    *,
    config: GeneticValidationConfig = GeneticValidationConfig(),
) -> NestedGeneticReferenceResult:
    """Select a conventional reference inside each outer population-held-out fold.

    Parameters
    ----------
    node_ids
        Population identifiers.  At least six populations are required so that an
        outer holdout still leaves enough populations for inner population-wise CV.
    genetic_distance
        Symmetric response matrix.  Missing off-diagonal pairs may be NaN, provided
        missingness is symmetric.
    reference_distances
        Predeclared conventional reference distance matrices.  Candidate input order is
        ignored; IDs are sorted lexicographically before evaluation and tie breaking.
        EOG predictors must not be included in this mapping.
    eog_continuous_distance, eog_disconnected
        Frozen EOG predictors.  They are used only after a conventional reference has
        been selected by inner CV.
    config
        Response transform and common ridge penalty.

    Notes
    -----
    Inner reference selection minimizes the equal-weight mean MSE across inner held-out
    populations.  Exact numerical ties are broken lexicographically by candidate ID.
    The primary aggregate returned here is the equal-weight mean of outer-population
    ``augmented - baseline`` MSE differences.  Negative values favour added EOG
    information.
    """

    ids = tuple(str(value) for value in node_ids)
    if len(ids) < 6 or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("node_ids must contain at least six unique non-empty IDs")
    n = len(ids)

    if not reference_distances:
        raise ValueError("reference_distances must contain at least one candidate")
    normalized_candidates: dict[str, np.ndarray] = {}
    for raw_id, values in reference_distances.items():
        candidate_id = _validate_candidate_id(raw_id)
        if candidate_id in normalized_candidates:
            raise ValueError(f"duplicate reference candidate ID: {candidate_id}")
        normalized_candidates[candidate_id] = _validate_distance_matrix(
            values,
            n,
            f"reference_distances[{candidate_id!r}]",
        )
    candidate_ids = tuple(sorted(normalized_candidates))

    response = _validate_response_matrix(genetic_distance, n)
    d_eog = _validate_distance_matrix(
        eog_continuous_distance,
        n,
        "eog_continuous_distance",
    )
    disconnected = _validate_disconnected(eog_disconnected, n).astype(float)

    upper = [
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if np.isfinite(response[i, j])
    ]
    if len(upper) < n:
        raise ValueError("too few observed genetic-distance pairs for nested validation")
    pair_array = np.asarray(upper, dtype=int)
    pair_y = _transform_response(
        np.asarray([response[i, j] for i, j in upper], dtype=float),
        config.response_transform,
    )
    candidate_values = {
        candidate_id: np.asarray(
            [normalized_candidates[candidate_id][i, j] for i, j in upper],
            dtype=float,
        )
        for candidate_id in candidate_ids
    }
    pair_eog = np.asarray([d_eog[i, j] for i, j in upper], dtype=float)
    pair_disconnected = np.asarray(
        [disconnected[i, j] for i, j in upper],
        dtype=float,
    )

    outer_folds: list[NestedReferenceOuterFold] = []
    all_baseline_squared: list[float] = []
    all_augmented_squared: list[float] = []
    all_baseline_absolute: list[float] = []
    all_augmented_absolute: list[float] = []

    for outer in range(n):
        outer_test = (pair_array[:, 0] == outer) | (pair_array[:, 1] == outer)
        outer_train = ~outer_test
        n_outer_test = int(np.sum(outer_test))
        n_outer_train = int(np.sum(outer_train))
        if n_outer_test == 0:
            continue

        inner_scores: list[NestedReferenceInnerScore] = []
        for candidate_id in candidate_ids:
            x_candidate = candidate_values[candidate_id][:, None]
            inner_mses: list[float] = []
            inner_maes: list[float] = []
            for inner in range(n):
                if inner == outer:
                    continue
                involves_inner = (pair_array[:, 0] == inner) | (pair_array[:, 1] == inner)
                inner_test = outer_train & involves_inner
                inner_train = outer_train & ~involves_inner
                n_inner_test = int(np.sum(inner_test))
                n_inner_train = int(np.sum(inner_train))
                if n_inner_test == 0 or n_inner_train <= 2:
                    continue
                model = _fit_ridge(
                    x_candidate[inner_train],
                    pair_y[inner_train],
                    config.ridge_penalty,
                )
                prediction = _predict_ridge(model, x_candidate[inner_test])
                error = pair_y[inner_test] - prediction
                inner_mses.append(float(np.mean(np.square(error))))
                inner_maes.append(float(np.mean(np.abs(error))))
            if not inner_mses:
                raise ValueError(
                    f"reference candidate {candidate_id!r} has no estimable inner folds "
                    f"inside outer holdout {ids[outer]!r}"
                )
            inner_scores.append(
                NestedReferenceInnerScore(
                    reference_id=candidate_id,
                    n_inner_folds=len(inner_mses),
                    mean_population_mse=float(np.mean(inner_mses)),
                    mean_population_mae=float(np.mean(inner_maes)),
                )
            )

        # Candidate IDs were sorted before evaluation; including the ID in the key makes
        # the deterministic lexicographic tie rule explicit.
        selected_score = min(
            inner_scores,
            key=lambda value: (value.mean_population_mse, value.reference_id),
        )
        selected = selected_score.reference_id
        baseline_x = candidate_values[selected][:, None]
        augmented_x = np.column_stack(
            [candidate_values[selected], pair_eog, pair_disconnected]
        )
        if n_outer_train <= augmented_x.shape[1] + 1:
            raise ValueError(
                f"too few outer-training pairs for held-out population {ids[outer]!r}"
            )

        baseline_model = _fit_ridge(
            baseline_x[outer_train],
            pair_y[outer_train],
            config.ridge_penalty,
        )
        augmented_model = _fit_ridge(
            augmented_x[outer_train],
            pair_y[outer_train],
            config.ridge_penalty,
        )
        baseline_prediction = _predict_ridge(baseline_model, baseline_x[outer_test])
        augmented_prediction = _predict_ridge(augmented_model, augmented_x[outer_test])
        baseline_error = pair_y[outer_test] - baseline_prediction
        augmented_error = pair_y[outer_test] - augmented_prediction
        baseline_squared = np.square(baseline_error)
        augmented_squared = np.square(augmented_error)
        baseline_absolute = np.abs(baseline_error)
        augmented_absolute = np.abs(augmented_error)

        all_baseline_squared.extend(baseline_squared.tolist())
        all_augmented_squared.extend(augmented_squared.tolist())
        all_baseline_absolute.extend(baseline_absolute.tolist())
        all_augmented_absolute.extend(augmented_absolute.tolist())
        baseline_mse = float(np.mean(baseline_squared))
        augmented_mse = float(np.mean(augmented_squared))
        baseline_mae = float(np.mean(baseline_absolute))
        augmented_mae = float(np.mean(augmented_absolute))
        outer_folds.append(
            NestedReferenceOuterFold(
                held_out_population=ids[outer],
                selected_reference=selected,
                inner_scores=tuple(inner_scores),
                n_train_pairs=n_outer_train,
                n_test_pairs=n_outer_test,
                baseline_mse=baseline_mse,
                augmented_mse=augmented_mse,
                delta_mse=float(augmented_mse - baseline_mse),
                baseline_mae=baseline_mae,
                augmented_mae=augmented_mae,
                delta_mae=float(augmented_mae - baseline_mae),
            )
        )

    if not outer_folds:
        raise ValueError("nested reference selection produced no estimable outer folds")

    selection_counts = tuple(
        (
            candidate_id,
            sum(fold.selected_reference == candidate_id for fold in outer_folds),
        )
        for candidate_id in candidate_ids
    )
    baseline_pooled_mse = float(np.mean(all_baseline_squared))
    augmented_pooled_mse = float(np.mean(all_augmented_squared))
    baseline_pooled_mae = float(np.mean(all_baseline_absolute))
    augmented_pooled_mae = float(np.mean(all_augmented_absolute))
    mean_population_delta_mse = float(np.mean([fold.delta_mse for fold in outer_folds]))
    mean_population_delta_mae = float(np.mean([fold.delta_mae for fold in outer_folds]))

    payload = {
        "node_ids": list(ids),
        "candidate_ids": list(candidate_ids),
        "config": {
            "response_transform": config.response_transform,
            "ridge_penalty": config.ridge_penalty,
        },
        "n_observed_pairs": len(upper),
        "folds": [
            {
                "held_out_population": fold.held_out_population,
                "selected_reference": fold.selected_reference,
                "inner_scores": [score.__dict__ for score in fold.inner_scores],
                "n_train_pairs": fold.n_train_pairs,
                "n_test_pairs": fold.n_test_pairs,
                "baseline_mse": fold.baseline_mse,
                "augmented_mse": fold.augmented_mse,
                "delta_mse": fold.delta_mse,
                "baseline_mae": fold.baseline_mae,
                "augmented_mae": fold.augmented_mae,
                "delta_mae": fold.delta_mae,
            }
            for fold in outer_folds
        ],
        "selection_counts": [list(value) for value in selection_counts],
        "baseline_pooled_mse": baseline_pooled_mse,
        "augmented_pooled_mse": augmented_pooled_mse,
        "pooled_delta_mse": augmented_pooled_mse - baseline_pooled_mse,
        "baseline_pooled_mae": baseline_pooled_mae,
        "augmented_pooled_mae": augmented_pooled_mae,
        "pooled_delta_mae": augmented_pooled_mae - baseline_pooled_mae,
        "mean_population_delta_mse": mean_population_delta_mse,
        "mean_population_delta_mae": mean_population_delta_mae,
    }

    return NestedGeneticReferenceResult(
        node_ids=ids,
        candidate_ids=candidate_ids,
        config=config,
        n_observed_pairs=len(upper),
        folds=tuple(outer_folds),
        selection_counts=selection_counts,
        baseline_pooled_mse=baseline_pooled_mse,
        augmented_pooled_mse=augmented_pooled_mse,
        pooled_delta_mse=float(augmented_pooled_mse - baseline_pooled_mse),
        baseline_pooled_mae=baseline_pooled_mae,
        augmented_pooled_mae=augmented_pooled_mae,
        pooled_delta_mae=float(augmented_pooled_mae - baseline_pooled_mae),
        mean_population_delta_mse=mean_population_delta_mse,
        mean_population_delta_mae=mean_population_delta_mae,
        fingerprint=_canonical_sha256(payload),
    )
