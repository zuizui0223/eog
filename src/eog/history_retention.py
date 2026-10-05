"""Target-specific history-retention statistics for EOG empirical benchmarks.

The core estimand is the fraction of target variation explained by a declared history
factor after a nuisance/time factor.  This module deliberately contains no dataset
adapter and no ecological interpretation.  Inference is randomized only at the declared
experimental-unit level.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class HistoryRetentionResult:
    """Auditable partial-R2 decomposition for one declared target."""

    partial_r2: float
    history_ss: float
    reduced_residual_ss: float
    full_residual_ss: float
    n_rows: int
    history_levels: int


@dataclass(frozen=True)
class PermutationResult:
    """Plot-level randomization diagnostic for a frozen retention statistic."""

    observed_partial_r2: float
    p_value: float
    permutations: int
    seed: int


def _array(values: Sequence[object], *, name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size < 2:
        raise ValueError(f"{name} must contain at least two rows")
    return array


def _numeric(values: Sequence[float], *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size < 2:
        raise ValueError(f"{name} must contain at least two rows")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _levels(values: np.ndarray) -> tuple[object, ...]:
    return tuple(sorted(set(values.tolist()), key=lambda value: str(value)))


def _dummy_matrix(values: np.ndarray, *, name: str) -> np.ndarray:
    levels = _levels(values)
    if not levels:
        raise ValueError(f"{name} has no levels")
    if len(levels) == 1:
        return np.empty((values.size, 0), dtype=float)
    return np.column_stack(
        [(values == level).astype(float) for level in levels[1:]]
    )


def _design_matrix(
    nuisance: np.ndarray,
    history: np.ndarray | None = None,
) -> np.ndarray:
    columns: list[np.ndarray] = [np.ones(nuisance.size, dtype=float)]
    nuisance_dummy = _dummy_matrix(nuisance, name="nuisance")
    columns.extend(
        nuisance_dummy[:, index]
        for index in range(nuisance_dummy.shape[1])
    )
    if history is not None:
        history_dummy = _dummy_matrix(history, name="history")
        columns.extend(
            history_dummy[:, index]
            for index in range(history_dummy.shape[1])
        )
    return np.column_stack(columns)


def _validate_factors(
    history: Sequence[object],
    nuisance: Sequence[object],
    *,
    n_rows: int,
) -> tuple[np.ndarray, np.ndarray]:
    history_array = _array(history, name="history")
    nuisance_array = _array(nuisance, name="nuisance")
    if history_array.size != n_rows or nuisance_array.size != n_rows:
        raise ValueError("history, nuisance, and target must have the same row count")
    if len(_levels(history_array)) < 2:
        raise ValueError("history must contain at least two levels")
    return history_array, nuisance_array


def _nested_partial_r2_from_sse(
    reduced_sse: float,
    full_sse: float,
    *,
    n_rows: int,
    history_levels: int,
) -> HistoryRetentionResult:
    tolerance = 1e-12
    if reduced_sse < -tolerance or full_sse < -tolerance:
        raise ValueError("residual sums of squares must not be negative")
    reduced_sse = max(0.0, float(reduced_sse))
    full_sse = max(0.0, float(full_sse))
    history_ss = reduced_sse - full_sse
    if history_ss < -1e-9:
        raise ValueError("full model cannot fit worse than nested reduced model")
    history_ss = max(0.0, history_ss)
    partial = 0.0 if reduced_sse <= tolerance else history_ss / reduced_sse
    partial = min(1.0, max(0.0, float(partial)))
    return HistoryRetentionResult(
        partial_r2=partial,
        history_ss=history_ss,
        reduced_residual_ss=reduced_sse,
        full_residual_ss=full_sse,
        n_rows=int(n_rows),
        history_levels=int(history_levels),
    )


def partial_r2_scalar(
    target: Sequence[float],
    history: Sequence[object],
    nuisance: Sequence[object],
) -> HistoryRetentionResult:
    """Return partial R2 of history after nuisance for a scalar target.

    The statistic is the incremental reduction in SSE divided by the reduced-model SSE:
    (SSE_reduced - SSE_full) / SSE_reduced.
    """

    y = _numeric(target, name="target")
    h, z = _validate_factors(history, nuisance, n_rows=y.size)
    reduced = _design_matrix(z)
    full = _design_matrix(z, h)
    beta_reduced = np.linalg.lstsq(reduced, y, rcond=None)[0]
    beta_full = np.linalg.lstsq(full, y, rcond=None)[0]
    reduced_sse = float(np.sum((y - reduced @ beta_reduced) ** 2))
    full_sse = float(np.sum((y - full @ beta_full) ** 2))
    return _nested_partial_r2_from_sse(
        reduced_sse,
        full_sse,
        n_rows=y.size,
        history_levels=len(_levels(h)),
    )


def _projection(design: np.ndarray) -> np.ndarray:
    return design @ np.linalg.pinv(design)


def partial_r2_distance(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    nuisance: Sequence[object],
) -> HistoryRetentionResult:
    """Return distance-based partial R2 of history after nuisance.

    The distance matrix is Gower-centered.  The numerator is
    tr[(H_full - H_reduced) G] and the denominator is the residual sum of squares
    after the nuisance-only model, tr[(I - H_reduced) G].

    This is the nested-model quantity used for the v27 multivariate retention
    estimand.  Statistical significance, when requested, must use the experimental-unit
    permutation contract rather than row shuffling.
    """

    d = np.asarray(distance, dtype=float)
    if d.ndim != 2 or d.shape[0] != d.shape[1] or d.shape[0] < 2:
        raise ValueError("distance must be a square matrix with at least two rows")
    if not np.all(np.isfinite(d)):
        raise ValueError("distance must contain only finite values")
    if np.any(d < -1e-12):
        raise ValueError("distance cannot contain negative values")
    if not np.allclose(d, d.T, atol=1e-10, rtol=0.0):
        raise ValueError("distance must be symmetric")
    if not np.allclose(np.diag(d), 0.0, atol=1e-10, rtol=0.0):
        raise ValueError("distance diagonal must be zero")

    h, z = _validate_factors(history, nuisance, n_rows=d.shape[0])
    n = d.shape[0]
    centering = np.eye(n) - np.ones((n, n), dtype=float) / n
    gower = -0.5 * centering @ (d ** 2) @ centering

    reduced = _design_matrix(z)
    full = _design_matrix(z, h)
    h_reduced = _projection(reduced)
    h_full = _projection(full)
    identity = np.eye(n)

    reduced_residual_ss = float(np.trace((identity - h_reduced) @ gower))
    history_ss = float(np.trace((h_full - h_reduced) @ gower))
    full_residual_ss = reduced_residual_ss - history_ss

    tolerance = 1e-9
    if reduced_residual_ss < -tolerance:
        raise ValueError("distance geometry yields negative reduced residual SS")
    if history_ss < -tolerance:
        raise ValueError("distance geometry yields negative history SS")
    if full_residual_ss < -tolerance:
        raise ValueError("distance geometry yields negative full residual SS")

    return _nested_partial_r2_from_sse(
        max(0.0, reduced_residual_ss),
        max(0.0, full_residual_ss),
        n_rows=n,
        history_levels=len(_levels(h)),
    )


def _plot_history(
    history: np.ndarray,
    plot_ids: np.ndarray,
) -> tuple[tuple[object, ...], np.ndarray]:
    if plot_ids.size != history.size:
        raise ValueError("plot_ids and history must have the same row count")
    plots = _levels(plot_ids)
    plot_history: list[object] = []
    for plot in plots:
        values = _levels(history[plot_ids == plot])
        if len(values) != 1:
            raise ValueError("each plot must have exactly one history label")
        plot_history.append(values[0])
    return plots, np.asarray(plot_history, dtype=object)


def _permuted_history(
    history: np.ndarray,
    plot_ids: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    plots, labels = _plot_history(history, plot_ids)
    shuffled = labels.copy()
    rng.shuffle(shuffled)
    mapping = dict(zip(plots, shuffled.tolist(), strict=True))
    return np.asarray([mapping[plot] for plot in plot_ids], dtype=object)


def permutation_partial_r2_scalar(
    target: Sequence[float],
    history: Sequence[object],
    nuisance: Sequence[object],
    plot_ids: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Randomization diagnostic that permutes history among whole plots only."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    y = _numeric(target, name="target")
    h, z = _validate_factors(history, nuisance, n_rows=y.size)
    plots = _array(plot_ids, name="plot_ids")
    _plot_history(h, plots)
    observed = partial_r2_scalar(y, h, z).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_history(h, plots, rng)
        statistic = partial_r2_scalar(y, permuted, z).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
    )


def permutation_partial_r2_distance(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    nuisance: Sequence[object],
    plot_ids: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Distance-based randomization diagnostic with whole-plot label permutation."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    d = np.asarray(distance, dtype=float)
    if d.ndim != 2:
        raise ValueError("distance must be two-dimensional")
    h, z = _validate_factors(history, nuisance, n_rows=d.shape[0])
    plots = _array(plot_ids, name="plot_ids")
    _plot_history(h, plots)
    observed = partial_r2_distance(d, h, z).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_history(h, plots, rng)
        statistic = partial_r2_distance(d, permuted, z).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
    )
