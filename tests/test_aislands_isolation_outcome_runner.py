from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from benchmarks.run_aislands_isolation_adequacy import (
    EXPECTED,
    bootstrap_interval,
    build_prepared,
    component_labels,
    find_unique_sha,
    fit_probabilities,
    load_climate,
    load_cohort,
    load_folds,
    reduce_constant_columns,
    sign_flip_p,
)


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_repository_inputs_resolve_uniquely_and_load_without_outcome_scoring() -> None:
    fold_path = find_unique_sha(ROOT, EXPECTED["folds"])
    climate_path = find_unique_sha(ROOT, EXPECTED["climate"])
    cohort_path = find_unique_sha(ROOT, EXPECTED["cohort"])

    folds = load_folds(fold_path)
    climate = load_climate(climate_path)
    cohort = load_cohort(cohort_path)

    assert len(folds) == 842
    assert len(climate) == 842
    assert len(set(folds.values())) == 5
    assert set(folds) == set(climate)
    assert len(cohort) == 886
    assert len(set(cohort)) == 886


def test_existing_authoritative_l2_engine_can_score_synthetic_heldout_rows() -> None:
    x_train = np.asarray(
        [
            [-2.0, -1.0],
            [-1.5, -0.5],
            [-1.0, -1.5],
            [-0.5, -0.8],
            [-0.2, -0.1],
            [0.2, 0.1],
            [0.5, 0.8],
            [1.0, 1.5],
            [1.5, 0.5],
            [2.0, 1.0],
        ],
        dtype=float,
    )
    y_train = np.asarray([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=int)
    x_test = np.asarray([[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]], dtype=float)

    probabilities = fit_probabilities(x_train, y_train, x_test)

    assert probabilities.shape == (3,)
    assert np.isfinite(probabilities).all()
    assert np.all((probabilities > 0.0) & (probabilities < 1.0))
    assert probabilities[0] < probabilities[-1]


def test_constant_predictor_reduction_is_training_only_and_index_stable() -> None:
    x_train = np.asarray(
        [
            [0.0, 1.0, 5.0],
            [1.0, 1.0, 6.0],
            [2.0, 1.0, 7.0],
        ]
    )
    x_test = np.asarray([[100.0, 9.0, 8.0]])
    train_reduced, test_reduced, kept, dropped = reduce_constant_columns(
        x_train,
        x_test,
        ["var_a", "constant_in_train", "var_b"],
    )
    assert kept == ["var_a", "var_b"]
    assert dropped == ["constant_in_train"]
    assert train_reduced.shape == (3, 2)
    assert test_reduced.tolist() == [[100.0, 8.0]]


def test_geography_graph_components_follow_radius_only() -> None:
    distance = np.asarray(
        [
            [0.0, 10.0, 100.0, 120.0],
            [10.0, 0.0, 90.0, 110.0],
            [100.0, 90.0, 0.0, 10.0],
            [120.0, 110.0, 10.0, 0.0],
        ]
    )
    labels_25 = component_labels(distance, 25.0)
    labels_125 = component_labels(distance, 125.0)
    assert labels_25[0] == labels_25[1]
    assert labels_25[2] == labels_25[3]
    assert labels_25[0] != labels_25[2]
    assert len(set(labels_125.tolist())) == 1


def test_prepared_graph_has_exact_frozen_geography_scenarios() -> None:
    coords = np.asarray(
        [
            [150.0, -30.0],
            [150.1, -30.0],
            [151.0, -30.0],
        ],
        dtype=float,
    )
    prepared = build_prepared(["1", "2", "3"], coords)
    assert prepared.scenario_ids == (
        "g25_env_none",
        "g50_env_none",
        "g125_env_none",
        "g250_env_none",
    )
    assert prepared.geographic_distance_km.shape == (3, 3)
    assert len(prepared.component_labels) == 4


def test_species_macro_inference_helpers_are_deterministic() -> None:
    values = np.asarray([-0.10, -0.05, 0.01, -0.02, -0.04])
    ci_a = bootstrap_interval(values, reps=2000, seed=20260812)
    ci_b = bootstrap_interval(values, reps=2000, seed=20260812)
    p_a = sign_flip_p(values, reps=4000, seed=20260812)
    p_b = sign_flip_p(values, reps=4000, seed=20260812)
    assert ci_a == ci_b
    assert p_a == p_b
    assert ci_a[0] <= float(np.mean(values)) <= ci_a[1]
    assert 0.0 < p_a <= 1.0


def test_sha_resolver_refuses_missing_identity() -> None:
    with pytest.raises(RuntimeError, match="expected one repository file"):
        find_unique_sha(ROOT, "0" * 64)
