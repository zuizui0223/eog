"""Frozen pointwise support producer used by the A-Islands benchmark.

This module deliberately stays small and deterministic. It produces a fitted
location-indexed support score; it does not perform EOG reachability or choose survey
sites. Hyperparameters are supplied explicitly and are never tuned from held-out EOG
outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class SupportModelError(ValueError):
    """Raised when a declared species-fold support model is not evaluable."""


@dataclass(frozen=True)
class PenalizedLogisticSupportModel:
    predictor_mean: np.ndarray
    predictor_scale: np.ndarray
    coefficients: np.ndarray
    intercept: float
    l2_penalty: float
    converged: bool
    n_iterations: int

    def predict_support(self, predictors: np.ndarray) -> np.ndarray:
        x = _as_2d_float(predictors)
        if x.shape[1] != self.coefficients.size:
            raise SupportModelError(
                f"predictor count {x.shape[1]} != fitted count {self.coefficients.size}"
            )
        if not np.all(np.isfinite(x)):
            raise SupportModelError("prediction predictors contain non-finite values")
        z = (x - self.predictor_mean) / self.predictor_scale
        return _sigmoid(self.intercept + z @ self.coefficients)


def _as_2d_float(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2:
        raise SupportModelError("predictors must be a two-dimensional array")
    if array.shape[0] < 1 or array.shape[1] < 1:
        raise SupportModelError("predictors must contain at least one row and one column")
    return array


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _objective(
    design: np.ndarray,
    response: np.ndarray,
    beta: np.ndarray,
    l2_penalty: float,
) -> float:
    eta = design @ beta
    # Stable logistic negative log-likelihood: log(1 + exp(eta)) - y*eta.
    loss = np.logaddexp(0.0, eta) - response * eta
    penalty = 0.5 * l2_penalty * float(np.dot(beta[1:], beta[1:]))
    return float(np.sum(loss) + penalty)


def fit_penalized_logistic_support(
    predictors: np.ndarray,
    response: np.ndarray,
    *,
    l2_penalty: float = 1.0,
    min_class_count: int = 5,
    max_iterations: int = 200,
    tolerance: float = 1e-9,
) -> PenalizedLogisticSupportModel:
    """Fit a deterministic L2-penalized logistic support model.

    Predictor standardization is learned from the supplied training rows only. The
    intercept is not penalized. A damped Newton update is used so the result does not
    depend on a random seed or an external optimizer version.
    """
    x = _as_2d_float(predictors)
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or y.shape[0] != x.shape[0]:
        raise SupportModelError("response must be one-dimensional and align with predictors")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise SupportModelError("training data contain non-finite values")
    if not np.all(np.isin(y, (0.0, 1.0))):
        raise SupportModelError("response must be binary 0/1")
    if l2_penalty <= 0 or not np.isfinite(l2_penalty):
        raise SupportModelError("l2_penalty must be finite and positive")
    if min_class_count < 1:
        raise SupportModelError("min_class_count must be positive")
    positives = int(np.sum(y == 1.0))
    negatives = int(np.sum(y == 0.0))
    if positives < min_class_count or negatives < min_class_count:
        raise SupportModelError(
            f"insufficient training classes: positives={positives}, negatives={negatives}, "
            f"minimum={min_class_count}"
        )

    mean = np.mean(x, axis=0)
    scale = np.std(x, axis=0, ddof=0)
    if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(scale)):
        raise SupportModelError("non-finite training standardization")
    if np.any(scale <= 0.0):
        indices = np.flatnonzero(scale <= 0.0).tolist()
        raise SupportModelError(f"constant training predictors at columns {indices}")

    z = (x - mean) / scale
    design = np.column_stack([np.ones(x.shape[0], dtype=float), z])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty_diag = np.concatenate([[0.0], np.full(x.shape[1], l2_penalty)])
    current = _objective(design, y, beta, l2_penalty)
    converged = False
    used_iterations = 0

    for iteration in range(1, max_iterations + 1):
        used_iterations = iteration
        probability = _sigmoid(design @ beta)
        weights = probability * (1.0 - probability)
        gradient = design.T @ (probability - y) + penalty_diag * beta
        hessian = design.T @ (design * weights[:, None])
        hessian += np.diag(penalty_diag)
        hessian += np.eye(hessian.shape[0]) * 1e-12
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError as exc:
            raise SupportModelError("penalized logistic Hessian is singular") from exc

        step_scale = 1.0
        accepted = False
        while step_scale >= 2.0 ** -20:
            candidate = beta - step_scale * step
            candidate_objective = _objective(design, y, candidate, l2_penalty)
            if candidate_objective <= current + 1e-12:
                beta = candidate
                accepted = True
                improvement = current - candidate_objective
                current = candidate_objective
                break
            step_scale *= 0.5
        if not accepted:
            raise SupportModelError("Newton update failed to reduce the penalized objective")

        if np.max(np.abs(step_scale * step)) <= tolerance or improvement <= tolerance:
            converged = True
            break

    if not converged:
        raise SupportModelError(f"penalized logistic model did not converge in {max_iterations} iterations")

    return PenalizedLogisticSupportModel(
        predictor_mean=mean.copy(),
        predictor_scale=scale.copy(),
        coefficients=beta[1:].copy(),
        intercept=float(beta[0]),
        l2_penalty=float(l2_penalty),
        converged=True,
        n_iterations=used_iterations,
    )
