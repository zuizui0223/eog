from __future__ import annotations

from collections import OrderedDict

import numpy as np
import pytest

from eog.genetic_reference_selection import evaluate_nested_genetic_reference_selection


def _distance_from_positions(values: list[float]) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    return np.abs(x[:, None] - x[None, :])


def _group_distance(groups: list[int]) -> np.ndarray:
    g = np.asarray(groups, dtype=int)
    result = (g[:, None] != g[None, :]).astype(float)
    np.fill_diagonal(result, 0.0)
    return result


def _base_fixture(n: int = 9):
    ids = tuple(f"p{i}" for i in range(n))
    geo = _distance_from_positions([float(i) for i in range(n)])
    barrier = _group_distance([0] * (n // 2) + [1] * (n - n // 2))
    resistance = geo + 4.0 * barrier
    disconnected = np.zeros((n, n), dtype=bool)
    return ids, geo, barrier, resistance, disconnected


def test_geographic_truth_selects_geographic_reference():
    ids, geo, barrier, resistance, disconnected = _base_fixture()
    result = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=geo,
        reference_distances={"resistance": resistance, "geographic": geo},
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )
    assert len(result.folds) == len(ids)
    assert all(fold.selected_reference == "geographic" for fold in result.folds)
    assert dict(result.selection_counts)["geographic"] == len(ids)


def test_resistance_truth_selects_resistance_reference():
    ids, geo, barrier, resistance, disconnected = _base_fixture()
    result = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=resistance,
        reference_distances={"geographic": geo, "resistance": resistance},
        eog_continuous_distance=np.zeros_like(geo),
        eog_disconnected=disconnected,
    )
    assert all(fold.selected_reference == "resistance" for fold in result.folds)


def test_omitted_dynamic_structure_can_add_eog_information():
    ids, geo, barrier, resistance, disconnected = _base_fixture()
    response = 0.15 * geo + 3.0 * barrier
    result = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=response,
        reference_distances={
            "geographic": geo,
            "smooth_graph": geo + 0.25 * resistance,
        },
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )
    assert result.mean_population_delta_mse < 0.0
    assert result.augmented_pooled_mse < result.baseline_pooled_mse


def test_outer_test_response_cannot_change_reference_selected_for_that_fold():
    ids, geo, barrier, resistance, disconnected = _base_fixture()
    response = geo + 0.2 * barrier
    original = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=response,
        reference_distances={"geographic": geo, "resistance": resistance},
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )

    perturbed = response.copy()
    outer = 0
    for other in range(1, len(ids)):
        perturbed[outer, other] += 1000.0 + other
        perturbed[other, outer] = perturbed[outer, other]
    changed = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=perturbed,
        reference_distances={"geographic": geo, "resistance": resistance},
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )

    fold_a = next(fold for fold in original.folds if fold.held_out_population == ids[outer])
    fold_b = next(fold for fold in changed.folds if fold.held_out_population == ids[outer])
    assert fold_a.selected_reference == fold_b.selected_reference
    assert fold_a.inner_scores == fold_b.inner_scores


def test_candidate_order_is_irrelevant_and_fingerprint_is_deterministic():
    ids, geo, barrier, resistance, disconnected = _base_fixture()
    response = geo + 0.1 * barrier
    first = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=response,
        reference_distances=OrderedDict(
            [("resistance", resistance), ("geographic", geo)]
        ),
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )
    second = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=response,
        reference_distances=OrderedDict(
            [("geographic", geo), ("resistance", resistance)]
        ),
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )
    assert first.candidate_ids == ("geographic", "resistance")
    assert first == second
    assert first.fingerprint == second.fingerprint


def test_exact_reference_ties_break_lexicographically():
    ids, geo, barrier, _, disconnected = _base_fixture()
    result = evaluate_nested_genetic_reference_selection(
        ids,
        genetic_distance=geo,
        reference_distances={"zeta": geo.copy(), "alpha": geo.copy()},
        eog_continuous_distance=barrier,
        eog_disconnected=disconnected,
    )
    assert all(fold.selected_reference == "alpha" for fold in result.folds)


def test_invalid_candidate_distance_is_rejected():
    ids, geo, barrier, _, disconnected = _base_fixture()
    invalid = geo.copy()
    invalid[0, 1] += 1.0
    with pytest.raises(ValueError, match="must be symmetric"):
        evaluate_nested_genetic_reference_selection(
            ids,
            genetic_distance=geo,
            reference_distances={"bad": invalid},
            eog_continuous_distance=barrier,
            eog_disconnected=disconnected,
        )


def test_requires_at_least_six_populations():
    ids, geo, barrier, _, disconnected = _base_fixture(n=5)
    with pytest.raises(ValueError, match="at least six"):
        evaluate_nested_genetic_reference_selection(
            ids,
            genetic_distance=geo,
            reference_distances={"geographic": geo},
            eog_continuous_distance=barrier,
            eog_disconnected=disconnected,
        )
