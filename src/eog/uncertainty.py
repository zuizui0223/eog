"""Effect sizes and sampling diagnostics for comparative EOG."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np

from .comparative import RobustReference, infer_comparative_geometry


@dataclass(frozen=True)
class ComparativeContrast:
    """Auditable contrast between two groups under one frozen reference."""

    metric: str
    estimate: float
    interval_low: float
    interval_high: float
    direction_stability: float
    permutation_pvalue: float
    direction_supported: bool
    ambiguous: bool
    n_resamples: int
    n_permutations: int
    resample_fraction: float
    matched_resample_size: int
    reference_fingerprint: str
    support_class: str | None
    span_difference: float | None = None


def reference_fingerprint(reference: RobustReference) -> str:
    """Return a stable identity for one serialized robust reference."""
    payload = json.dumps(reference.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_groups(group_a: np.ndarray, group_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(group_a, dtype=float)
    b = np.asarray(group_b, dtype=float)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[1]:
        raise ValueError("groups must be two-dimensional with matching feature dimensions")
    if len(a) < 4 or len(b) < 4:
        raise ValueError("each group must contain at least four rows")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("groups contain non-finite entries")
    return a, b


def _metric_contrast(
    a: np.ndarray,
    b: np.ndarray,
    reference: RobustReference,
    metric: str,
) -> tuple[float, float | None]:
    geom_a = infer_comparative_geometry(a, reference)
    geom_b = infer_comparative_geometry(b, reference)
    value_a = float(getattr(geom_a, metric))
    value_b = float(getattr(geom_b, metric))
    if metric == "span":
        if value_a <= 0.0 or value_b <= 0.0:
            raise ValueError("span contrasts require positive spans")
        return float(np.log(value_b / value_a)), float(value_b - value_a)
    return float(value_b - value_a), None


def compare_geometry(
    group_a: np.ndarray,
    group_b: np.ndarray,
    reference: RobustReference,
    *,
    metric: str = "span",
    support_class: str | None = None,
    n_resamples: int = 500,
    n_permutations: int = 200,
    resample_fraction: float = 0.80,
    interval: tuple[float, float] = (0.05, 0.95),
    random_state: int = 0,
) -> ComparativeContrast:
    """Compare groups in common reference units with matched-size diagnostics.

    Both groups contribute the same number of rows to every draw. This prevents
    unequal sample size from being mistaken for a difference in a pairwise-distance
    quantile. The interval is a conditional occurrence-subsampling sensitivity
    interval, not a confidence interval for ecological replication. The permutation
    diagnostic requires exchangeability under the declared comparison design and is
    reported separately; it is not a posterior probability or causal test.
    """
    a, b = _validate_groups(group_a, group_b)
    if metric not in {"span", "continuity", "gap_strength"}:
        raise ValueError("metric must be span, continuity, or gap_strength")
    if metric != "span" and not str(support_class or "").strip():
        raise ValueError("tree-sensitive comparisons require a predeclared support_class")
    if n_resamples < 20 or n_permutations < 20:
        raise ValueError("n_resamples and n_permutations must each be at least 20")
    if not 0.25 <= resample_fraction <= 1.0:
        raise ValueError("resample_fraction must lie in [0.25, 1]")
    low_q, high_q = interval
    if not 0.0 < low_q < high_q < 1.0:
        raise ValueError("interval quantiles must satisfy 0 < low < high < 1")

    matched_size = max(4, int(np.floor(min(len(a), len(b)) * resample_fraction)))
    rng = np.random.default_rng(random_state)
    draws = np.empty(n_resamples, dtype=float)
    span_differences = np.empty(n_resamples, dtype=float) if metric == "span" else None
    for i in range(n_resamples):
        sample_a = a[rng.choice(len(a), size=matched_size, replace=False)]
        sample_b = b[rng.choice(len(b), size=matched_size, replace=False)]
        draws[i], difference = _metric_contrast(sample_a, sample_b, reference, metric)
        if span_differences is not None:
            span_differences[i] = float(difference)

    estimate = float(np.median(draws))
    interval_low, interval_high = np.quantile(draws, [low_q, high_q])
    if estimate > 0:
        direction_stability = float(np.mean(draws > 0))
    elif estimate < 0:
        direction_stability = float(np.mean(draws < 0))
    else:
        direction_stability = float(np.mean(np.isclose(draws, 0.0)))

    pooled = np.vstack([a, b])
    null_draws = np.empty(n_permutations, dtype=float)
    for i in range(n_permutations):
        selected = rng.choice(len(pooled), size=2 * matched_size, replace=False)
        perm_a = pooled[selected[:matched_size]]
        perm_b = pooled[selected[matched_size:]]
        null_draws[i], _ = _metric_contrast(perm_a, perm_b, reference, metric)
    permutation_pvalue = float(
        (1 + np.sum(np.abs(null_draws) >= abs(estimate))) / (n_permutations + 1)
    )
    direction_supported = bool(direction_stability >= 0.90 and permutation_pvalue < 0.10)
    ambiguous = not direction_supported
    span_difference = (
        float(np.median(span_differences)) if span_differences is not None else None
    )
    return ComparativeContrast(
        metric=metric,
        estimate=estimate,
        interval_low=float(interval_low),
        interval_high=float(interval_high),
        direction_stability=direction_stability,
        permutation_pvalue=permutation_pvalue,
        direction_supported=direction_supported,
        ambiguous=ambiguous,
        n_resamples=int(n_resamples),
        n_permutations=int(n_permutations),
        resample_fraction=float(resample_fraction),
        matched_resample_size=int(matched_size),
        reference_fingerprint=reference_fingerprint(reference),
        support_class=support_class,
        span_difference=span_difference,
    )
