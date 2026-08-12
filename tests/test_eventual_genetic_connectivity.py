import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.eventual_genetic_connectivity import (
    build_eventual_genetic_validation_bundle,
    infer_eventual_genetic_connectivity,
)


def edge(a, b, support):
    return DynamicReachabilityEdge(a, b, geographic_support=support)


def test_one_way_support_remains_finite_exchange_not_disconnected():
    operator = build_dynamic_transition_operator(
        ("west", "east"),
        [edge(0, 1, 0.8)],
        loss_support=0.5,
    )
    result = infer_eventual_genetic_connectivity(operator)
    assert result.directional_support[0, 1] > 0.0
    assert result.directional_support[1, 0] == 0.0
    assert not result.disconnected[0, 1]
    expected = -np.log(0.5 * result.directional_support[0, 1])
    assert result.continuous_distance[0, 1] == pytest.approx(expected)


def test_bidirectionally_disconnected_pair_has_explicit_indicator_and_finite_cap():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 0, 0.8)],
        loss_support=0.5,
    )
    result = infer_eventual_genetic_connectivity(operator)
    assert result.disconnected[0, 2]
    assert result.disconnected[1, 2]
    assert np.isfinite(result.continuous_distance).all()
    assert result.continuous_distance[0, 2] == pytest.approx(
        result.disconnected_distance_cap
    )
    assert result.continuous_distance[1, 2] == pytest.approx(
        result.disconnected_distance_cap
    )


def test_unsampled_intermediate_remains_available_to_genetic_path():
    operator = build_dynamic_transition_operator(
        ("source", "bridge", "target"),
        [edge(0, 1, 0.8), edge(1, 2, 0.8), edge(2, 1, 0.4), edge(1, 0, 0.4)],
        loss_support=0.5,
    )
    result = infer_eventual_genetic_connectivity(
        operator,
        sampled_node_ids=("source", "target"),
    )
    assert result.node_ids == ("source", "target")
    assert result.symmetric_exchange_support[0, 1] > 0.0
    assert not result.disconnected[0, 1]


def test_bundle_contains_disconnection_as_separate_predictor_and_no_floor_parameter():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 0, 0.8)],
        loss_support=0.5,
    )
    connectivity = infer_eventual_genetic_connectivity(operator)
    d_geo = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
    d_env = np.array([[0, 0.2, 0.4], [0.2, 0, 0.2], [0.4, 0.2, 0]], dtype=float)
    bundle = build_eventual_genetic_validation_bundle(d_geo, d_env, connectivity)
    assert bundle.eog_disconnected[0, 2]
    assert "no propagation horizon or numerical support-floor" in bundle.method
    assert bundle.connectivity_fingerprint == connectivity.fingerprint
    assert len(bundle.fingerprint) == 64


def test_connectivity_is_deterministic():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 0, 0.4), edge(1, 2, 0.6), edge(2, 1, 0.3)],
        loss_support=0.5,
    )
    first = infer_eventual_genetic_connectivity(operator)
    second = infer_eventual_genetic_connectivity(operator)
    assert first.fingerprint == second.fingerprint
    assert np.array_equal(first.continuous_distance, second.continuous_distance)
    assert np.array_equal(first.disconnected, second.disconnected)
