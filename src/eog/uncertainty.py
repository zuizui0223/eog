"""Effect sizes and subsampling uncertainty for comparative EOG."""
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
    ambiguous: bool
    n_resamples: int
    resample_fraction: float
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


def compare_geometry(
    group_a: np.ndarray,
    group_b: np.ndarray,
    reference: RobustReference,
    *,
    metric: str = "span",
    support_class: str | None = None,
    n_resamples: int = 500,
    resample_fraction: float = 0.80,
    interval: tuple[float, float] = (0.05, 0.95),
    random_state: int = 0,
) -> ComparativeContrast:
    """Compare groups using one reference and matched within-group subsampling.

    For ``span``, the primary estimate is ``log(span_B / span_A)`` and
    ``span_difference`` retains the difference in reference units. For tree-sensitive
    metrics, groups must share a non-empty predeclared ``support_class``.
    Intervals quantify occurrence-subsampling sensitivity, not ecological replication.
    """
    a, b = _validate_groups(group_a, group_b)
    if metric not in {"span", "continuity", "gap_strength"}:
        raise ValueError("metric must be span, continuity, or gap_strength")
    if metric != "span" and not str(support_class or "").strip():
        raise ValueError("tree-sensitive comparisons require a predeclared support_class")
    if n_resamples < 20:
        raise ValueError("n_resamples must be at least 20")
    if not 0.25 <= resample_fraction <= 1.0:
        raise ValueError("resample_fraction must lie in [0.25, 1]")
    low_q, high_q = interval
    if not 0.0 < low_q < high_q < 1.0:
        raise ValueError("interval quantiles must satisfy 0 < low < high < 1")

    full_a = infer_comparative_geometry(a, reference)
    full_b = infer_comparative_geometry(b, reference)
    value_a = float(getattr(full_a, metric))
    value_b = float(getattr(full_b, metric))
    if metric == "span":
        if value_a <= 0.0 or value_b <= 0.0:
            raise ValueError("span contrasts require positive spans")
        estimate = float(np.log(value_b / value_a))
        span_difference = value_b - value_a
    else:
        estimate = value_b - value_a
        span_difference = None

    rng = np.random.default_rng(random_state)
    size_a = max(4, int(np.floor(len(a) * resample_fraction)))
    size_b = max(4, int(np.floor(len(b) * resample_fraction)))
    draws = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sample_a = a[rng.choice(len(a), size=size_a, replace=False)]
        sample_b = b[rng.choice(len(b), size=size_b, replace=False)]
        geom_a = infer_comparative_geometry(sample_a, reference)
        geom_b = infer_comparative_geometry(sample_b, reference)
        draw_a = float(getattr(geom_a, metric))
        draw_b = float(getattr(geom_b, metric))
        if metric == "span":
            draws[i] = np.log(draw_b / draw_a)
        else:
            draws[i] = draw_b - draw_a

    interval_low, interval_high = np.quantile(draws, [low_q, high_q])
    if estimate > 0:
        direction_stability = float(np.mean(draws > 0))
    elif estimate < 0:
        direction_stability = float(np.mean(draws < 0))
    else:
        direction_stability = float(np.mean(np.isclose(draws, 0.0)))
    ambiguous = bool(interval_low <= 0.0 <= interval_high or direction_stability < 0.90)
    return ComparativeContrast(
        metric=metric,
        estimate=estimate,
        interval_low=float(interval_low),
        interval_high=float(interval_high),
        direction_stability=direction_stability,
        ambiguous=ambiguous,
        n_resamples=int(n_resamples),
        resample_fraction=float(resample_fraction),
        reference_fingerprint=reference_fingerprint(reference),
        support_class=support_class,
        span_difference=float(span_difference) if span_difference is not None else None,
    )
