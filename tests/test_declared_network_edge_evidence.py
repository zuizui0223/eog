"""Exact graph structural-edge evidence source projection on 64 toy EOG rules.

An independently declared structural nonedge is NOT synonymous with
a recorded species non-detection; all cases here are synthetic known truth.
"""
from itertools import combinations
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge, build_dynamic_transition_operator
)
from eog.v2.declared_network_edge_evidence import (
    DeclaredDirectedEdgeEvidence, DirectedNetworkEvidenceSourceProjection,
    audit_declared_directed_network_evidence
)
from eog.v2.traversability import audit_declared_directed_network_evidence as public
from eog.v2 import audit_declared_directed_network_evidence as historical

NODES=("A","B","C")
BITS=(
    ("A","B"),("A","C"),("B","A"),("B","C"),("C","A"),("C","B")
)
HYPOTHESES={
    "from_A":("A",), "from_B":("B",), "from_C":("C",)
}


@pytest.fixture(scope="module")
def operators():
    ans={}
    for mask in range(64):
        edges=[
            DynamicReachabilityEdge(
                source=NODES.index(a),target=NODES.index(b),
                geographic_support=1.0
            )for i,(a,b) in enumerate(BITS) if mask&(1<<i)
        ]
        ans[f"mask_{mask:02d}"]=build_dynamic_transition_operator(
            NODES,edges,loss_support=1.0
        )
    return ans


def known(a,b,status):
    return DeclaredDirectedEdgeEvidence(
        source_id=a,target_id=b,status=status,
        evidence_basis="synthetic_known_truth",
        evidence_ref=f"known-graph-fixture:{a}>{b}:{status}"
    )


def evaluate(operators,*declarations):
    return audit_declared_directed_network_evidence(
        operators,NODES,HYPOTHESES,declarations,max_steps=1
    )


def test_public_and_root_facade_expose_one_implementation():
    assert public is audit_declared_directed_network_evidence
    assert historical is audit_declared_directed_network_evidence


def test_baseline_no_extra_edge_evidence_keeps_all_64_and_three_sources(operators):
    result=evaluate(operators)
    assert isinstance(result,DirectedNetworkEvidenceSourceProjection)
    assert len(result.admitted_rule_ids)==64
    assert len(result.excluded_rule_ids)==0
    assert result.compatible_pairs_before==48
    assert result.compatible_pairs_after==48
    assert result.source_identification_status=="multiple_sources_possible_under_declared_edge_evidence"
    assert result.possible_source_hypotheses_after==(
        "from_A","from_B","from_C"
    )
    assert not result.source_historical_origin_verified
    assert not result.input_structural_edge_truth_independently_verified
    assert result.omitted_species_records_are_NOT_structural_absence_evidence


def test_one_declared_nonedge_excludes_one_source_not_the_other_two(operators):
    result=evaluate(operators,known("A","B","structurally_unavailable"))
    assert len(result.admitted_rule_ids)==32
    assert result.compatible_pairs_after==16
    assert result.after_source_projection is not None
    assert len(set(
        rule for rule,_ in result.after_source_projection.compatible_rule_source_assignments
    ))==14
    assert result.possible_source_hypotheses_after==("from_B","from_C")
    assert result.source_identification_status=="multiple_sources_possible_under_declared_edge_evidence"


def test_two_distinct_source_nonedge_statements_can_isolate_C_without_known_graph(operators):
    result=evaluate(
        operators,
        known("A","B","structurally_unavailable"),
        known("B","A","structurally_unavailable"),
    )
    assert len(result.admitted_rule_ids)==16
    assert len(result.excluded_rule_ids)==48
    assert result.compatible_pairs_after==4
    assert result.after_source_projection is not None
    assert result.after_source_projection.possible_source_hypotheses_after_marginalizing_rule==("from_C",)
    assert result.possible_source_hypotheses_after==("from_C",)
    assert result.source_identification_status=="one_source_supported_within_declared_edge_rule_universe"
    assert not result.source_historical_origin_verified
    assert len(set(r for r,s in result.after_source_projection.compatible_rule_source_assignments))==4
    assert {s for r,s in result.after_source_projection.compatible_rule_source_assignments}=={"from_C"}


def test_two_declared_present_edges_do_not_remove_the_complete_graph_or_identify_source(operators):
    result=evaluate(
        operators,known("A","B","present"),known("B","A","present")
    )
    assert len(result.admitted_rule_ids)==16
    assert result.compatible_pairs_after==20
    assert len(set(
        r for r,_ in result.after_source_projection.compatible_rule_source_assignments
    ))==13
    assert result.possible_source_hypotheses_after==(
        "from_A","from_B","from_C"
    )
    assert "mask_63" in result.admitted_rule_ids
    assert result.source_identification_status=="multiple_sources_possible_under_declared_edge_evidence"


def test_all_six_positive_edge_declarations_still_do_not_identify_a_source(operators):
    result=evaluate(
        operators,*(known(a,b,"present") for a,b in BITS)
    )
    assert result.admitted_rule_ids==("mask_63",)
    assert result.compatible_pairs_after==3
    assert result.possible_source_hypotheses_after==(
        "from_A","from_B","from_C"
    )


