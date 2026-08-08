"""Frozen local-support producer for held-out incidence benchmarks.

This module deliberately contains no EOG topology or bridge logic.  It produces a
pointwise environmental-support baseline using only declared predictors and training
rows within each fold.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class LogisticSupportDeclaration:
    n_splits: int = 10
    l2_penalty: float = 1.0
    max_iter: int = 100
    tolerance: float = 1e-8

    def __post_init__(self) -> None:
        if self.n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        if not np.isfinite(self.l2_penalty) or self.l2_penalty <= 0:
            raise ValueError("l2_penalty must be finite and positive")
        if self.max_iter < 1:
            raise ValueError("max_iter must be positive")
        if not np.isfinite(self.tolerance) or self.tolerance <= 0:
            raise ValueError("tolerance must be finite and positive")


@dataclass(frozen=True)
class CrossFittedSupport:
    probabilities: tuple[float, ...]
    fold_ids: tuple[int, ...]
    fingerprint: str


def deterministic_stratified_folds(
    labels: Sequence[int],
    unit_ids: Sequence[str],
    n_splits: int = 10,
) -> np.ndarray:
    """Assign deterministic round-robin folds separately within each binary class."""
    y = np.asarray(labels, dtype=int)
    ids = tuple(str(value) for value in unit_ids)
    if y.ndim != 1 or len(y) != len(ids):
        raise ValueError("labels and unit_ids must be one-dimensional and aligned")
    if len(set(ids)) != len(ids):
        raise ValueError("unit_ids must be unique")
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("labels must contain both binary classes 0 and 1")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    counts = np.bincount(y, minlength=2)
    if np.min(counts) < n_splits:
        raise ValueError("each class must have at least n_splits observations")

    folds = np.empty(len(y), dtype=int)
    for label in (0, 1):
        indices = [i for i, value in enumerate(y) if value == label]
        indices.sort(key=lambda i: ids[i])
        for rank, index in enumerate(indices):
            folds[index] = rank % n_splits
    return folds


def _standardize_training_only(
    train_x: np.ndarray,
    test_x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    center = np.mean(train_x, axis=0)
    scale = np.std(train_x, axis=0, ddof=0)
    scale = np.where(scale > 0, scale, 1.0)
    return (train_x - center) / scale, (test_x - center) / scale


def _sigmoid(values: np.ndarray) -> np.ndarray:
    out = np.empty_like(values, dtype=float)
    positive = values >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exp_values = np.exp(values[~positive])
    out[~positive] = exp_values / (1.0 + exp_values)
    return out


def fit_l2_logistic(
    features: np.ndarray,
    labels: np.ndarray,
    *,
    l2_penalty: float = 1.0,
    max_iter: int = 100,
    tolerance: float = 1e-8,
) -> np.ndarray:
    """Fit a binary logistic model by damped Newton updates.

    The intercept is unpenalized; all feature coefficients receive the same frozen L2
    penalty.  The function returns ``[intercept, coefficients...]``.
    """
    x = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=float)
    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("features must be 2D and aligned with 1D labels")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("features and labels must be finite")
    if set(np.unique(y)) != {0.0, 1.0}:
        raise ValueError("training labels must contain both classes")
    if l2_penalty <= 0 or not np.isfinite(l2_penalty):
        raise ValueError("l2_penalty must be finite and positive")

    design = np.column_stack((np.ones(len(x)), x))
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.diag(np.r_[0.0, np.full(x.shape[1], l2_penalty)])

    for _ in range(max_iter):
        probability = _sigmoid(design @ beta)
        gradient = design.T @ (probability - y) + penalty @ beta
        variance = np.clip(probability * (1.0 - probability), 1e-9, None)
        hessian = design.T @ (design * variance[:, None]) + penalty
        step = np.linalg.solve(hessian, gradient)
        beta_next = beta - step
        if np.max(np.abs(beta_next - beta)) < tolerance:
            beta = beta_next
            break
        beta = beta_next
    return beta


def cross_fitted_logistic_support(
    features: Sequence[Sequence[float]],
    labels: Sequence[int],
    unit_ids: Sequence[str],
    declaration: LogisticSupportDeclaration = LogisticSupportDeclaration(),
) -> CrossFittedSupport:
    """Return held-out probabilities from a deterministic stratified cross-fit.

    Predictor scaling and logistic fitting are performed separately inside every
    training fold.  No held-out predictor value contributes to centering, scaling, or
    coefficient estimation.
    """
    x = np.asarray(features, dtype=float)
    y = np.asarray(labels, dtype=int)
    ids = tuple(str(value) for value in unit_ids)
    if x.ndim != 2 or len(x) != len(y) or len(y) != len(ids):
        raise ValueError("features, labels, and unit_ids must align")
    if x.shape[1] < 1 or not np.isfinite(x).all():
        raise ValueError("features must contain at least one finite predictor")

    folds = deterministic_stratified_folds(y, ids, declaration.n_splits)
    probabilities = np.full(len(y), np.nan, dtype=float)
    for fold in range(declaration.n_splits):
        test = folds == fold
        train = ~test
        train_x, test_x = _standardize_training_only(x[train], x[test])
        beta = fit_l2_logistic(
            train_x,
            y[train],
            l2_penalty=declaration.l2_penalty,
            max_iter=declaration.max_iter,
            tolerance=declaration.tolerance,
        )
        design_test = np.column_stack((np.ones(np.sum(test)), test_x))
        probabilities[test] = _sigmoid(design_test @ beta)

    if not np.isfinite(probabilities).all():
        raise RuntimeError("cross-fitting failed to produce finite probabilities")

    payload = {
        "unit_ids": list(ids),
        "labels": y.tolist(),
        "features": x.tolist(),
        "declaration": declaration.__dict__,
        "fold_ids": folds.tolist(),
        "probabilities": probabilities.tolist(),
        "scientific_boundary": "pointwise environmental support only; no EOG structure used",
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return CrossFittedSupport(
        probabilities=tuple(float(value) for value in probabilities),
        fold_ids=tuple(int(value) for value in folds),
        fingerprint=fingerprint,
    )
