"""Outcome-evaluation statistic for structural reachability beyond support and distance.

Strata are formed from held-out covariates only. Species labels are consulted only after
support and distance bins have been fixed, so the statistic does not tune reachability
from the outcome it evaluates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ConditionalConcordance:
    concordance: float | None
    comparable_pairs: int
    informative_strata: int
    total_strata: int
    support_bins: int
    distance_bins: int


def _rank_bins(values: np.ndarray, n_bins: int) -> np.ndarray:
    """Assign equal values to the same deterministic empirical-quantile bin."""
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("binning values must be a finite one-dimensional vector")
    if n_bins < 2:
        raise ValueError("n_bins must be at least two")
    n = len(values)
    if n < 2:
        raise ValueError("at least two values are required for binning")

    order = np.argsort(values, kind="mergesort")
    bins = np.empty(n, dtype=int)
    start = 0
    while start < n:
        end = start + 1
        while end < n and values[order[end]] == values[order[start]]:
            end += 1
        # Mid-rank percentile keeps exact ties together.
        midpoint = ((start + end - 1) / 2.0) / max(n - 1, 1)
        bin_id = min(n_bins - 1, int(np.floor(midpoint * n_bins)))
        bins[order[start:end]] = bin_id
        start = end
    return bins


def conditional_reachability_concordance(
    labels: Sequence[int | bool],
    pointwise_support: Sequence[float],
    nearest_anchor_distance_km: Sequence[float],
    structural_reachability: Sequence[float],
    *,
    support_bins: int = 5,
    distance_bins: int = 5,
) -> ConditionalConcordance:
    """Compare reachability for presence/absence pairs within support-distance strata.

    Within a held-out species-fold, islands are first stratified into empirical quintiles
    of pointwise support and nearest-anchor distance without using the held-out labels.
    Every presence-absence pair inside the same 2-D stratum contributes 1 if the presence
    has higher structural reachability, 0 if lower, and 0.5 for a tie. The null value is
    therefore 0.5. No threshold is learned from the labels.
    """
    y = np.asarray(labels)
    support = np.asarray(pointwise_support, dtype=float)
    distance = np.asarray(nearest_anchor_distance_km, dtype=float)
    reachability = np.asarray(structural_reachability, dtype=float)
    n = len(y)
    if any(array.ndim != 1 or len(array) != n for array in (support, distance, reachability)):
        raise ValueError("all inputs must be aligned one-dimensional vectors")
    if n < 2:
        raise ValueError("at least two held-out islands are required")
    if not np.all(np.isin(y, (0, 1, False, True))):
        raise ValueError("labels must be binary")
    if not np.isfinite(support).all() or not np.isfinite(distance).all() or not np.isfinite(reachability).all():
        raise ValueError("support, distance and reachability must be finite")

    support_bin = _rank_bins(support, support_bins)
    distance_bin = _rank_bins(distance, distance_bins)
    total_strata = support_bins * distance_bins
    numerator = 0.0
    denominator = 0
    informative = 0

    for s_bin in range(support_bins):
        for d_bin in range(distance_bins):
            mask = (support_bin == s_bin) & (distance_bin == d_bin)
            positive = reachability[mask & (y.astype(int) == 1)]
            negative = reachability[mask & (y.astype(int) == 0)]
            if positive.size == 0 or negative.size == 0:
                continue
            informative += 1
            delta = positive[:, None] - negative[None, :]
            numerator += float(np.sum(delta > 0.0) + 0.5 * np.sum(delta == 0.0))
            denominator += int(delta.size)

    return ConditionalConcordance(
        concordance=None if denominator == 0 else numerator / denominator,
        comparable_pairs=denominator,
        informative_strata=informative,
        total_strata=total_strata,
        support_bins=support_bins,
        distance_bins=distance_bins,
    )
