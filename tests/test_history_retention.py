import numpy as np
import pytest

from eog.history_retention import (
    partial_r2_distance,
    partial_r2_scalar,
    permutation_partial_r2_distance,
    permutation_partial_r2_scalar,
    factorial_history_design,
    partial_r2_factorial_distance,
    partial_r2_factorial_scalar,
    partial_r2_nested_scalar,
    permutation_factorial_partial_r2_distance,
    permutation_factorial_partial_r2_scalar,
)


def _balanced_plot_year_panel():
    plot_ids = np.repeat(np.arange(18), 2)
    observation_year = np.tile(np.array([2019, 2020]), 18)
    history = np.repeat(np.repeat(np.array([2014, 2015, 2016]), 6), 2)
    return plot_ids, observation_year, history


def _euclidean_distance(matrix):
    x = np.asarray(matrix, dtype=float)
    delta = x[:, None, :] - x[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def test_scalar_partial_r2_is_zero_when_target_contains_only_nuisance():
    _, year, history = _balanced_plot_year_panel()
    target = (year - 2019).astype(float)
    result = partial_r2_scalar(target, history, year)
    assert result.partial_r2 == pytest.approx(0.0, abs=1e-12)


def test_scalar_partial_r2_recovers_history_signal_after_year():
    _, year, history = _balanced_plot_year_panel()
    target = 5.0 * (history - 2014) + 2.0 * (year - 2019)
    result = partial_r2_scalar(target, history, year)
    assert result.partial_r2 == pytest.approx(1.0, abs=1e-12)
    assert result.history_levels == 3


def test_distance_partial_r2_recovers_history_signal_after_year():
    _, year, history = _balanced_plot_year_panel()
    state = np.column_stack(
        [
            3.0 * (history - 2014) + 0.1 * (year - 2019),
            -1.0 * (history - 2014),
        ]
    )
    distance = _euclidean_distance(state)
    result = partial_r2_distance(distance, history, year)
    assert result.partial_r2 == pytest.approx(1.0, abs=1e-12)


def test_plot_permutation_diagnostic_is_deterministic_and_plot_blocked():
    plot_ids, year, history = _balanced_plot_year_panel()
    target = 5.0 * (history - 2014) + 0.25 * (year - 2019)
    a = permutation_partial_r2_scalar(
        target,
        history,
        year,
        plot_ids,
        permutations=199,
        seed=17,
    )
    b = permutation_partial_r2_scalar(
        target,
        history,
        year,
        plot_ids,
        permutations=199,
        seed=17,
    )
    assert a == b
    assert a.observed_partial_r2 == pytest.approx(1.0, abs=1e-12)
    assert a.p_value <= 0.05


def test_distance_plot_permutation_detects_strong_history_structure():
    plot_ids, year, history = _balanced_plot_year_panel()
    state = np.column_stack(
        [
            4.0 * (history - 2014) + 0.05 * (year - 2019),
            2.0 * (history - 2014),
        ]
    )
    distance = _euclidean_distance(state)
    result = permutation_partial_r2_distance(
        distance,
        history,
        year,
        plot_ids,
        permutations=199,
        seed=23,
    )
    assert result.observed_partial_r2 > 0.99
    assert result.p_value <= 0.05


def test_plot_permutation_rejects_inconsistent_history_within_plot():
    plot_ids, year, history = _balanced_plot_year_panel()
    broken = history.copy()
    broken[1] = 2015
    target = 2.0 * (history - 2014) + (year - 2019)
    with pytest.raises(ValueError, match="exactly one history label"):
        permutation_partial_r2_scalar(
            target,
            broken,
            year,
            plot_ids,
            permutations=9,
        )


def test_distance_validation_rejects_asymmetry():
    _, year, history = _balanced_plot_year_panel()
    distance = np.zeros((36, 36), dtype=float)
    distance[0, 1] = 1.0
    with pytest.raises(ValueError, match="symmetric"):
        partial_r2_distance(distance, history, year)



def _factorial_panel():
    context = np.repeat(np.array(["A", "B", "C"]), 20)
    history = np.tile(np.repeat(np.array(["h1", "h2", "h3", "h4"]), 5), 3)
    return context, history


def test_factorial_design_is_nested_and_adds_history_subspace():
    context, history = _factorial_panel()
    reduced, full = factorial_history_design(context, history)
    assert np.linalg.matrix_rank(full) > np.linalg.matrix_rank(reduced)
    projection = full @ np.linalg.pinv(full)
    assert np.linalg.norm(reduced - projection @ reduced) < 1e-10


def test_factorial_scalar_retention_recovers_context_specific_history():
    context, history = _factorial_panel()
    c = np.array([{"A": 0.0, "B": 2.0, "C": -1.0}[x] for x in context])
    h = np.array([{"h1": 0.0, "h2": 1.0, "h3": 2.0, "h4": 3.0}[x] for x in history])
    interaction = np.array([
        (2.0 if cx == "B" else -0.5 if cx == "C" else 1.0) * hx
        for cx, hx in zip(context, h)
    ])
    target = c + interaction
    result = partial_r2_factorial_scalar(target, history, context)
    assert result.partial_r2 == pytest.approx(1.0, abs=1e-12)


def test_factorial_distance_retention_recovers_history_geometry():
    context, history = _factorial_panel()
    h = np.array([{"h1": 0.0, "h2": 1.0, "h3": 2.0, "h4": 3.0}[x] for x in history])
    c = np.array([{"A": 0.0, "B": 1.0, "C": 2.0}[x] for x in context])
    state = np.column_stack([h * (1 + c), h - c])
    distance = _euclidean_distance(state)
    result = partial_r2_factorial_distance(distance, history, context)
    assert result.partial_r2 == pytest.approx(1.0, abs=1e-12)


def test_factorial_permutation_is_deterministic_within_context():
    context, history = _factorial_panel()
    h = np.array([{"h1": 0.0, "h2": 1.0, "h3": 2.0, "h4": 3.0}[x] for x in history])
    target = h * np.array([1.0 if x == "A" else 2.0 if x == "B" else 3.0 for x in context])
    a = permutation_factorial_partial_r2_scalar(
        target, history, context, permutations=199, seed=41
    )
    b = permutation_factorial_partial_r2_scalar(
        target, history, context, permutations=199, seed=41
    )
    assert a == b
    assert a.observed_partial_r2 > 0.99
    assert a.p_value <= 0.05


def test_factorial_distance_permutation_detects_history_signal():
    context, history = _factorial_panel()
    h = np.array([{"h1": 0.0, "h2": 1.0, "h3": 2.0, "h4": 3.0}[x] for x in history])
    state = np.column_stack([h, h * (np.arange(h.size) % 3 + 1)])
    distance = _euclidean_distance(state)
    result = permutation_factorial_partial_r2_distance(
        distance, history, context, permutations=199, seed=43
    )
    assert result.observed_partial_r2 > 0.5
    assert result.p_value <= 0.05


def test_nested_scalar_rejects_non_nested_designs():
    y = np.arange(8, dtype=float)
    reduced = np.column_stack([np.ones(8), np.arange(8)])
    full = np.column_stack([np.ones(8), np.arange(8) % 2])
    with pytest.raises(ValueError, match="not nested"):
        partial_r2_nested_scalar(y, reduced, full, history_levels=2)
