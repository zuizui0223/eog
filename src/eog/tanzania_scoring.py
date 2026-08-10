"""Leakage-safe scoring primitives for the Tanzania external benchmark.

These functions are intentionally outcome-agnostic utilities.  They implement
the pre-outcome scoring contract using only already-frozen held-out labels and
probabilities.  They do not fit models, choose folds, tune thresholds, or build
EOG graphs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

PROBABILITY_EPSILON = 1e-15


@dataclass(frozen=True)
class PairedScoreSummary:
    n_matched: int
    mean_log_loss_reference: float
    mean_log_loss_candidate: float
    mean_log_loss_difference: float
    mean_brier_reference: float
    mean_brier_candidate: float
    mean_brier_difference: float


def _validated_binary(y: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(y, dtype=float)
    if arr.ndim != 1:
        raise ValueError("y must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError("y contains non-finite values")
    if not np.all(np.isin(arr, [0.0, 1.0])):
        raise ValueError("y must contain only 0/1 values")
    return arr


def _validated_probability(p: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(p, dtype=float)
    if arr.ndim != 1:
        raise ValueError("probabilities must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError("probabilities contain non-finite values")
    if np.any((arr < 0.0) | (arr > 1.0)):
        raise ValueError("probabilities must lie in [0, 1]")
    return arr


def bernoulli_log_loss(
    y: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
    *,
    epsilon: float = PROBABILITY_EPSILON,
) -> np.ndarray:
    """Return per-observation Bernoulli negative log likelihood.

    ``epsilon`` exists only for numerical stability and must be shared by every
    method in a benchmark comparison.
    """
    yy = _validated_binary(y)
    pp = _validated_probability(probability)
    if yy.shape != pp.shape:
        raise ValueError("y and probability must have identical shape")
    if not (0.0 < epsilon < 0.5):
        raise ValueError("epsilon must lie strictly between 0 and 0.5")
    clipped = np.clip(pp, epsilon, 1.0 - epsilon)
    return -(yy * np.log(clipped) + (1.0 - yy) * np.log(1.0 - clipped))


def brier_score(
    y: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return per-observation Brier score."""
    yy = _validated_binary(y)
    pp = _validated_probability(probability)
    if yy.shape != pp.shape:
        raise ValueError("y and probability must have identical shape")
    return np.square(pp - yy)


def paired_score_summary(
    y: Sequence[float] | np.ndarray,
    reference_probability: Sequence[float] | np.ndarray,
    candidate_probability: Sequence[float] | np.ndarray,
    *,
    reference_valid: Sequence[bool] | np.ndarray | None = None,
    candidate_valid: Sequence[bool] | np.ndarray | None = None,
    epsilon: float = PROBABILITY_EPSILON,
) -> PairedScoreSummary:
    """Compare two methods on their exact intersection of valid predictions.

    Differences are ``candidate - reference``; negative values therefore mean
    the candidate has lower (better) held-out loss.
    """
    yy = _validated_binary(y)
    ref = _validated_probability(reference_probability)
    cand = _validated_probability(candidate_probability)
    if not (yy.shape == ref.shape == cand.shape):
        raise ValueError("y/reference/candidate arrays must have identical shape")

    if reference_valid is None:
        ref_valid = np.ones(yy.size, dtype=bool)
    else:
        ref_valid = np.asarray(reference_valid, dtype=bool)
    if candidate_valid is None:
        cand_valid = np.ones(yy.size, dtype=bool)
    else:
        cand_valid = np.asarray(candidate_valid, dtype=bool)
    if ref_valid.shape != yy.shape or cand_valid.shape != yy.shape:
        raise ValueError("valid masks must match y shape")

    matched = ref_valid & cand_valid
    n = int(matched.sum())
    if n == 0:
        raise ValueError("no matched valid held-out predictions")

    y_m = yy[matched]
    ref_m = ref[matched]
    cand_m = cand[matched]
    ref_ll = bernoulli_log_loss(y_m, ref_m, epsilon=epsilon)
    cand_ll = bernoulli_log_loss(y_m, cand_m, epsilon=epsilon)
    ref_br = brier_score(y_m, ref_m)
    cand_br = brier_score(y_m, cand_m)

    return PairedScoreSummary(
        n_matched=n,
        mean_log_loss_reference=float(np.mean(ref_ll)),
        mean_log_loss_candidate=float(np.mean(cand_ll)),
        mean_log_loss_difference=float(np.mean(cand_ll - ref_ll)),
        mean_brier_reference=float(np.mean(ref_br)),
        mean_brier_candidate=float(np.mean(cand_br)),
        mean_brier_difference=float(np.mean(cand_br - ref_br)),
    )


def species_mean_differences(
    species_ids: Iterable[str],
    per_observation_difference: Sequence[float] | np.ndarray,
    valid: Sequence[bool] | np.ndarray | None = None,
) -> dict[str, float]:
    """Aggregate matched score differences at species level."""
    species = np.asarray(list(species_ids), dtype=object)
    diff = np.asarray(per_observation_difference, dtype=float)
    if species.ndim != 1 or diff.ndim != 1 or species.shape != diff.shape:
        raise ValueError("species_ids and differences must be aligned 1-D arrays")
    if not np.all(np.isfinite(diff)):
        raise ValueError("differences contain non-finite values")
    mask = np.ones(diff.size, dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    if mask.shape != diff.shape:
        raise ValueError("valid mask must match differences")
    out: dict[str, float] = {}
    for name in sorted({str(x) for x in species[mask]}):
        selected = mask & (species.astype(str) == name)
        out[name] = float(np.mean(diff[selected]))
    return out
