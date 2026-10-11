"""Outcome-blind, baseline-relative log-loss protection for binary predictions.

This is an optional output policy, not a learner or an empirical promotion gate.
The budget must be fixed before heldout outcomes are inspected.
"""

from __future__ import annotations

import math

import numpy as np


def protect_binary_probabilities(
    baseline: np.ndarray,
    candidate: np.ndarray,
    *,
    max_excess_log_loss: float,
) -> np.ndarray:
    """Project candidate P(Y=1) into a baseline-protecting interval.

    For either outcome, loss(output) - loss(baseline) <= budget in natural
    log units, up to floating-point arithmetic. This also bounds any mean with
    the same nonnegative weights. It does not guarantee improvement, accuracy,
    calibration, AUC, or protection relative to a different baseline.

    Inputs must be aligned nonempty 1-D arrays. Baseline probabilities must be
    strictly inside (0, 1); candidate probabilities may include endpoints.
    Invalid values are rejected, not silently clipped or repaired. No labels,
    fitting, threshold selection, or biological assumptions are involved.
    """
    if isinstance(max_excess_log_loss, (bool, np.bool_)):
        raise TypeError("max_excess_log_loss must be numeric, not bool")
    budget = float(max_excess_log_loss)
    if not math.isfinite(budget) or budget < 0:
        raise ValueError("max_excess_log_loss must be finite and nonnegative")
    base = np.asarray(baseline, dtype=float)
    proposed = np.asarray(candidate, dtype=float)
    if base.ndim != 1 or not base.size or proposed.shape != base.shape:
        raise ValueError("predictions must be aligned nonempty 1-D arrays")
    if not np.all(np.isfinite(base)) or np.any((base <= 0) | (base >= 1)):
        raise ValueError("baseline probabilities must be finite and strictly in (0, 1)")
    if not np.all(np.isfinite(proposed)) or np.any((proposed < 0) | (proposed > 1)):
        raise ValueError("candidate probabilities must be finite and in [0, 1]")
    if budget == 0:
        return base.copy()
    # q >= exp(-b)*p and 1-q >= exp(-b)*(1-p) protect both outcomes.
    lower = math.exp(-budget) * base
    upper = base + (-math.expm1(-budget)) * (1 - base)
    # Round inward and avoid exact 0/1 even at extreme budgets/probabilities.
    lower = np.nextafter(lower, base)
    upper = np.nextafter(upper, base)
    return np.clip(proposed, lower, upper)
