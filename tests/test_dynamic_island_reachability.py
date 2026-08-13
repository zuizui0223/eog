import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
    summarize_first_passage,
)


def _edge(a, b, support, *, direction=1.0, capture=1.0):
    return DynamicReachabilityEdge(
        a,
        b,
        geographic_support=support,
        directional_support=direction,
        target_capture_support=capture,
    )


def test_substochastic_operator_preserves_absolute_edge_weakness_and_mass_decays():
    weak = build_dynamic_transition_operator(
        ("source", "target"),
        [_edge(0, 1, 0.1)],
        loss_support=1.0,
    )
    strong = build_dynamic_transition_operator(
        ("source", "target"),
        [_edge(0, 1, 0.9)],
        loss_support=1.0,
    )
    assert np.all(weak.transition.sum(axis=1) < 1.0)
    assert np.all(strong.transition.sum(axis=1) < 1.0)
    assert strong.transition[0, 1] > weak.transition[0, 1]

    result = propagate_dynamic_reachability(strong, ["source"], max_steps=4)
    assert np.all(np.diff(result.total_mass_by_step) <= 1e-12)
    assert result.total_mass_by_step[0] == pytest.approx(1.0)
    assert result.total_mass_by_step[1] < 1.0


def test_same_endpoint_chain_recovers_stepping_stone_structure():
    ids = ("source", "step1", "step2", "target")
    chain = build_dynamic_transition_operator(
        ids,
        [_edge(0, 1, 0.9), _edge(1, 2, 0.9), _edge(2, 3, 0.9)],
        loss_support=0.5,
    )
    broken = build_dynamic_transition_operator(
        ids,
        [_edge(0, 1, 0.9), _edge(2, 3, 0.9)],
        loss_support=0.5,
    )

    chain_fp = summarize_first_passage(chain, ["source"], "target", max_steps=5)
    broken_fp = summarize_first_passage(broken, ["source"], "target", max_steps=5)

    assert chain_fp.first_positive_step == 3
    assert chain_fp.horizon_support > 0.0
    assert broken_fp.first_positive_step is None
    assert broken_fp.horizon_support == pytest.approx(0.0)


def test_bottleneck_reduces_first_passage_support_without_changing_hop_depth():
    ids = ("source", "step1", "step2", "target")
    open_chain = build_dynamic_transition_operator(
        ids,
        [_edge(0, 1, 0.9), _edge(1, 2, 0.9), _edge(2, 3, 0.9)],
        loss_support=0.5,
    )
    bottleneck = build_dynamic_transition_operator(
        ids,
        [_edge(0, 1, 0.9), _edge(1, 2, 0.05), _edge(2, 3, 0.9)],
        loss_support=0.5,
    )
    open_fp = summarize_first_passage(open_chain, ["source"], "target", max_steps=5)
    bottleneck_fp = summarize_first_passage(bottleneck, ["source"], "target", max_steps=5)

    assert open_fp.first_positive_step == bottleneck_fp.first_positive_step == 3
    assert open_fp.horizon_support > bottleneck_fp.horizon_support > 0.0


def test_directional_support_creates_asymmetric_reachability():
    ids = ("west", "mid", "east")
    operator = build_dynamic_transition_operator(
        ids,
        [
            _edge(0, 1, 0.9, direction=1.0),
            _edge(1, 2, 0.9, direction=1.0),
            _edge(2, 1, 0.9, direction=0.1),
            _edge(1, 0, 0.9, direction=0.1),
        ],
        loss_support=0.5,
    )
    west_to_east = summarize_first_passage(operator, ["west"], "east", max_steps=4)
    east_to_west = summarize_first_passage(operator, ["east"], "west", max_steps=4)
    assert west_to_east.horizon_support > east_to_west.horizon_support


def test_target_capture_support_affects_arrival_but_not_persistence_layer():
    ids = ("source", "small_target", "large_target")
    operator = build_dynamic_transition_operator(
        ids,
        [
            _edge(0, 1, 0.8, capture=0.25),
            _edge(0, 2, 0.8, capture=1.0),
        ],
        loss_support=1.0,
    )
    small = summarize_first_passage(operator, ["source"], "small_target", max_steps=1)
    large = summarize_first_passage(operator, ["source"], "large_target", max_steps=1)
    assert large.horizon_support > small.horizon_support


def test_multiple_source_attribution_is_normalized_for_supported_target():
    ids = ("left", "right", "target")
    operator = build_dynamic_transition_operator(
        ids,
        [_edge(0, 2, 0.9), _edge(1, 2, 0.2)],
        loss_support=0.5,
    )
    summary = summarize_first_passage(
        operator,
        {"left": 0.5, "right": 0.5},
        "target",
        max_steps=2,
    )
    assert summary.horizon_support > 0.0
    assert np.sum(summary.source_attribution) == pytest.approx(1.0)
    assert summary.source_attribution[0] > summary.source_attribution[1]


def test_validation_rejects_duplicates_and_nonpositive_loss_support():
    ids = ("a", "b")
    with pytest.raises(ValueError, match="duplicate"):
        build_dynamic_transition_operator(ids, [_edge(0, 1, 0.5), _edge(0, 1, 0.4)])
    with pytest.raises(ValueError, match="strictly positive"):
        build_dynamic_transition_operator(ids, [_edge(0, 1, 0.5)], loss_support=0.0)
