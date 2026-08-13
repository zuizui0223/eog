import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
)
from eog.reachability_network_diagnostics import (
    evaluate_bridge_node_importance,
    summarize_network_flux,
)


def edge(a, b, support=0.9):
    return DynamicReachabilityEdge(a, b, geographic_support=support)


def test_flux_entropy_distinguishes_single_route_from_redundant_split():
    chain = build_dynamic_transition_operator(
        ("source", "mid", "target"),
        [edge(0, 1), edge(1, 2)],
        loss_support=0.5,
    )
    chain_result = propagate_dynamic_reachability(chain, ["source"], max_steps=3)
    chain_flux = summarize_network_flux(chain_result)
    assert chain_flux.active_outdegree[0] == 1
    assert chain_flux.outgoing_flux_entropy[0] == pytest.approx(0.0)

    diamond = build_dynamic_transition_operator(
        ("source", "left", "right", "target"),
        [edge(0, 1), edge(0, 2), edge(1, 3), edge(2, 3)],
        loss_support=0.5,
    )
    diamond_result = propagate_dynamic_reachability(diamond, ["source"], max_steps=3)
    diamond_flux = summarize_network_flux(diamond_result)
    assert diamond_flux.active_outdegree[0] == 2
    assert diamond_flux.outgoing_flux_entropy[0] == pytest.approx(1.0)
    assert np.sum(diamond_flux.edge_flux_fraction) == pytest.approx(1.0)


def test_bridge_importance_is_one_for_mandatory_chain_node():
    operator = build_dynamic_transition_operator(
        ("source", "mid", "target"),
        [edge(0, 1), edge(1, 2)],
        loss_support=0.5,
    )
    result = evaluate_bridge_node_importance(operator, ["source"], "target", max_steps=3)
    assert result.baseline_first_passage_support > 0.0
    assert result.blocked_first_passage_support[1] == pytest.approx(0.0)
    assert result.relative_support_loss[1] == pytest.approx(1.0)
    assert np.isnan(result.relative_support_loss[0])
    assert np.isnan(result.relative_support_loss[2])


def test_redundant_diamond_nodes_each_have_partial_importance():
    operator = build_dynamic_transition_operator(
        ("source", "left", "right", "target"),
        [edge(0, 1), edge(0, 2), edge(1, 3), edge(2, 3)],
        loss_support=0.5,
    )
    result = evaluate_bridge_node_importance(operator, ["source"], "target", max_steps=3)
    assert 0.0 < result.relative_support_loss[1] < 1.0
    assert result.relative_support_loss[1] == pytest.approx(result.relative_support_loss[2])
    assert result.blocked_first_passage_support[1] > 0.0


def test_blocking_node_never_increases_first_passage_support():
    operator = build_dynamic_transition_operator(
        ("s1", "s2", "mid", "target"),
        [edge(0, 2, 0.8), edge(1, 2, 0.5), edge(2, 3, 0.9), edge(0, 3, 0.1)],
        loss_support=0.5,
    )
    result = evaluate_bridge_node_importance(
        operator,
        {"s1": 0.75, "s2": 0.25},
        "target",
        max_steps=4,
    )
    finite = np.isfinite(result.blocked_first_passage_support)
    assert np.all(result.blocked_first_passage_support[finite] <= result.baseline_first_passage_support + 1e-12)
