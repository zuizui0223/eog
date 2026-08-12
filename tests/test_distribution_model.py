import numpy as np
import pytest

from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    EOGDistributionConfig,
    fit_eog_distribution,
)


def _landscape():
    return [
        BridgeNode("source_a", 0.0, 0.00, (0.80,)),
        BridgeNode("source_b", 0.0, 0.05, (0.90,)),
        BridgeNode("near", 0.0, 0.10, (0.85,)),
        BridgeNode("neg_a", 0.0, 0.15, (0.10,)),
        BridgeNode("far", 0.0, 2.00, (0.85,)),
        BridgeNode("neg_b", 0.0, 2.05, (0.10,)),
    ]


def _fit(nodes=None, predictors=None):
    nodes = _landscape() if nodes is None else nodes
    return fit_eog_distribution(
        nodes,
        ["source_a", "source_b", "neg_a", "neg_b"],
        [1, 1, 0, 0],
        EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=30.0),
            min_class_count=2,
        ),
        support_predictors=predictors,
        reference_provenance="synthetic distribution-model test",
    )


def test_equal_environmental_support_is_separated_by_structural_accessibility():
    model = _fit()
    prediction = model.predict(["near", "far"])

    assert prediction.environmental_support[0] == pytest.approx(
        prediction.environmental_support[1]
    )
    assert prediction.structural_accessibility[0] > 0.0
    assert prediction.structural_accessibility[1] == pytest.approx(0.0)
    assert np.isfinite(prediction.minimum_cumulative_cost[0])
    assert np.isinf(prediction.minimum_cumulative_cost[1])
    assert prediction.distribution_support[0] > prediction.distribution_support[1]
    assert prediction.distribution_support[1] == pytest.approx(0.0)


def test_only_positive_observations_become_sources():
    model = _fit()
    assert model.source_node_ids == ("source_a", "source_b")
    prediction = model.predict(["neg_a", "neg_b"])
    assert prediction.structural_accessibility[0] > 0.0
    assert prediction.structural_accessibility[1] == pytest.approx(0.0)


def test_second_source_cost_and_redundancy_are_exposed_separately():
    model = _fit()
    prediction = model.predict(["near"])
    assert np.isfinite(prediction.minimum_cumulative_cost[0])
    assert np.isfinite(prediction.secondary_source_cost[0])
    assert prediction.secondary_source_cost[0] >= prediction.minimum_cumulative_cost[0]
    assert 0.0 < prediction.source_redundancy[0] <= 1.0


def test_fit_is_deterministic_under_landscape_input_reordering():
    nodes = _landscape()
    first = _fit(nodes)
    order = [4, 1, 5, 0, 3, 2]
    shuffled = [nodes[index] for index in order]
    second = _fit(shuffled)

    assert first.fingerprint == second.fingerprint
    assert first.graph.fingerprint == second.graph.fingerprint
    assert first.predict().node_ids == second.predict().node_ids
    assert np.array_equal(
        first.predict().distribution_support,
        second.predict().distribution_support,
    )


def test_custom_pointwise_predictors_follow_input_node_order():
    nodes = _landscape()
    predictors = np.asarray([[node.environmental_state[0], i] for i, node in enumerate(nodes)])
    first = _fit(nodes, predictors)

    order = [4, 1, 5, 0, 3, 2]
    shuffled = [nodes[index] for index in order]
    shuffled_predictors = predictors[order]
    second = _fit(shuffled, shuffled_predictors)

    assert first.fingerprint == second.fingerprint


def test_prediction_subset_rejects_unknown_or_duplicate_ids():
    model = _fit()
    with pytest.raises(ValueError, match="unknown prediction node IDs"):
        model.predict(["missing"])
    with pytest.raises(ValueError, match="must be unique"):
        model.predict(["near", "near"])


def test_observed_labels_must_be_inside_declared_landscape():
    with pytest.raises(ValueError, match="outside the landscape universe"):
        fit_eog_distribution(
            _landscape(),
            ["source_a", "source_b", "neg_a", "missing"],
            [1, 1, 0, 0],
            EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=30.0),
                min_class_count=2,
            ),
        )
