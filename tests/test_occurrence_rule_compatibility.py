import pytest

from eog.v2 import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    compare_occurrence_transition_rules,
    evaluate_occurrence_rule_compatibility,
)


NODE_IDS = ("A", "B", "C")


def _operator(kind):
    if kind == "chain":
        edges = [
            DynamicReachabilityEdge(0, 1, geographic_support=0.8),
            DynamicReachabilityEdge(1, 2, geographic_support=0.8),
        ]
    elif kind == "broken":
        edges = [DynamicReachabilityEdge(0, 1, geographic_support=0.8)]
    elif kind == "permissive":
        edges = [
            DynamicReachabilityEdge(i, j, geographic_support=0.8)
            for i in range(3)
            for j in range(3)
            if i != j
        ]
    else:
        raise ValueError(kind)
    return build_dynamic_transition_operator(NODE_IDS, edges, loss_support=0.5)


def test_fixed_source_occurrences_constrain_a_broken_transition_rule():
    chain = evaluate_occurrence_rule_compatibility(
        _operator("chain"),
        NODE_IDS,
        rule_id="chain",
        fixed_source_ids=["A"],
        max_steps=2,
    )
    broken = evaluate_occurrence_rule_compatibility(
        _operator("broken"),
        NODE_IDS,
        rule_id="broken",
        fixed_source_ids=["A"],
        max_steps=2,
    )

    assert chain.source_policy == "fixed"
    assert chain.coverage_fraction == 1.0
    assert chain.unsupported_occurrence_ids == ()
    assert broken.coverage_fraction == 0.5
    assert broken.unsupported_occurrence_ids == ("C",)


def test_permissive_rule_is_not_auto_promoted_over_a_supported_chain():
    comparison = compare_occurrence_transition_rules(
        {
            "chain": _operator("chain"),
            "permissive": _operator("permissive"),
        },
        NODE_IDS,
        fixed_source_ids=["A"],
        max_steps=2,
    )
    results = {result.rule_id: result for result in comparison.rule_results}

    assert results["chain"].coverage_fraction == 1.0
    assert results["permissive"].coverage_fraction == 1.0
    assert (
        results["permissive"].operator_active_edge_fraction
        > results["chain"].operator_active_edge_fraction
    )
    assert (
        results["permissive"].operator_mean_outgoing_mass
        > results["chain"].operator_mean_outgoing_mass
    )
    assert not hasattr(comparison, "winner")
    assert not hasattr(comparison, "score")


def test_self_excluded_peer_source_is_not_a_directional_history_test():
    chain = _operator("chain")
    fixed = evaluate_occurrence_rule_compatibility(
        chain,
        NODE_IDS,
        rule_id="chain-fixed",
        fixed_source_ids=["A"],
        max_steps=2,
    )
    peer = evaluate_occurrence_rule_compatibility(
        chain,
        NODE_IDS,
        rule_id="chain-peer",
        max_steps=2,
    )

    assert fixed.coverage_fraction == 1.0
    assert peer.source_policy == "self_excluded"
    assert peer.coverage_fraction == pytest.approx(2.0 / 3.0)
    assert peer.unsupported_occurrence_ids == ("A",)


def test_occurrence_input_order_does_not_change_fingerprint():
    operator = _operator("chain")
    forward = evaluate_occurrence_rule_compatibility(
        operator,
        ["A", "B", "C"],
        rule_id="chain",
        fixed_source_ids=["A"],
        max_steps=2,
    )
    reverse = evaluate_occurrence_rule_compatibility(
        operator,
        ["C", "B", "A"],
        rule_id="chain",
        fixed_source_ids=["A"],
        max_steps=2,
    )
    assert forward.occurrence_ids == reverse.occurrence_ids == NODE_IDS
    assert forward.fingerprint == reverse.fingerprint


def test_fixed_sources_must_be_observed_occurrences():
    with pytest.raises(ValueError, match="subset of occurrence_ids"):
        evaluate_occurrence_rule_compatibility(
            _operator("chain"),
            ["B", "C"],
            rule_id="bad-source",
            fixed_source_ids=["A"],
            max_steps=2,
        )
