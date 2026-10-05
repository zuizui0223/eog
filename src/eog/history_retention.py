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



def _factorial_design_matrices(
    context: np.ndarray,
    history: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return nested reduced/full design matrices for context * history.

    Reduced: 1 + context
    Full:    1 + context + history + context:history

    Reference-cell dummy coding is used only to construct the column spaces; the
    retention statistic depends on the nested projection spaces, not coefficient
    parameterization.
    """

    context_dummy = _dummy_matrix(context, name="context")
    history_dummy = _dummy_matrix(history, name="history")
    reduced_columns: list[np.ndarray] = [np.ones(context.size, dtype=float)]
    reduced_columns.extend(
        context_dummy[:, index] for index in range(context_dummy.shape[1])
    )
    reduced = np.column_stack(reduced_columns)

    full_columns = list(reduced_columns)
    full_columns.extend(
        history_dummy[:, index] for index in range(history_dummy.shape[1])
    )
    for context_index in range(context_dummy.shape[1]):
        for history_index in range(history_dummy.shape[1]):
            full_columns.append(
                context_dummy[:, context_index] * history_dummy[:, history_index]
            )
    full = np.column_stack(full_columns)

    reduced_rank = int(np.linalg.matrix_rank(reduced))
    full_rank = int(np.linalg.matrix_rank(full))
    if full_rank <= reduced_rank:
        raise ValueError(
            "history increment is not identifiable beyond the context-only model"
        )
    return reduced, full


def partial_r2_scalar_factorial(
    target: Sequence[float],
    history: Sequence[object],
    context: Sequence[object],
) -> HistoryRetentionResult:
    """Return context-aware history retention for a scalar target.

    The reduced model is 1 + context and the full model is
    1 + context + history + context:history.
    """

    y = _numeric(target, name="target")
    h, c = _validate_factors(history, context, n_rows=y.size)
    reduced, full = _factorial_design_matrices(c, h)
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


def partial_r2_distance_factorial(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    context: Sequence[object],
) -> HistoryRetentionResult:
    """Return context-aware history retention for a distance target."""

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

    h, c = _validate_factors(history, context, n_rows=d.shape[0])
    reduced, full = _factorial_design_matrices(c, h)

    n = d.shape[0]
    centering = np.eye(n) - np.ones((n, n), dtype=float) / n
    gower = -0.5 * centering @ (d ** 2) @ centering
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


def _permuted_within_strata(
    history: np.ndarray,
    strata: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    if history.size != strata.size:
        raise ValueError("history and strata must have the same row count")
    permuted = history.copy()
    for level in _levels(strata):
        indexes = np.flatnonzero(strata == level)
        values = permuted[indexes].copy()
        rng.shuffle(values)
        permuted[indexes] = values
    return permuted


def permutation_partial_r2_scalar_factorial(
    target: Sequence[float],
    history: Sequence[object],
    context: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Permute history within context strata for a scalar factorial target."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    y = _numeric(target, name="target")
    h, c = _validate_factors(history, context, n_rows=y.size)
    observed = partial_r2_scalar_factorial(y, h, c).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_within_strata(h, c, rng)
        statistic = partial_r2_scalar_factorial(y, permuted, c).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
    )


def permutation_partial_r2_distance_factorial(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    context: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Permute history within context strata for a distance factorial target."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    d = np.asarray(distance, dtype=float)
    if d.ndim != 2:
        raise ValueError("distance must be two-dimensional")
    h, c = _validate_factors(history, context, n_rows=d.shape[0])
    observed = partial_r2_distance_factorial(d, h, c).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_within_strata(h, c, rng)
        statistic = partial_r2_distance_factorial(d, permuted, c).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
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


def factorial_history_design(
    context: Sequence[object],
    history: Sequence[object],
) -> tuple[np.ndarray, np.ndarray]:
    """Build nested reduced/full designs for context-dependent history retention.

    Reduced: 1 + context.
    Full:    1 + context + history + context:history.

    Treatment/reference coding is used only to span the model subspaces.  The retention
    statistic depends on those subspaces, not on the arbitrary reference levels.
    """

    context_array = _array(context, name="context")
    history_array = _array(history, name="history")
    if context_array.size != history_array.size:
        raise ValueError("context and history must have the same row count")
    if len(_levels(history_array)) < 2:
        raise ValueError("history must contain at least two levels")

    c = _dummy_matrix(context_array, name="context")
    h = _dummy_matrix(history_array, name="history")
    intercept = np.ones((context_array.size, 1), dtype=float)
    reduced = np.column_stack([intercept, c])

    columns = [intercept]
    if c.shape[1]:
        columns.append(c)
    if h.shape[1]:
        columns.append(h)
    if c.shape[1] and h.shape[1]:
        interactions = np.column_stack(
            [
                c[:, i] * h[:, j]
                for i in range(c.shape[1])
                for j in range(h.shape[1])
            ]
        )
        columns.append(interactions)
    full = np.column_stack(columns)
    return reduced, full


def _validate_nested_designs(
    reduced: Sequence[Sequence[float]],
    full: Sequence[Sequence[float]],
    *,
    n_rows: int,
) -> tuple[np.ndarray, np.ndarray]:
    reduced_array = np.asarray(reduced, dtype=float)
    full_array = np.asarray(full, dtype=float)
    if reduced_array.ndim != 2 or full_array.ndim != 2:
        raise ValueError("reduced and full designs must be two-dimensional")
    if reduced_array.shape[0] != n_rows or full_array.shape[0] != n_rows:
        raise ValueError("design row counts must match the target")
    if reduced_array.shape[1] < 1 or full_array.shape[1] < 1:
        raise ValueError("designs must contain at least one column")
    if not np.all(np.isfinite(reduced_array)) or not np.all(np.isfinite(full_array)):
        raise ValueError("designs must contain only finite values")

    full_projection = _projection(full_array)
    nesting_error = np.linalg.norm(
        reduced_array - full_projection @ reduced_array,
        ord="fro",
    )
    scale = max(1.0, np.linalg.norm(reduced_array, ord="fro"))
    if nesting_error > 1e-9 * scale:
        raise ValueError("reduced design is not nested in full design")

    reduced_rank = int(np.linalg.matrix_rank(reduced_array))
    full_rank = int(np.linalg.matrix_rank(full_array))
    if full_rank <= reduced_rank:
        raise ValueError("full design adds no identifiable history subspace")
    return reduced_array, full_array


def partial_r2_nested_scalar(
    target: Sequence[float],
    reduced: Sequence[Sequence[float]],
    full: Sequence[Sequence[float]],
    *,
    history_levels: int,
) -> HistoryRetentionResult:
    """Return partial R2 for an arbitrary declared nested scalar model pair."""

    y = _numeric(target, name="target")
    reduced_array, full_array = _validate_nested_designs(
        reduced,
        full,
        n_rows=y.size,
    )
    beta_reduced = np.linalg.lstsq(reduced_array, y, rcond=None)[0]
    beta_full = np.linalg.lstsq(full_array, y, rcond=None)[0]
    reduced_sse = float(np.sum((y - reduced_array @ beta_reduced) ** 2))
    full_sse = float(np.sum((y - full_array @ beta_full) ** 2))
    return _nested_partial_r2_from_sse(
        reduced_sse,
        full_sse,
        n_rows=y.size,
        history_levels=int(history_levels),
    )


def partial_r2_nested_distance(
    distance: Sequence[Sequence[float]],
    reduced: Sequence[Sequence[float]],
    full: Sequence[Sequence[float]],
    *,
    history_levels: int,
) -> HistoryRetentionResult:
    """Return Gower-centered partial R2 for an arbitrary nested design pair."""

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

    reduced_array, full_array = _validate_nested_designs(
        reduced,
        full,
        n_rows=d.shape[0],
    )
    n = d.shape[0]
    centering = np.eye(n) - np.ones((n, n), dtype=float) / n
    gower = -0.5 * centering @ (d ** 2) @ centering
    h_reduced = _projection(reduced_array)
    h_full = _projection(full_array)
    identity = np.eye(n)

    reduced_residual_ss = float(np.trace((identity - h_reduced) @ gower))
    history_ss = float(np.trace((h_full - h_reduced) @ gower))
    full_residual_ss = reduced_residual_ss - history_ss

    tolerance = 1e-8
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
        history_levels=int(history_levels),
    )


def partial_r2_factorial_scalar(
    target: Sequence[float],
    history: Sequence[object],
    context: Sequence[object],
) -> HistoryRetentionResult:
    """History retention from adding history and context×history to context."""

    history_array = _array(history, name="history")
    reduced, full = factorial_history_design(context, history_array)
    return partial_r2_nested_scalar(
        target,
        reduced,
        full,
        history_levels=len(_levels(history_array)),
    )


def partial_r2_factorial_distance(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    context: Sequence[object],
) -> HistoryRetentionResult:
    """Distance analogue of :func:`partial_r2_factorial_scalar`."""

    history_array = _array(history, name="history")
    reduced, full = factorial_history_design(context, history_array)
    return partial_r2_nested_distance(
        distance,
        reduced,
        full,
        history_levels=len(_levels(history_array)),
    )


def _permuted_within_strata(
    history: np.ndarray,
    strata: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    if history.size != strata.size:
        raise ValueError("history and strata must have the same row count")
    result = history.copy()
    for level in _levels(strata):
        index = np.flatnonzero(strata == level)
        values = result[index].copy()
        rng.shuffle(values)
        result[index] = values
    return result


def permutation_factorial_partial_r2_scalar(
    target: Sequence[float],
    history: Sequence[object],
    context: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Permute history within context and refit the context×history model."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    y = _numeric(target, name="target")
    h = _array(history, name="history")
    c = _array(context, name="context")
    if y.size != h.size or y.size != c.size:
        raise ValueError("target, history, and context must have the same row count")
    observed = partial_r2_factorial_scalar(y, h, c).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_within_strata(h, c, rng)
        statistic = partial_r2_factorial_scalar(y, permuted, c).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
    )


def permutation_factorial_partial_r2_distance(
    distance: Sequence[Sequence[float]],
    history: Sequence[object],
    context: Sequence[object],
    *,
    permutations: int = 999,
    seed: int = 20261005,
) -> PermutationResult:
    """Distance retention diagnostic with history shuffled within context."""

    if permutations < 1:
        raise ValueError("permutations must be at least one")
    d = np.asarray(distance, dtype=float)
    if d.ndim != 2 or d.shape[0] != d.shape[1]:
        raise ValueError("distance must be square")
    h = _array(history, name="history")
    c = _array(context, name="context")
    if d.shape[0] != h.size or d.shape[0] != c.size:
        raise ValueError("distance, history, and context must have the same row count")
    observed = partial_r2_factorial_distance(d, h, c).partial_r2
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(permutations):
        permuted = _permuted_within_strata(h, c, rng)
        statistic = partial_r2_factorial_distance(d, permuted, c).partial_r2
        if statistic >= observed - 1e-12:
            exceed += 1
    return PermutationResult(
        observed_partial_r2=observed,
        p_value=(exceed + 1) / (permutations + 1),
        permutations=int(permutations),
        seed=int(seed),
    )
