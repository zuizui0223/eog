import numpy as np
import pytest

from eog import (
    BridgeEdge,
    BridgeWeights,
    environmental_edge_costs,
    fit_robust_reference,
    infer_bridge,
)


def test_continuous_bridge_beats_direct_jump():
    edges = [
        BridgeEdge(0, 1, 1.0, 0.2),
        BridgeEdge(1, 2, 1.0, 0.2),
        BridgeEdge(0, 2, 1.0, 4.0),
    ]
    result = infer_bridge(3, edges, 0, 2)
    assert result.minimum_cost_path.nodes == (0, 1, 2)
    assert result.minimum_cost_path.cumulative_cost == pytest.approx(2.4)
    assert result.direct_edge_cost == pytest.approx(5.0)
    assert result.bridge_gain == pytest.approx(2.6)


def test_minimax_path_can_differ_from_minimum_sum_path():
    edges = [
        BridgeEdge(0, 1, 0.0, 1.0),
        BridgeEdge(1, 3, 0.0, 4.0),
        BridgeEdge(0, 2, 0.0, 3.0),
        BridgeEdge(2, 3, 0.0, 3.0),
    ]
    result = infer_bridge(4, edges, 0, 3)
    assert result.minimum_cost_path.nodes == (0, 1, 3)
    assert result.minimum_cost_path.cumulative_cost == pytest.approx(5.0)
    assert result.minimum_bottleneck_path.nodes == (0, 2, 3)
    assert result.minimum_bottleneck_path.bottleneck_cost == pytest.approx(3.0)


def test_barrier_penalty_changes_selected_path():
    edges = [
        BridgeEdge(0, 1, 1.0, 0.0, 10.0),
        BridgeEdge(1, 3, 1.0, 0.0, 0.0),
        BridgeEdge(0, 2, 2.0, 0.0, 0.0),
        BridgeEdge(2, 3, 2.0, 0.0, 0.0),
    ]
    no_barrier = infer_bridge(4, edges, 0, 3, weights=BridgeWeights(1, 0, 0))
    with_barrier = infer_bridge(4, edges, 0, 3, weights=BridgeWeights(1, 0, 1))
    assert no_barrier.minimum_cost_path.nodes == (0, 1, 3)
    assert with_barrier.minimum_cost_path.nodes == (0, 2, 3)


def test_edge_disjoint_redundancy_counts_alternative_bridges():
    edges = [
        BridgeEdge(0, 1, 1.0, 0.0),
        BridgeEdge(1, 3, 1.0, 0.0),
        BridgeEdge(0, 2, 1.0, 0.0),
        BridgeEdge(2, 3, 1.0, 0.0),
    ]
    result = infer_bridge(4, edges, 0, 3, redundancy_threshold=1.0)
    assert result.edge_disjoint_path_count == 2


def test_environmental_cost_uses_one_shared_reference():
    reference_values = np.array([[0.0, 0.0], [2.0, 4.0], [4.0, 8.0]])
    reference = fit_robust_reference(reference_values, provenance="frozen test reference")
    values = np.array([[0.0, 0.0], [2.0, 4.0], [4.0, 8.0]])
    costs = environmental_edge_costs(values, [(0, 1), (1, 2)], reference)
    assert costs[0][2] == pytest.approx(costs[1][2])


def test_disconnected_graph_is_rejected():
    with pytest.raises(ValueError, match="disconnected"):
        infer_bridge(3, [BridgeEdge(0, 1, 1.0, 1.0)], 0, 2)