def test_two_nonedge_constraints_from_one_source_leave_two_possible_sources(operators):
    result=evaluate(
        operators,
        known("A","B","structurally_unavailable"),
        known("A","C","structurally_unavailable"),
    )
    assert len(result.admitted_rule_ids)==16
    assert result.compatible_pairs_after==8
    assert len(set(
        r for r,_ in result.after_source_projection.compatible_rule_source_assignments
    ))==7
    assert result.possible_source_hypotheses_after==("from_B","from_C")


def test_all_fifteen_two_nonedge_combinations_have_exact_twelve_one_source_cases(operators):
    one_source=[]
    remaining_ambiguous=[]
    for a,b in combinations(BITS,2):
        result=evaluate(
            operators,
            known(*a,"structurally_unavailable"),
            known(*b,"structurally_unavailable")
        )
        if len(result.possible_source_hypotheses_after)==1:
            one_source.append((a,b))
            assert result.compatible_pairs_after==4
        else:
            remaining_ambiguous.append((a,b))
            assert len(result.possible_source_hypotheses_after)==2
            assert result.compatible_pairs_after==8
    assert len(one_source)==12
    assert len(remaining_ambiguous)==3
    assert all(a[0]==b[0] for a,b in remaining_ambiguous)
    assert all(a[0]!=b[0] for a,b in one_source)


def test_no_graph_survives_edge_declarations_is_stop_not_unique_source(operators):
    only_complete={"only_complete":operators["mask_63"]}
    res=evaluate(
        only_complete,known("A","B","structurally_unavailable")
    )
    assert res.admitted_rule_ids==()
    assert res.after_source_projection is None
    assert res.compatible_pairs_after==0
    assert res.source_identification_status=="declared_graph_rule_universe_exhausted"
    assert res.possible_source_hypotheses_after==()


def test_graphs_survive_but_no_source_graph_pair_is_stop(operators):
    res=evaluate(
        operators,*(known(a,b,"structurally_unavailable") for a,b in BITS)
    )
    assert res.admitted_rule_ids==("mask_00",)
    assert res.after_source_projection is not None
    assert res.compatible_pairs_after==0
    assert res.source_identification_status=="declared_graph_source_pair_universe_falsified"
    assert res.possible_source_hypotheses_after==()


def test_canonical_evidence_order_yields_identical_fingerprints(operators):
    a=known("A","B","structurally_unavailable")
    b=known("B","A","structurally_unavailable")
    first=evaluate(operators,a,b)
    second=evaluate(dict(reversed(tuple(operators.items()))),b,a)
    assert first.fingerprint==second.fingerprint
    assert first.admitted_rule_ids==second.admitted_rule_ids
    assert first.after_source_projection.fingerprint==second.after_source_projection.fingerprint


@pytest.mark.parametrize("bad,match",[
    (DeclaredDirectedEdgeEvidence("A","A","structurally_unavailable","synthetic_known_truth","x"),"self-loop"),
    (DeclaredDirectedEdgeEvidence("A","X","present","synthetic_known_truth","x"),"known frozen graph"),
    (DeclaredDirectedEdgeEvidence("A","B","species_nondetection","synthetic_known_truth","x"),"edge status"),
    (DeclaredDirectedEdgeEvidence("A","B","structurally_unavailable","species_nondetection","x"),"species nondetection"),
    (DeclaredDirectedEdgeEvidence("A","B","structurally_unavailable","model_prediction","x"),"species nondetection"),
    (DeclaredDirectedEdgeEvidence("A","B","structurally_unavailable","synthetic_known_truth",""),"nonblank evidence_ref"),
])
def test_illegal_edge_statement_never_silently_becomes_biological_nonedge(operators,bad,match):
    with pytest.raises(ValueError,match=match):
        evaluate(operators,bad)


def test_contradictory_or_duplicate_assertions_fail_closed(operators):
    one=known("A","B","present")
    with pytest.raises(ValueError,match="duplicate or contradictory"):
        evaluate(operators,one,one)
    with pytest.raises(ValueError,match="duplicate or contradictory"):
        evaluate(
            operators,one,known("A","B","structurally_unavailable")
        )
    with pytest.raises(TypeError,match="DeclaredDirectedEdgeEvidence"):
        audit_declared_directed_network_evidence(
            operators,NODES,HYPOTHESES,[{"source_id":"A"}],max_steps=1
        )


def test_external_declaration_is_only_assertion_not_field_verified(operators):
    a=DeclaredDirectedEdgeEvidence(
        source_id="A",target_id="B",
        status="structurally_unavailable",
        evidence_basis="declared_external_structural_assessment",
        evidence_ref="UNVERIFIED_EXTERNAL_ASSUMPTION_TEST_ONLY"
    )
    result=evaluate(operators,a)
    assert result.source_identification_status=="multiple_sources_possible_under_declared_edge_evidence"
    assert not result.input_structural_edge_truth_independently_verified
    assert not result.source_historical_origin_verified
