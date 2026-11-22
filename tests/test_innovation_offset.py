import numpy as np
import pytest
from scipy.optimize import minimize

from eog.v2.innovation_offset import fit_innovation_offset


def test_matches_independent_optimizer_and_preserves_zero_reference():
    rng = np.random.default_rng(23)
    x = rng.normal(size=(200, 3))
    p = rng.uniform(0.1, 0.9, 200)
    y = rng.integers(0, 2, 200)
    names = ("a", "b", "c")
    model = fit_innovation_offset(p, x, y, feature_names=names, ridge=0.1)
    z = x / np.sqrt(np.mean(x * x, axis=0))
    offset = np.log(p) - np.log1p(-p)

    def objective(beta):
        eta = offset + z @ beta
        return np.mean(np.logaddexp(0, eta) - y * eta) + 0.05 * (beta @ beta)

    oracle = minimize(objective, np.zeros(3), method="BFGS", options={"gtol": 1e-7})
    assert oracle.success
    np.testing.assert_allclose(model.coefficients, oracle.x, atol=2e-6)
    assert model.gradient_max <= 1e-9
    np.testing.assert_array_equal(
        model.predict(p, np.zeros_like(x), feature_names=names), p
    )


def test_zero_state_fits_baseline_exactly_and_scale_is_train_only():
    p = np.array([0.2, 0.8, 0.3, 0.7])
    x = np.zeros((4, 2))
    model = fit_innovation_offset(
        p, x, [0, 1, 0, 1], feature_names=("a", "b"), ridge=0.1
    )
    assert model.coefficients == (0.0, 0.0)
    assert model.scales == (1.0, 1.0)
    np.testing.assert_array_equal(model.predict(p, x, feature_names=("a", "b")), p)
    with pytest.raises(ValueError, match="identity"):
        model.predict(p, x, feature_names=("b", "a"))


def test_column_rescaling_does_not_change_predictions():
    rng = np.random.default_rng(82)
    x = rng.normal(size=(100, 2))
    y = (x[:, 0] > 0).astype(int)
    p = np.full(100, 0.5)
    first = fit_innovation_offset(p, x, y, feature_names=("a", "b"), ridge=0.1)
    scaled = fit_innovation_offset(
        p, x * [10, 0.1], y, feature_names=("a", "b"), ridge=0.1
    )
    np.testing.assert_allclose(
        first.predict(p, x, feature_names=("a", "b")),
        scaled.predict(p, x * [10, 0.1], feature_names=("a", "b")),
        atol=1e-12,
    )


@pytest.mark.parametrize("penalty", [0, -1, np.nan, np.inf])
def test_invalid_ridge_rejected(penalty):
    with pytest.raises(ValueError):
        fit_innovation_offset([0.5], [[1]], [1], feature_names=("a",), ridge=penalty)


@pytest.mark.parametrize(
    "p,x,y,names",
    [
        ([0], [[1]], [1], ("a",)),
        ([np.nan], [[1]], [1], ("a",)),
        ([0.5], [[np.inf]], [1], ("a",)),
        ([0.5], [[1]], [2], ("a",)),
        ([0.5], [[1, 2]], [1], ("a", "a")),
        ([0.5], [[1]], [1], ("",)),
        ([0.5], [[1]], [], ("a",)),
        ([], [], [], ("a",)),
    ],
)
def test_invalid_fit_inputs_rejected(p, x, y, names):
    with pytest.raises(ValueError):
        fit_innovation_offset(p, x, y, feature_names=names, ridge=0.1)


def test_calibration_tie_falls_back_to_baseline():
    from benchmarks.innovation_offset_comparison import choose_on_calibration

    assert not choose_on_calibration([0, 1], [0.2, 0.8], [0.2, 0.8])
    assert choose_on_calibration([0, 1], [0.2, 0.8], [0.1, 0.9])
    assert not choose_on_calibration([0, 1], [0.2, 0.8], [0.9, 0.1])


def test_full_pipeline_reproduces_first_seed_without_score_based_pass_gate(monkeypatch):
    import json
    from pathlib import Path

    from benchmarks import innovation_offset_comparison as benchmark

    monkeypatch.setattr(benchmark, "SEEDS", (701,))
    fresh = benchmark.run_comparison()
    path = (
        Path(__file__).resolve().parents[1]
        / "validation/layer_b_mechanism_v2/innovation_offset_development_result_v1.json"
    )
    recorded = json.loads(path.read_text(encoding="utf-8"))
    assert len(recorded["rows"]) == 16
    assert len(fresh["rows"]) == 4
    for actual in fresh["rows"]:
        expected = next(
            row
            for row in recorded["rows"]
            if row["seed"] == 701 and row["regime"] == actual["regime"]
        )
        assert actual["innovation_fingerprint"] == expected["innovation_fingerprint"]
        assert actual["promoted"] == expected["promoted"]
        assert actual["baseline_log_loss"] == pytest.approx(
            expected["baseline_log_loss"], abs=1e-10
        )
        for name, loss in actual["always_on_log_loss"].items():
            assert loss == pytest.approx(
                expected["always_on_log_loss"][name], abs=1e-10
            )
            selected = actual["selected_log_loss"][name]
            assert selected == (
                loss if actual["promoted"][name] else actual["baseline_log_loss"]
            )
