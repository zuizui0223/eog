import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)
from eog.eventual_reachability_genetics import (
    build_eventual_genetic_validation_distance_bundle,
    eventual_first_passage_support_matrix,
    pairwise_eventual_reachability_distances,
)


def edge(a, b, support, direction=1.0):
    return DynamicReachabilityEdge(
        a,
        b,
        geographic_support=support,
        directional_support=direction,
    )


def test_exact_eventual_support_matches_long_finite_horizon_on_acyclic_chain():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 2, 0.6)],
        loss_support=0.5,
    )
    ids, support = eventual_first_passage_support_matrix(operator)
    finite = summarize_first_passage(operator, ["a"], "c", max_steps=20)
    assert ids == ("a", "b", "c")
    assert support[0, 2] == pytest.approx(finite.horizon_support, rel=0, abs=1e-14)


def test_eventual_support_includes_repeated_indirect_routes_beyond_short_horizon():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [
            edge(0, 1, 0.8),
            edge(1, 0, 0.8),
            edge(1, 2, 0.2),
            edge(2, 1, 0.2),
        ],
        loss_support=0.5,
    )
    _, support = eventual_first_passage_support_matrix(operator)
    short = summarize_first_passage(operator, ["a"], "c", max_steps=2)
    long = summarize_first_passage(operator, ["a"], "c", max_steps=100)
    assert support[0, 2] > short.horizon_support
    assert support[0, 2] == pytest.approx(long.horizon_support, rel=0, abs=1e-12)


def test_eventual_directionality_and_symmetric_genetic_distance_remain_separate():
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
    result = pairwise_eventual_reachability_distances(
        operator,
        support_floor=1e-9,
        symmetrization="mean_log",
    )
    assert result.directional_distance[0, 2] < result.directional_distance[2, 0]
    assert result.symmetric_distance[0, 2] == pytest.approx(
        0.5 * (result.directional_distance[0, 2] + result.directional_distance[2, 0])
    )
    assert np.allclose(result.symmetric_distance, result.symmetric_distance.T)


def test_mean_support_symmetrisation_retains_one_way_gene_flow_signal():
    operator = build_dynamic_transition_operator(
        ("west", "east"),
        [edge(0, 1, 0.8)],
        loss_support=0.5,
    )
    mean_log = pairwise_eventual_reachability_distances(
        operator,
        support_floor=1e-9,
        symmetrization="mean_log",
    )
    mean_support = pairwise_eventual_reachability_distances(
        operator,
        support_floor=1e-9,
        symmetrization="mean_support",
    )
    assert mean_support.symmetric_distance[0, 1] < mean_log.symmetric_distance[0, 1]
    reciprocal_mean = 0.5 * (
        mean_support.directional_support[0, 1]
        + mean_support.directional_support[1, 0]
    )
    assert mean_support.symmetric_distance[0, 1] == pytest.approx(-np.log(reciprocal_mean))
    assert mean_support.fingerprint != mean_log.fingerprint


def test_exact_zero_support_is_retained_separately_from_numerical_floor():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8)],
        loss_support=0.5,
    )
    result = pairwise_eventual_reachability_distances(
        operator,
        support_floor=1e-6,
        symmetrization="max_log",
    )
    assert result.directional_support[0, 2] == 0.0
    assert result.zero_support[0, 2]
    assert result.directional_distance[0, 2] == pytest.approx(-np.log(1e-6))


def test_paths_may_use_unsampled_intermediate_nodes():
    operator = build_dynamic_transition_operator(
        ("source", "unsampled_bridge", "target"),
        [edge(0, 1, 0.8), edge(1, 2, 0.8)],
        loss_support=0.5,
    )
    result = pairwise_eventual_reachability_distances(
        operator,
        sampled_node_ids=("source", "target"),
        support_floor=1e-9,
        symmetrization="mean_log",
    )
    assert result.node_ids == ("source", "target")
    assert result.directional_support[0, 1] > 0.0


def test_eventual_bundle_freezes_method_without_genetic_response():
    operator = build_dynamic_transition_operator(
        ("a", "b", "c"),
        [edge(0, 1, 0.8), edge(1, 0, 0.8), edge(1, 2, 0.4), edge(2, 1, 0.4)],
        loss_support=0.5,
    )
    reachability = pairwise_eventual_reachability_distances(
        operator,
        support_floor=1e-9,
        symmetrization="mean_support",
    )
    d_geo = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
    d_env = np.array([[0, 0.2, 0.5], [0.2, 0, 0.3], [0.5, 0.3, 0]], dtype=float)
    bundle = build_eventual_genetic_validation_distance_bundle(d_geo, d_env, reachability)
    assert "exact eventual first-passage" in bundle.reachability_method
    assert "mean_support" in bundle.reachability_method
    assert bundle.reachability_fingerprint == reachability.fingerprint
    assert len(bundle.fingerprint) == 64


def test_unknown_eventual_symmetrisation_is_rejected():
    operator = build_dynamic_transition_operator(
        ("a", "b"),
        [edge(0, 1, 0.8), edge(1, 0, 0.8)],
        loss_support=0.5,
    )
    with pytest.raises(ValueError, match="symmetrization"):
        pairwise_eventual_reachability_distances(
            operator,
            symmetrization="automatic",
        )
