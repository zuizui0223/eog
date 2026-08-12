"""Prospective empirical occurrence validation for fixed-source EOG v2.

Feature construction is intentionally response-free. Frozen sources, a frozen dynamic
operator, local viability and precomputed conventional reference features are converted
into a fingerprinted predictor bundle before any empirical occurrence response is
attached. A separate evaluator then performs predeclared fold validation.

This module validates incidence prediction, not latent occupancy or detection
probability. Presence-only unsurveyed nodes must not be encoded as zeros.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .dynamic_island_reachability import (
    DynamicTransitionOperator,
    propagate_dynamic_reachability,
)


@dataclass(frozen=True)
class FixedSourceOccurrenceFeatures:
    node_ids: tuple[str, ...]
    viability: np.ndarray
    dynamic_reachability: np.ndarray
    source_mask: np.ndarray
    reference_names: tuple[str, ...]
    reference_values: np.ndarray
    max_steps: int
    operator_fingerprint: str
    feature_fingerprint: str


@dataclass(frozen=True)
class OccurrenceModelScore:
    model_name: str
    log_loss: float
    brier: float
    n_evaluated: int


@dataclass(frozen=True)
class FixedSourceOccurrenceValidationResult:
    feature_fingerprint: str
    operator_fingerprint: str
    fold_ids: tuple[str, ...]
    model_scores: tuple[OccurrenceModelScore, ...]
    dynamic_increment_over_viability: float
    dynamic_increment_over_references: tuple[tuple[str, float], ...]
    n_evaluated: int
    n_missing_response: int


def _as_finite_vector(values: Sequence[float], n: int, label: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (n,) or not np.isfinite(result).all():
        raise ValueError(f"{label} must be a finite vector aligned with node_ids")
    return result


def _feature_fingerprint(
    node_ids: tuple[str, ...],
    viability: np.ndarray,
    dynamic: np.ndarray,
    source_mask: np.ndarray,
    reference_names: tuple[str, ...],
    reference_values: np.ndarray,
    max_steps: int,
    operator_fingerprint: str,
) -> str:
    payload = {
        "node_ids": list(node_ids),
        "viability": viability.tolist(),
        "dynamic_reachability": dynamic.tolist(),
        "source_mask": source_mask.astype(int).tolist(),
        "reference_names": list(reference_names),
        "reference_values": reference_values.tolist(),
        "max_steps": int(max_steps),
        "operator_fingerprint": operator_fingerprint,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_fixed_source_occurrence_features(
    node_ids: Sequence[str],
    viability: Sequence[float],
    source_mask: Sequence[bool],
    operator: DynamicTransitionOperator,
    *,
    max_steps: int,
    reference_features: Mapping[str, Sequence[float]] | None = None,
) -> FixedSourceOccurrenceFeatures:
    """Build response-free empirical predictors from frozen sources and references."""

    ids = tuple(str(value) for value in node_ids)
    if ids != operator.node_ids:
        raise ValueError("node_ids must exactly match the frozen operator node order")
    n = len(ids)
    local = _as_finite_vector(viability, n, "viability")
    sources = np.asarray(source_mask, dtype=bool)
    if sources.shape != (n,) or not np.any(sources):
        raise ValueError("source_mask must align and contain at least one frozen source")
    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")

    source_ids = [ids[index] for index in np.flatnonzero(sources)]
    dynamic_result = propagate_dynamic_reachability(
        operator,
        source_ids,
        max_steps=int(max_steps),
    )
    dynamic = np.asarray(dynamic_result.integrated_node_support, dtype=float)

    declared = reference_features or {}
    names = tuple(sorted(str(name) for name in declared))
    if len(names) != len(declared) or any(not name.strip() for name in names):
        raise ValueError("reference feature names must be unique non-empty strings")
    if names:
        columns = [
            _as_finite_vector(declared[name], n, f"reference feature {name}")
            for name in names
        ]
        reference_values = np.column_stack(columns)
    else:
        reference_values = np.empty((n, 0), dtype=float)

    fingerprint = _feature_fingerprint(
        ids,
        local,
        dynamic,
        sources,
        names,
        reference_values,
        int(max_steps),
        operator.fingerprint,
    )
    return FixedSourceOccurrenceFeatures(
        node_ids=ids,
        viability=local,
        dynamic_reachability=dynamic,
        source_mask=sources,
        reference_names=names,
        reference_values=reference_values,
        max_steps=int(max_steps),
        operator_fingerprint=operator.fingerprint,
        feature_fingerprint=fingerprint,
    )


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-values))


def _fit_ridge_logistic(
    predictors: np.ndarray,
    response: np.ndarray,
    *,
    l2_penalty: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(response, dtype=float)
    if len(np.unique(y)) != 2:
        raise ValueError("each training fold must contain both response classes")
    if not np.isfinite(l2_penalty) or l2_penalty < 0.0:
        raise ValueError("l2_penalty must be finite and non-negative")
    mean = np.mean(x, axis=0)
    standard_deviation = np.std(x, axis=0)
    scale = np.where(standard_deviation > 1e-12, standard_deviation, 1.0)
    z = (x - mean) / scale
    design = np.column_stack([np.ones(len(y), dtype=float), z])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.concatenate(
        [[0.0], np.full(x.shape[1], float(l2_penalty), dtype=float)]
    )

    def objective(value: np.ndarray) -> float:
        eta = design @ value
        return float(
            np.sum(np.logaddexp(0.0, eta) - y * eta)
            + 0.5 * l2_penalty * np.dot(value[1:], value[1:])
        )

    current = objective(beta)
    for _ in range(200):
        probability = _sigmoid(design @ beta)
        weights = probability * (1.0 - probability)
        gradient = design.T @ (probability - y) + penalty * beta
        hessian = design.T @ (design * weights[:, None])
        hessian += np.diag(penalty) + np.eye(hessian.shape[0]) * 1e-12
        step = np.linalg.solve(hessian, gradient)
        step_scale = 1.0
        accepted = False
        improvement = 0.0
        while step_scale >= 2.0 ** -20:
            candidate = beta - step_scale * step
            candidate_objective = objective(candidate)
            if candidate_objective <= current + 1e-12:
                improvement = current - candidate_objective
                beta = candidate
                current = candidate_objective
                accepted = True
                break
            step_scale *= 0.5
        if not accepted:
            raise RuntimeError("ridge logistic update failed")
        if np.max(np.abs(step_scale * step)) <= 1e-9 or improvement <= 1e-9:
            break
    return mean, scale, beta


def _predict(
    model: tuple[np.ndarray, np.ndarray, np.ndarray],
    predictors: np.ndarray,
) -> np.ndarray:
    mean, scale, beta = model
    z = (np.asarray(predictors, dtype=float) - mean) / scale
    return _sigmoid(np.column_stack([np.ones(len(z), dtype=float), z]) @ beta)


def _score(response: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    p = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    y = np.asarray(response, dtype=float)
    log_loss = float(
        np.mean(-(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))
    )
    brier = float(np.mean((y - p) ** 2))
    return log_loss, brier


def evaluate_fixed_source_occurrence_validation(
    features: FixedSourceOccurrenceFeatures,
    response: Sequence[float],
    fold_ids: Sequence[str],
    *,
    l2_penalty: float = 1.0,
) -> FixedSourceOccurrenceValidationResult:
    """Evaluate frozen predictors after empirical responses are attached."""

    n = len(features.node_ids)
    y = np.asarray(response, dtype=float)
    if y.shape != (n,):
        raise ValueError("response must align with feature nodes")
    observed = np.isfinite(y)
    if np.any(observed & ~np.isin(y, [0.0, 1.0])):
        raise ValueError("observed responses must be binary 0/1; use NaN for missing")
    folds = np.asarray([str(value) for value in fold_ids], dtype=object)
    if folds.shape != (n,) or any(not value.strip() for value in folds):
        raise ValueError("fold_ids must be non-empty strings aligned with nodes")

    eligible = observed & ~features.source_mask
    if np.sum(eligible) < 4:
        raise ValueError("at least four non-source observed outcomes are required")
    unique_folds = tuple(sorted(set(folds[eligible].tolist())))
    if len(unique_folds) < 2:
        raise ValueError("at least two held-out folds are required")

    predictors: dict[str, np.ndarray] = {
        "viability": features.viability[:, None],
        "viability_dynamic": np.column_stack(
            [features.viability, features.dynamic_reachability]
        ),
    }
    for column, name in enumerate(features.reference_names):
        reference = features.reference_values[:, column]
        predictors[f"viability_ref_{name}"] = np.column_stack(
            [features.viability, reference]
        )
        predictors[f"viability_ref_{name}_dynamic"] = np.column_stack(
            [features.viability, reference, features.dynamic_reachability]
        )

    predictions = {
        name: np.full(n, np.nan, dtype=float) for name in predictors
    }
    for fold in unique_folds:
        test = eligible & (folds == fold)
        train = eligible & (folds != fold)
        if not np.any(test):
            continue
        if len(np.unique(y[train])) != 2:
            raise ValueError(f"training fold excluding {fold!r} lacks both classes")
        for name, matrix in predictors.items():
            model = _fit_ridge_logistic(
                matrix[train],
                y[train],
                l2_penalty=float(l2_penalty),
            )
            predictions[name][test] = _predict(model, matrix[test])

    scores: list[OccurrenceModelScore] = []
    score_map: dict[str, float] = {}
    for name in predictors:
        probability = predictions[name][eligible]
        if not np.isfinite(probability).all():
            raise RuntimeError(f"non-estimable held-out predictions for {name}")
        log_loss, brier = _score(y[eligible], probability)
        score_map[name] = log_loss
        scores.append(
            OccurrenceModelScore(
                model_name=name,
                log_loss=log_loss,
                brier=brier,
                n_evaluated=int(np.sum(eligible)),
            )
        )

    increments = tuple(
        (
            name,
            float(
                score_map[f"viability_ref_{name}_dynamic"]
                - score_map[f"viability_ref_{name}"]
            ),
        )
        for name in features.reference_names
    )
    return FixedSourceOccurrenceValidationResult(
        feature_fingerprint=features.feature_fingerprint,
        operator_fingerprint=features.operator_fingerprint,
        fold_ids=unique_folds,
        model_scores=tuple(scores),
        dynamic_increment_over_viability=float(
            score_map["viability_dynamic"] - score_map["viability"]
        ),
        dynamic_increment_over_references=increments,
        n_evaluated=int(np.sum(eligible)),
        n_missing_response=int(np.sum(~observed)),
    )
