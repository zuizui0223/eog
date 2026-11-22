"""Exact source projection: conditional uniqueness does not imply historical origin.

Uses native EOG v2 rule compatibility plus complete synthetic 64-graph panels.
No published wetland sites or real biological source assignments are inferred.
"""
from dataclasses import replace

import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge, build_dynamic_transition_operator,
)
from eog.v2.fixed_source_hypothesis_sensitivity import (
    FixedSourceHypothesisIdentifiability,
    audit_fixed_source_hypotheses,
    summarize_fixed_source_hypothesis_identifiability,
)
from eog.v2.traversability import (
    summarize_fixed_source_hypothesis_identifiability as public,
)
from eog.v2 import summarize_fixed_source_hypothesis_identifiability as historical


NODES=("A","B","C")
BITS=(("A","B"),("A","C"),("B","A"),("B","C"),("C","A"),("C","B"))
SOURCES={"from_A":("A",),"from_B":("B",),"from_C":("C",)}


def rule(edges):
    return build_dynamic_transition_operator(
        NODES,
        [DynamicReachabilityEdge(
            source=NODES.index(a),target=NODES.index(b),
            geographic_support=1.0
        )for a,b in edges],
        loss_support=1.0,
    )


def all_64():
    return {f"mask_{mask:02d}":rule([
        e for i,e in enumerate(BITS) if mask&(1<<i)
    ]) for mask in range(64)}


def summarize(operators, positives=NODES, hypotheses=SOURCES):
    parent=audit_fixed_source_hypotheses(
        operators,positives,hypotheses,max_steps=1
    )
    return summarize_fixed_source_hypothesis_identifiability(parent)


def test_public_facade_and_historical_alias_are_same_summary():
    assert public is summarize_fixed_source_hypothesis_identifiability
    assert historical is summarize_fixed_source_hypothesis_identifiability


def test_all_64_exact_graph_conditional_vs_global_source_projection():
    summary=summarize(all_64())
    assert isinstance(summary,FixedSourceHypothesisIdentifiability)
    assert summary.candidate_rule_count==64
    assert summary.declared_source_hypothesis_ids==(
        "from_A","from_B","from_C"
    )
    assert summary.source_support_cardinality_counts==(
        (0,27),(1,27),(2,9),(3,1)
    )
    assert len(summary.uniquely_source_supported_rule_ids)==27
    assert summary.source_hypotheses_unique_given_rule_counts==(
        ("from_A",9),("from_B",9),("from_C",9)
    )
    assert summary.compatible_rule_source_assignment_count==48
    assert len(summary.compatible_rule_source_assignments)==48
    assert len(set(summary.compatible_rule_source_assignments))==48
    assert summary.possible_source_hypotheses_after_marginalizing_rule==(
        "from_A","from_B","from_C"
    )
    assert summary.source_hypothesis_identifiability_status==(
        "multiple_sources_possible_after_rule_marginalization"
    )
    assert not summary.historical_origin_identified
    assert not summary.graph_truth_or_source_prior_estimated
    assert ("mask_63","from_C") in summary.compatible_rule_source_assignments
    assert "mask_63" not in summary.uniquely_source_supported_rule_ids
    assert summary.parent_audit_fingerprint and summary.fingerprint


def test_uniqueness_conditional_on_hub_graph_does_not_certify_ancestry():
    hub=rule([
        ("A","C"),("C","A"),("B","C"),("C","B")
    ])
    s=summarize({"hub":hub})
    assert s.source_support_cardinality_counts==(
        (0,0),(1,1),(2,0),(3,0)
    )
    assert s.uniquely_source_supported_rule_ids==("hub",)
    assert s.compatible_rule_source_assignment_count==1
    assert s.compatible_rule_source_assignments==(("hub","from_C"),)
    assert s.possible_source_hypotheses_after_marginalizing_rule==("from_C",)
    assert s.source_hypothesis_identifiability_status==(
        "one_source_supported_within_declared_rule_and_source_universe"
    )
    assert not s.historical_origin_identified
    assert not s.graph_truth_or_source_prior_estimated


def test_complete_graph_admits_every_source_and_empty_graph_falsifies_universe():
    full=summarize({"complete":rule(BITS)})
    assert full.source_support_cardinality_counts==(
        (0,0),(1,0),(2,0),(3,1)
    )
    assert full.compatible_rule_source_assignment_count==3
    assert full.source_hypothesis_identifiability_status==(
        "multiple_sources_possible_after_rule_marginalization"
    )
    none=summarize({"disconnected":rule(())})
    assert none.source_support_cardinality_counts==(
        (0,1),(1,0),(2,0),(3,0)
    )
    assert none.compatible_rule_source_assignment_count==0
    assert none.possible_source_hypotheses_after_marginalizing_rule==()
    assert none.source_hypothesis_identifiability_status==(
        "declared_rule_source_universe_falsified"
    )


def test_one_source_declared_is_not_an_identification_test():
    s=summarize({"complete":rule(BITS)},NODES,{"only_A":("A",)})
    assert s.compatible_rule_source_assignment_count==1
    assert s.possible_source_hypotheses_after_marginalizing_rule==("only_A",)
    assert s.source_hypothesis_identifiability_status==(
        "single_candidate_declared_not_an_identification_test"
    )
    assert not s.historical_origin_identified


def test_two_positive_nodes_and_two_declared_source_hypotheses():
    s=summarize(all_64(),("B","A"),{"from_B":("B",),"from_A":("A",)})
    assert s.source_support_cardinality_counts==(
        (0,16),(1,32),(2,16)
    )
    assert s.compatible_rule_source_assignment_count==64
    assert s.source_hypotheses_unique_given_rule_counts==(
        ("from_A",16),("from_B",16)
    )
    assert s.possible_source_hypotheses_after_marginalizing_rule==(
        "from_A","from_B"
    )


def test_result_fingerprint_invariant_to_rule_and_source_input_order():
    rules=all_64()
    a=summarize(rules,("A","B","C"),SOURCES)
    b=summarize(
        dict(reversed(tuple(rules.items()))),("C","B","A"),
        {"from_C":("C",),"from_A":("A",),"from_B":("B",)}
    )
    assert a.fingerprint==b.fingerprint
    assert a.parent_audit_fingerprint==b.parent_audit_fingerprint


def test_fail_closed_when_audited_rule_source_partition_tampered():
    parent=audit_fixed_source_hypotheses(
        {"complete":rule(BITS)},NODES,SOURCES,max_steps=1
    )
    with pytest.raises(TypeError,match="FixedSourceHypothesisSensitivity"):
        summarize_fixed_source_hypothesis_identifiability(None)
    changed=replace(
        parent,
        rule_status=(replace(
            parent.rule_status[0],compatible_hypothesis_ids=("from_A",)
        ),)
    )
    with pytest.raises(ValueError,match="support identities inconsistent"):
        summarize_fixed_source_hypothesis_identifiability(changed)
    changed=replace(parent,source_robust_rule_ids=())
    with pytest.raises(ValueError,match="aggregate rule-source"):
        summarize_fixed_source_hypothesis_identifiability(changed)
    changed=replace(
        parent,
        rule_operator_fingerprints=(("wrong_id","hash"),)
    )
    with pytest.raises(ValueError,match="fingerprint identities"):
        summarize_fixed_source_hypothesis_identifiability(changed)
