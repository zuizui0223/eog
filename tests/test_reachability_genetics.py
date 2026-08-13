import numpy as np
import pytest

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.reachability_genetics import (
    build_genetic_validation_distance_bundle,
    pairwise_reachability_distances,
)


def edge(a, b, support, direction=1.0):
    return DynamicReachabilityEdge(
        a,
        b,
        geographic_support=support,
        directional_support=direction,
    )


def test_directional_colonisation_distance_and_symmetric_genetic_distance_are_separate():
    operator = build_dynamic_transition_operator(
        ("west", "mid", "east"),
        [
            edge(0, 1, 0.9, 1.0),
            edge(1, 2, 0.9, 1.0),
            edge(2, 1, 0.9, 0.1),
            edge(1, 0, 0.9, 0.1),
        ],
        loss_support=0.5,
    )
    result = pairwise_reachability_distances(
        operator,
        max_steps=4,
        symmetrization="mean_log",
    )
    assert result.directional_distance[0, 2] < result.directional_distance[2, 0]
    assert np.allclose(result.symmetric_distance, result.symmetric_distance.T)
    assert result.symmetric_distance[0, 2] == pytest.approx(
        0.5 * (result.directional_distance[0, 2] + result.directional_distance[2, 0])
    )


def test_unreached_pair_uses_explicit_finite_floor():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8)],
        loss_support=0.5,
    )
    result = pairwise_reachability_distances(
        operator,
        max_steps=3,
        support_floor=1e-6,
        symmetrization="max_log",
    )
    assert result.directional_support[0, 2] == 0.0
    assert result.directional_distance[0, 2] == pytest.approx(-np.log(1e-6))


def test_genetic_bundle_freezes_ibd_ibe_and_eog_without_response_data():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 0, 0.8), edge(1, 2, 0.4), edge(2, 1, 0.4)],
        loss_support=0.5,
    )
    reachability = pairwise_reachability_distances(
        operator,
        max_steps=4,
        symmetrization="mean_log",
    )
    d_geo = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
    d_env = np.array([[0, 0.2, 0.5], [0.2, 0, 0.3], [0.5, 0.3, 0]], dtype=float)
    bundle = build_genetic_validation_distance_bundle(d_geo, d_env, reachability)
    assert bundle.node_ids == ("a", "b", "c")
    assert np.array_equal(bundle.geographic_distance, d_geo)
    assert np.array_equal(bundle.environmental_distance, d_env)
    assert np.array_equal(bundle.reachability_distance, reachability.symmetric_distance)
    assert len(bundle.fingerprint) == 64


def test_symmetrization_choice_is_explicit_and_fingerprinted():
    operator = build_dynamic_transition_operator(
        ("a", "b"),
        [edge(0, 1, 0.8), edge(1, 0, 0.2)],
        loss_support=0.5,
    )
    mean = pairwise_reachability_distances(operator, max_steps=2, symmetrization="mean_log")
    maximum = pairwise_reachability_distances(operator, max_steps=2, symmetrization="max_log")
    assert not np.array_equal(mean.symmetric_distance, maximum.symmetric_distance)
    assert mean.fingerprint != maximum.fingerprint
    with pytest.raises(ValueError, match="symmetrization"):
        pairwise_reachability_distances(operator, max_steps=2, symmetrization="automatic")
