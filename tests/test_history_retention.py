import numpy as np
import pytest

from eog.history_retention import (
    partial_r2_distance,
    partial_r2_scalar,
    permutation_partial_r2_distance,
    permutation_partial_r2_scalar,
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
