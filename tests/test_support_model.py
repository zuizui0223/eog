import numpy as np
import pytest

from eog.support_model import SupportModelError, fit_penalized_logistic_support


def test_penalized_logistic_is_deterministic_and_ranks_signal():
    x = np.array([
        [-2.0, 0.0],
        [-1.5, 0.5],
        [-1.0, -0.5],
        [-0.5, 0.2],
        [0.0, -0.2],
        [0.5, 0.1],
        [1.0, -0.4],
        [1.5, 0.3],
        [2.0, -0.1],
        [2.5, 0.4],
        [3.0, -0.3],
        [3.5, 0.2],
    ])
    y = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], dtype=float)
    first = fit_penalized_logistic_support(x, y, min_class_count=5)
    second = fit_penalized_logistic_support(x, y, min_class_count=5)
    assert np.allclose(first.coefficients, second.coefficients)
    assert first.intercept == pytest.approx(second.intercept)
    support = first.predict_support(x)
    assert support[-1] > support[0]
    assert np.all((support >= 0.0) & (support <= 1.0))


def test_immediate_prediction_path_is_identical_to_historical_fit_then_predict():
    x = np.array([
        [-2.0, 0.0],
        [-1.5, 0.5],
        [-1.0, -0.5],
        [-0.5, 0.2],
        [0.0, -0.2],
        [0.5, 0.1],
        [1.0, -0.4],
        [1.5, 0.3],
        [2.0, -0.1],
        [2.5, 0.4],
        [3.0, -0.3],
        [3.5, 0.2],
    ])
    y = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], dtype=float)
    target = np.array([[-1.25, 0.1], [0.75, -0.1], [2.75, 0.0]])
    model = fit_penalized_logistic_support(x, y, min_class_count=5)
    historical = model.predict_support(target)
    immediate = fit_penalized_logistic_support(x, y, target, min_class_count=5)
    assert np.array_equal(immediate, historical)


def test_standardization_is_training_only_and_reused_for_prediction():
    x = np.array([
        [0.0, 10.0], [1.0, 11.0], [2.0, 12.0], [3.0, 13.0], [4.0, 14.0],
        [5.0, 15.0], [6.0, 16.0], [7.0, 17.0], [8.0, 18.0], [9.0, 19.0],
    ])
    y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=float)
    model = fit_penalized_logistic_support(x, y, min_class_count=5)
    assert np.allclose(model.predictor_mean, np.mean(x, axis=0))
    assert np.allclose(model.predictor_scale, np.std(x, axis=0, ddof=0))
    prediction = model.predict_support(np.array([[100.0, 110.0]]))
    assert prediction.shape == (1,)


def test_insufficient_training_class_is_explicit_failure():
    x = np.arange(20, dtype=float).reshape(10, 2)
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=float)
    with pytest.raises(SupportModelError, match="insufficient training classes"):
        fit_penalized_logistic_support(x, y, min_class_count=5)


def test_constant_predictor_is_not_silently_dropped():
    x = np.column_stack([np.arange(12, dtype=float), np.ones(12)])
    y = np.array([0] * 6 + [1] * 6, dtype=float)
    with pytest.raises(SupportModelError, match="constant training predictors"):
        fit_penalized_logistic_support(x, y, min_class_count=5)


def test_nonfinite_prediction_is_explicit_failure():
    x = np.column_stack([np.arange(12, dtype=float), np.arange(12, dtype=float) ** 2])
    y = np.array([0] * 6 + [1] * 6, dtype=float)
    model = fit_penalized_logistic_support(x, y, min_class_count=5)
    with pytest.raises(SupportModelError, match="non-finite"):
        model.predict_support(np.array([[np.nan, 1.0]]))
