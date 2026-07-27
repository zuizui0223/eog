import warnings

import pytest

from eog import BridgeEdge, BridgeWeights, infer_bridge


def test_mixed_cost_scales_emit_explicit_warning():
    edges = [
        BridgeEdge(0, 1, geographic_cost=120.0, environmental_cost=0.2),
        BridgeEdge(1, 2, geographic_cost=110.0, environmental_cost=0.3),
    ]
    with pytest.warns(RuntimeWarning, match="differ by more than 100-fold"):
        result = infer_bridge(3, edges, 0, 2, weights=BridgeWeights())
    assert result.minimum_cost_path.nodes == (0, 1, 2)


def test_explicit_scaling_policy_avoids_warning():
    edges = [
        BridgeEdge(0, 1, geographic_cost=120.0, environmental_cost=0.2),
        BridgeEdge(1, 2, geographic_cost=110.0, environmental_cost=0.3),
    ]
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        infer_bridge(
            3,
            edges,
            0,
            2,
            weights=BridgeWeights(geographic=0.01, environmental=1.0, barrier=0.0),
        )
    assert not record


def test_duplicate_undirected_edges_are_rejected():
    edges = [
        BridgeEdge(0, 1, geographic_cost=1.0, environmental_cost=0.0),
        BridgeEdge(1, 0, geographic_cost=2.0, environmental_cost=0.0),
    ]
    with pytest.raises(ValueError, match="duplicate undirected bridge edge"):
        infer_bridge(
            2,
            edges,
            0,
            1,
            weights=BridgeWeights(geographic=1.0, environmental=0.0, barrier=0.0),
        )
