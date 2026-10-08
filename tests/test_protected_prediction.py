import numpy as np
import pytest

from eog.v2.protected_prediction import protect_binary_probabilities


def test_fitted_stress_preserves_all_regimes_and_bounds_each_replicate():
    from benchmarks.protected_prediction_stress import run_fitted_benchmark

    report = run_fitted_benchmark()
    assert len(report["rows"]) == 12
    assert report["uses_eog_computed_features"] is False
    assert report["uses_biological_response"] is False
    for row in report["rows"]:
        losses = row["log_loss"]
        assert all(np.isfinite(value) for value in losses.values())
        assert losses["protected"] - losses["baseline"] <= 0.01 + 1e-12
    # Do not turn a particular favourable fitted result into a pass requirement.
    assert set(report["regime_mean_deltas"]) == {
        "helpful",
        "neutral",
        "unseen_sign_reversal",
    }


def test_stress_report_retains_some_gain_and_limits_reversal_harm():
    from benchmarks.protected_prediction_stress import run_benchmark

    report = run_benchmark()
    rows = {row["case"]: row for row in report["results"]}
    assert rows["helpful"]["protected_minus_baseline"] < 0
    assert rows["unchanged"]["protected_minus_baseline"] == 0
    assert rows["exactly_wrong"]["candidate_loss_infinite"] is True
    assert rows["confidently_wrong"]["macro_log_loss"]["candidate"] > 6
    for row in rows.values():
        assert row["protected_minus_baseline"] <= report["budget_nats"] + 1e-12


@pytest.mark.parametrize("budget", [0.0, 1e-16, 0.01, 0.1, 1.0, 1000.0])
def test_both_outcomes_are_protected_including_extreme_probabilities(budget):
    rng = np.random.default_rng(90210)
    base = np.r_[rng.uniform(1e-8, 1 - 1e-8, 1000), 1e-300, np.nextafter(1.0, 0.0)]
    for candidate in (np.zeros_like(base), np.ones_like(base), 1 - base, base):
        result = protect_binary_probabilities(
            base, candidate, max_excess_log_loss=budget
        )
        assert np.all((result > 0) & (result < 1))
        assert np.all(np.log(base) - np.log(result) <= budget + 2e-13)
        assert np.all(np.log1p(-base) - np.log1p(-result) <= budget + 2e-13)
        if budget == 0:
            np.testing.assert_array_equal(result, base)


def test_keeps_safe_improvement_and_does_not_mutate_inputs():
    base = np.array([0.5, 0.5])
    candidate = np.array([0.51, 0.49])
    result = protect_binary_probabilities(base, candidate, max_excess_log_loss=0.1)
    np.testing.assert_array_equal(result, candidate)
    np.testing.assert_array_equal(base, [0.5, 0.5])
    np.testing.assert_array_equal(candidate, [0.51, 0.49])
    assert not np.shares_memory(result, candidate)


@pytest.mark.parametrize("budget", [-0.1, float("nan"), float("inf")])
def test_invalid_budget_rejected(budget):
    with pytest.raises(ValueError):
        protect_binary_probabilities([0.5], [0.7], max_excess_log_loss=budget)


def test_boolean_budget_rejected():
    with pytest.raises(TypeError):
        protect_binary_probabilities([0.5], [0.7], max_excess_log_loss=True)


@pytest.mark.parametrize(
    "base,candidate",
    [
        ([], []),
        ([[0.5]], [[0.5]]),
        ([0.5], [0.5, 0.5]),
        ([0.0], [0.5]),
        ([1.0], [0.5]),
        ([float("nan")], [0.5]),
        ([0.5], [-0.1]),
        ([0.5], [1.1]),
        ([0.5], [float("inf")]),
    ],
)
def test_invalid_predictions_rejected(base, candidate):
    with pytest.raises(ValueError):
        protect_binary_probabilities(base, candidate, max_excess_log_loss=0.01)
