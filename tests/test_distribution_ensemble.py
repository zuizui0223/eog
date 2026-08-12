import numpy as np

from benchmarks.distribution_model_heldout_benchmark import build_replicated_landscape
from eog import BridgeGraphDeclaration, EOGDistributionConfig
from eog.distribution_ensemble import (
    EOGStructuralEnsembleConfig,
    fit_eog_structural_ensemble,
)


def _fit(alpha):
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        target_ids,
        _target_response,
        _sources,
    ) = build_replicated_landscape(6)
    model = fit_eog_structural_ensemble(
        nodes,
        observed_ids,
        response,
        EOGStructuralEnsembleConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
                min_class_count=4,
            ),
            stack_weight=alpha,
        ),
        gate_fold_ids=gate_folds,
    )
    return model, target_ids


def test_structural_ensemble_zero_weight_equals_probability_component():
    model, target_ids = _fit(0.0)
    ensemble = model.predict(target_ids).distribution_support
    probability = model.probability_model.predict(target_ids).distribution_support
    assert np.array_equal(ensemble, probability)


def test_structural_ensemble_unit_weight_equals_stacked_component():
    model, target_ids = _fit(1.0)
    ensemble = model.predict(target_ids).distribution_support
    stacked = model.stacked_model.predict(target_ids).distribution_support
    assert np.array_equal(ensemble, stacked)


def test_structural_ensemble_is_exact_convex_combination():
    alpha = 0.125
    model, target_ids = _fit(alpha)
    ensemble = model.predict(target_ids).distribution_support
    probability = model.probability_model.predict(target_ids).distribution_support
    stacked = model.stacked_model.predict(target_ids).distribution_support
    expected = (1.0 - alpha) * probability + alpha * stacked
    assert np.allclose(ensemble, expected, rtol=0.0, atol=1e-15)
    assert np.all((ensemble >= 0.0) & (ensemble <= 1.0))


def test_structural_ensemble_rejects_invalid_weight():
    base = EOGDistributionConfig(
        graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0)
    )
    for value in (-0.1, 1.1, np.nan):
        try:
            EOGStructuralEnsembleConfig(base_config=base, stack_weight=value)
        except ValueError as exc:
            assert "stack_weight" in str(exc)
        else:
            raise AssertionError("invalid ensemble weight must be rejected")
