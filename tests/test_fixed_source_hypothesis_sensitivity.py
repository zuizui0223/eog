"""Fixed-source hypothesis uncertainty as an exact finite rule-set bracket.

Every node, operator, scenario and expected count is synthetic: none of
these tests recognizes a real historical population source or absence.
"""
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.fixed_source_hypothesis_sensitivity import (
    FixedSourceHypothesisSensitivity,
    audit_fixed_source_hypotheses,
)
from eog.v2.traversability import audit_fixed_source_hypotheses as public_api
from eog.v2 import audit_fixed_source_hypotheses as historical_export


NODES=("A","B","C")
EDGES=(
    ("A","B"),("A","C"),("B","A"),
    ("B","C"),("C","A"),("C","B")
)


def graph(mask,nodes=NODES):
    edges=[DynamicReachabilityEdge(
        source=nodes.index(a),target=nodes.index(b),
        geographic_support=1.0,
    )for bit,(a,b) in enumerate(EDGES) if mask&(1<<bit)]
    return build_dynamic_transition_operator(nodes,edges,loss_support=1.0)


def all_graphs():
    return {f"mask_{m:02d}":graph(m) for m in range(64)}


def test_public_and_historical_exports_preserve_one_implementation():
    assert public_api is audit_fixed_source_hypotheses
    assert historical_export is audit_fixed_source_hypotheses


def test_complete_64_graph_single_source_hypothesis_bracket():
    result=audit_fixed_source_hypotheses(
        all_graphs(),NODES,
        {"from_A":("A",),"from_B":("B",),"from_C":("C",)},
        max_steps=1,
    )
    assert isinstance(result,FixedSourceHypothesisSensitivity)
    assert len(result.rule_status)==64
    assert len(result.rule_operator_fingerprints)==64
    assert len(result.source_hypotheses)==3
    assert {
        x.hypothesis_id:len(x.compatible_rule_ids)
        for x in result.source_hypotheses
    }=={"from_A":16,"from_B":16,"from_C":16}
    assert len(result.source_possible_rule_ids)==37
    assert result.source_robust_rule_ids==("mask_63",)
    assert len(result.source_dependent_rule_ids)==36
    assert len(result.source_impossible_under_declared_hypotheses_rule_ids)==27
    assert "mask_03" in result.source_dependent_rule_ids
    assert "mask_00" in result.source_impossible_under_declared_hypotheses_rule_ids
    assert not any(x.status=="source_robust" and x.rule_id!="mask_63"
                   for x in result.rule_status)
    assert result.source_hypotheses_are_NOT_independently_verified_historical_origins
    assert result.source_state_scope=="static_alternative_declared_fixed_sources_not_sequential"


def test_two_recorded_positive_nodes_have_different_source_possible_and_robust_counts():
    r=audit_fixed_source_hypotheses(
        all_graphs(),("A","B"),
        {"from_B":("B",),"from_A":("A",)},
        max_steps=1,
    )
    assert len(r.source_hypotheses)==2
    assert {x.hypothesis_id:len(x.compatible_rule_ids)
            for x in r.source_hypotheses}=={
                "from_A":32,"from_B":32
            }
    assert (len(r.source_possible_rule_ids),
            len(r.source_robust_rule_ids),
            len(r.source_dependent_rule_ids),
            len(r.source_impossible_under_declared_hypotheses_rule_ids))==(
                48,16,32,16
            )


def test_source_hypothesis_order_and_positive_node_order_do_not_change_fingerprint():
    ops=all_graphs()
    a=audit_fixed_source_hypotheses(
        ops,("A","B","C"),
        {"from_C":("C",),"from_A":("A",),"from_B":("B",)},
        max_steps=1,
    )
    b=audit_fixed_source_hypotheses(
        dict(reversed(tuple(ops.items()))),("C","A","B"),
        {"from_B":("B",),"from_C":("C",),"from_A":("A",)},
        max_steps=1,
    )
    assert a.fingerprint==b.fingerprint
    assert a.rule_operator_fingerprints==b.rule_operator_fingerprints


def test_multi_source_alternative_is_not_equivalent_to_union_of_single_source_scenarios():
    ops=all_graphs()
    a=audit_fixed_source_hypotheses(
        ops,("A","B","C"),
        {"joint_AB":("A","B"),"single_A":("A",)},
        max_steps=1,
    )
    assert a.source_hypotheses[0].hypothesis_id=="joint_AB"
    assert a.source_hypotheses[0].source_ids==("A","B")
    assert len(a.source_hypotheses[0].compatible_rule_ids)==48
    # With two jointly declared equal-weight sources, only target C
    # remains and either A>C or B>C suffices: 3 of 4 bit patterns.
    assert len(a.source_robust_rule_ids)==16
    assert len(a.source_possible_rule_ids)==48
    assert len(a.source_dependent_rule_ids)==32


@pytest.mark.parametrize("hypotheses,expected",[
    ({}, "at least one scenario"),
    ({"blank":()}, "distinct source IDs"),
    ({"not_a_source":("X",)}, "distinct source IDs"),
    ({"duplicate":("A","A")}, "distinct source IDs"),
    ({"all_three":("A","B","C")}, "non-source occurrence target"),
    ({"string_not_sequence":"A"}, "sequence of node IDs"),
    ({"":("A",)}, "nonblank strings"),
    ({"duplicate_1":("A",),"duplicate_2":("A",)}, "distinct fixed source sets"),
    ({"none_source":None}, "sequence of node IDs"),
])
def test_unqualified_source_hypotheses_fail_closed(hypotheses,expected):
    with pytest.raises(ValueError,match=expected):
        audit_fixed_source_hypotheses(
            all_graphs(),NODES,hypotheses,max_steps=1,
        )


def test_unfrozen_operator_node_universe_and_invalid_positive_roster_are_rejected():
    ops=all_graphs()
    ops["bad"]=build_dynamic_transition_operator(
        ("Q","R"),
        [DynamicReachabilityEdge(source=0,target=1,geographic_support=1.0)],
    )
    with pytest.raises(ValueError,match="same node IDs and order"):
        audit_fixed_source_hypotheses(
            ops,NODES,{"source_A":("A",)},max_steps=1,
        )
    with pytest.raises(ValueError,match="positive_occurrence_ids"):
        audit_fixed_source_hypotheses(
            all_graphs(),("A","A","B"),{"source_A":("A",)},max_steps=1,
        )
    with pytest.raises(ValueError,match="sequence, not a string"):
        audit_fixed_source_hypotheses(
            all_graphs(),"ABC",{"source_A":("A",)},max_steps=1,
        )
    with pytest.raises(ValueError,match="max_steps"):
        audit_fixed_source_hypotheses(
            all_graphs(),NODES,{"source_A":("A",)},max_steps=0,
        )


def test_no_source_truth_is_inferred_for_even_all_candidate_rule_compatibility():
    r=audit_fixed_source_hypotheses(
        {"complete":graph(63)},NODES,
        {"assumed_A":("A",),"assumed_B":("B",),"assumed_C":("C",)},
        max_steps=1,
    )
    assert r.source_robust_rule_ids==("complete",)
    assert r.source_dependent_rule_ids==()
    assert r.source_impossible_under_declared_hypotheses_rule_ids==()
    assert r.source_hypotheses_are_NOT_independently_verified_historical_origins
    assert "declared_fixed_source_hypotheses" in r.coverage_certificate
