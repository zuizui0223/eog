"""Ridge logistic correction with a frozen baseline-logit offset.

Training baseline predictions must be out-of-fold or from a disjoint fit. This
low-level module cannot certify that provenance. It neither creates folds nor
selects a model using heldout outcomes. No intercept: zero innovation is baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _inputs(probabilities, innovation, feature_names):
    p = np.asarray(probabilities, dtype=float)
    x = np.asarray(innovation, dtype=float)
    names = tuple(feature_names)
    if not names or any(not isinstance(n, str) or not n.strip() for n in names):
        raise ValueError("feature_names must contain nonempty strings")
    if len(set(names)) != len(names):
        raise ValueError("feature_names must be unique")
    if p.ndim != 1 or not p.size or x.shape != (p.size, len(names)):
        raise ValueError("probabilities and named innovation columns must be aligned")
    if not np.isfinite(p).all() or np.any((p <= 0) | (p >= 1)):
        raise ValueError("baseline probabilities must be finite and strictly in (0,1)")
    if not np.isfinite(x).all():
        raise ValueError("innovation must be finite")
    return p, x, names


def _sigmoid(eta):
    exp = np.exp(-np.abs(eta))
    return np.where(eta >= 0, 1 / (1 + exp), exp / (1 + exp))


@dataclass(frozen=True)
class InnovationOffsetModel:
    feature_names: tuple[str, ...]
    scales: tuple[float, ...]
    coefficients: tuple[float, ...]
    ridge: float
    gradient_max: float
    iterations: int

    def predict(self, baseline_probabilities, innovation, *, feature_names):
        p, x, names = _inputs(baseline_probabilities, innovation, feature_names)
        if names != self.feature_names:
            raise ValueError("prediction feature identity/order differs from fit")
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            correction = (x / np.asarray(self.scales)) @ np.asarray(self.coefficients)
            result = _sigmoid(np.log(p) - np.log1p(-p) + correction)
        # Preserve baseline bit-for-bit when the correction is exactly zero.
        return np.where(correction == 0, p, result)


def fit_innovation_offset(
    out_of_fold_probabilities,
    innovation,
    response,
    *,
    feature_names,
    ridge: float,
) -> InnovationOffsetModel:
    """Fit mean Bernoulli loss + ridge/2 * ||beta||^2, without an intercept.

    RMS feature scaling is learned only from supplied fit rows, without centering,
    preserving the zero-innovation reference. Ridge must be strictly positive.
    Convex damped Newton optimization fails explicitly if it does not converge.
    This is predictive residual fitting, not causal orthogonalization.
    """
    p, x, names = _inputs(out_of_fold_probabilities, innovation, feature_names)
    if isinstance(ridge, (bool, np.bool_)):
        raise TypeError("ridge must be numeric, not bool")
    penalty = float(ridge)
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("ridge must be finite and positive")
    y = np.asarray(response, dtype=float)
    if y.shape != p.shape or not np.isfinite(y).all() or not np.isin(y, (0, 1)).all():
        raise ValueError("response must be aligned binary outcomes")
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        scales = np.sqrt(np.mean(x * x, axis=0))
        scales = np.where(scales == 0, 1.0, scales)
        z = x / scales
        offset = np.log(p) - np.log1p(-p)
        beta = np.zeros(x.shape[1])

        def objective(value):
            eta = offset + z @ value
            return np.mean(np.logaddexp(0, eta) - y * eta) + penalty / 2 * (
                value @ value
            )

        for iteration in range(101):
            fitted = _sigmoid(offset + z @ beta)
            gradient = z.T @ (fitted - y) / len(y) + penalty * beta
            gradient_max = float(np.max(np.abs(gradient)))
            if gradient_max <= 1e-9:
                return InnovationOffsetModel(
                    names,
                    tuple(scales),
                    tuple(beta),
                    penalty,
                    gradient_max,
                    iteration,
                )
            if iteration == 100:
                break
            hessian = (z.T * (fitted * (1 - fitted))) @ z / len(y)
            hessian += penalty * np.eye(x.shape[1])
            step = np.linalg.solve(hessian, gradient)
            current = objective(beta)
            factor = 1.0
            for _ in range(30):
                proposed = beta - factor * step
                if objective(proposed) <= current - 1e-4 * factor * (gradient @ step):
                    beta = proposed
                    break
                factor *= 0.5
            else:
                raise RuntimeError("innovation offset line search did not converge")
    raise RuntimeError("innovation offset fit did not converge")
