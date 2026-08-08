import numpy as np

from eog.local_support import (
    LogisticSupportDeclaration,
    cross_fitted_logistic_support,
    deterministic_stratified_folds,
    fit_l2_logistic,
)


def test_stratified_folds_are_deterministic_and_balanced():
    ids = [f"I{i:02d}" for i in range(20)]
    labels = [0] * 10 + [1] * 10
    folds = deterministic_stratified_folds(labels, ids, n_splits=10)
    assert sorted(folds[:10].tolist()) == list(range(10))
    assert sorted(folds[10:].tolist()) == list(range(10))
    assert np.array_equal(folds, deterministic_stratified_folds(labels, ids, n_splits=10))


def test_cross_fit_is_order_invariant_by_unit_id():
    ids = np.array([f"I{i:02d}" for i in range(20)])
    x = np.column_stack((np.linspace(-2, 2, 20), np.linspace(2, -2, 20)))
    y = np.array([0] * 10 + [1] * 10)
    declaration = LogisticSupportDeclaration(n_splits=10)
    first = cross_fitted_logistic_support(x, y, ids, declaration)

    order = np.array([7, 1, 15, 4, 19, 0, 12, 9, 2, 17, 6, 10, 3, 18, 5, 11, 8, 14, 13, 16])
    second = cross_fitted_logistic_support(x[order], y[order], ids[order], declaration)
    second_by_id = {unit_id: p for unit_id, p in zip(ids[order], second.probabilities)}
    first_by_id = {unit_id: p for unit_id, p in zip(ids, first.probabilities)}
    for unit_id in ids:
        assert np.isclose(first_by_id[unit_id], second_by_id[unit_id])


def test_held_out_predictor_does_not_change_other_fold_predictions():
    ids = np.array([f"I{i:02d}" for i in range(20)])
    x = np.column_stack((np.linspace(-1, 1, 20), np.linspace(0, 3, 20)))
    y = np.array([0] * 10 + [1] * 10)
    declaration = LogisticSupportDeclaration(n_splits=10)
    baseline = cross_fitted_logistic_support(x, y, ids, declaration)

    folds = np.asarray(baseline.fold_ids)
    changed_index = 0
    changed_fold = folds[changed_index]
    x_changed = x.copy()
    x_changed[changed_index] = [1000.0, -1000.0]
    changed = cross_fitted_logistic_support(x_changed, y, ids, declaration)

    same_fold = np.where(folds == changed_fold)[0]
    for index in same_fold:
        if index != changed_index:
            assert np.isclose(baseline.probabilities[index], changed.probabilities[index])


def test_primary_screen_minimum_counts_support_ten_fold_crossfit():
    ids = [f"I{i:02d}" for i in range(20)]
    x = np.column_stack((np.arange(20), np.arange(20) ** 2)).astype(float)
    y = [0] * 10 + [1] * 10
    result = cross_fitted_logistic_support(x, y, ids)
    assert len(result.probabilities) == 20
    assert all(0.0 <= value <= 1.0 for value in result.probabilities)


def test_balanced_class_weight_removes_prevalence_only_intercept():
    x = np.zeros((100, 1), dtype=float)
    y = np.array([0] * 90 + [1] * 10)
    beta = fit_l2_logistic(x, y, class_weight="balanced")
    assert np.isclose(beta[0], 0.0, atol=1e-10)
    assert np.isclose(beta[1], 0.0, atol=1e-10)


def test_declaration_rejects_unfrozen_class_weight():
    try:
        LogisticSupportDeclaration(class_weight="none")
    except ValueError as exc:
        assert "class_weight='balanced'" in str(exc)
    else:
        raise AssertionError("unfrozen class weighting must be rejected")
