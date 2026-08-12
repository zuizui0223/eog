import numpy as np

from eog import BridgeGraphDeclaration, BridgeNode, EOGDistributionConfig
from eog.distribution_odds import (
    EOGOddsGateConfig,
    fit_eog_odds_distribution,
    odds_accessibility_fusion,
)


def _landscape():
    return [
        BridgeNode("source_a", 0.0, 0.00, (0.9,)),
        BridgeNode("source_b", 0.0, 0.02, (0.9,)),
        BridgeNode("negative_a", 0.0, 0.04, (0.2,)),
        BridgeNode("negative_b", 0.0, 0.06, (0.2,)),
        BridgeNode("target", 0.0, 0.08, (0.9,)),
    ]


def test_odds_accessibility_zero_strength_reduces_exactly_to_environmental_support():
    environmental = np.asarray([0.2, 0.5, 0.9])
    accessibility = np.asarray([0.0, 0.3, 1.0])
    result = odds_accessibility_fusion(environmental, accessibility, 0.0)
    assert np.array_equal(result, environmental)


def test_odds_accessibility_never_inflates_environmental_baseline():
    environmental = np.asarray([0.2, 0.5, 0.9])
    accessibility = np.asarray([0.0, 0.3, 1.0])
    result = odds_accessibility_fusion(environmental, accessibility, 2.0)
    assert np.all(result <= environmental + 1e-15)
    assert result[-1] == environmental[-1]
    assert result[0] < 1e-10


def test_odds_gate_requires_inner_folds_when_strength_is_estimated():
    base = EOGDistributionConfig(
        graph_declaration=BridgeGraphDeclaration(max_geographic_km=20.0),
        min_class_count=2,
    )
    config = EOGOddsGateConfig(base_config=base)
    try:
        fit_eog_odds_distribution(
            _landscape(),
            ["source_a", "source_b", "negative_a", "negative_b"],
            [1, 1, 0, 0],
            config,
        )
    except ValueError as exc:
        assert "gate_fold_ids are required" in str(exc)
    else:
        raise AssertionError("estimated odds gate must require inner folds")


def test_fixed_zero_odds_gate_returns_environmental_prediction():
    base = EOGDistributionConfig(
        graph_declaration=BridgeGraphDeclaration(max_geographic_km=20.0),
        min_class_count=2,
    )
    model = fit_eog_odds_distribution(
        _landscape(),
        ["source_a", "source_b", "negative_a", "negative_b"],
        [1, 1, 0, 0],
        EOGOddsGateConfig(base_config=base, structural_gate_strength=0.0),
    )
    prediction = model.predict()
    assert model.structural_gate_strength == 0.0
    assert model.structural_gate_fitted is False
    assert np.array_equal(
        prediction.distribution_support, prediction.environmental_support
    )
