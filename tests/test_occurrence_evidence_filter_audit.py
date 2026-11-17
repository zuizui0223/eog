"""Regression tests for the production source-policy-aware EOG filter audit.

These tests are synthetic graph logic, not wetland movement model fits or
observed ecological absence.
"""
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.occurrence_evidence_filter import (
    OccurrenceEvidenceFilterAudit,
    audit_occurrence_evidence_filter,
)
from eog.v2.traversability import (
    audit_occurrence_evidence_filter as public_api,
)
from eog.v2 import audit_occurrence_evidence_filter as historical_export


NODE_IDS = ("A", "B", "C")
EDGE_BITS = (
    ("A", "B"), ("A", "C"), ("B", "A"),
    ("B", "C"), ("C", "A"), ("C", "B")
)


def make_operator(edges, nodes=NODE_IDS):
    return build_dynamic_transition_operator(
        nodes,
        [
            DynamicReachabilityEdge(
                source=nodes.index(a),
                target=nodes.index(b),
                geographic_support=1.0,
            )
            for a,b in edges
        ],
        loss_support=1.0,
    )


def selected_three():
    return {
        "hub": make_operator((
            ("A","C"),("C","A"),("B","C"),("C","B")
        )),
        "isolated_C": make_operator((("A","B"),("B","A"))),
        "complete": make_operator(EDGE_BITS),
    }


def all_64():
    return {
        f"mask_{mask:02d}":make_operator(tuple(
            edge for bit,edge in enumerate(EDGE_BITS) if mask & (1 << bit)
        ))
        for mask in range(64)
    }


def test_public_and_historical_lazy_exports_are_single_actual_implementation():
    assert public_api is audit_occurrence_evidence_filter
    assert historical_export is audit_occurrence_evidence_filter


def test_fixed_source_filter_keeps_declared_source_and_can_only_gain_rules():
    result=audit_occurrence_evidence_filter(
        selected_three(), ("C","A","B"), ("B","A"),
        fixed_source_ids=("A",), max_steps=1
    )
    assert isinstance(result,OccurrenceEvidenceFilterAudit)
    assert result.source_policy=="fixed"
    assert result.full_occurrence_ids==("A","B","C")
    assert result.filtered_occurrence_ids==("A","B")
    assert result.removed_occurrence_ids==("C",)
    assert result.full_compatible_rule_ids==("complete",)
    assert result.filtered_compatible_rule_ids==("complete","isolated_C")
    assert result.shared_compatible_rule_ids==("complete",)
    assert result.lost_compatible_rule_ids==()
    assert result.gained_compatible_rule_ids==("isolated_C",)
    assert result.compatible_sets_nested
    assert result.fixed_source_monotonicity_certified is True
    assert result.changed_retained_target_sources==()
    assert result.membership_change=="expanded"


def test_self_exclusion_reports_both_lost_and_gained_rules_not_count_only():
    result=audit_occurrence_evidence_filter(
        selected_three(), ("A","B","C"), ("A","B"), max_steps=1
    )
    assert result.source_policy=="self_excluded"
    assert result.full_compatible_rule_ids==("complete","hub")
    assert result.filtered_compatible_rule_ids==("complete","isolated_C")
    assert result.shared_compatible_rule_ids==("complete",)
    assert result.lost_compatible_rule_ids==("hub",)
    assert result.gained_compatible_rule_ids==("isolated_C",)
    assert result.membership_change=="swapped"
    assert result.fixed_source_monotonicity_certified is None
    assert not result.compatible_sets_nested
    assert len(result.changed_retained_target_sources)==6
    hub_a=next(x for x in result.changed_retained_target_sources
               if x.rule_id=="hub" and x.target_id=="A")
    assert hub_a.sources_before==("B","C")
    assert hub_a.sources_after==("B",)
    assert hub_a.support_before>0.0
    assert hub_a.support_after==0.0


def test_all_64_native_rules_and_both_source_policies_preserve_exact_membership():
    operators=all_64()
    fixed=audit_occurrence_evidence_filter(
        operators, ("A","B","C"), ("A","B"),
        fixed_source_ids=("A",), max_steps=1
    )
    peer=audit_occurrence_evidence_filter(
        operators, ("A","B","C"), ("A","B"), max_steps=1
    )
    assert (len(fixed.full_compatible_rule_ids),
            len(fixed.filtered_compatible_rule_ids),
            len(fixed.shared_compatible_rule_ids),
            len(fixed.lost_compatible_rule_ids),
            len(fixed.gained_compatible_rule_ids))==(16,32,16,0,16)
    assert (len(peer.full_compatible_rule_ids),
            len(peer.filtered_compatible_rule_ids),
            len(peer.shared_compatible_rule_ids),
            len(peer.lost_compatible_rule_ids),
            len(peer.gained_compatible_rule_ids))==(27,16,12,15,4)
    assert peer.membership_change=="swapped"
    assert not peer.compatible_sets_nested
    assert len(peer.changed_retained_target_sources)==64*2
    assert fixed.changed_retained_target_sources==()
    assert len(peer.operator_fingerprints)==64
    assert fixed.operator_fingerprints==peer.operator_fingerprints
    assert "mask_58" in peer.lost_compatible_rule_ids
    assert "mask_05" in peer.gained_compatible_rule_ids
    assert "mask_63" in peer.shared_compatible_rule_ids


def test_fingerprints_reproducible_and_operator_mapping_order_immaterial():
    rules=selected_three()
    a=audit_occurrence_evidence_filter(
        rules, ("A","B","C"), ("A","B"),max_steps=1
    )
    b=audit_occurrence_evidence_filter(
        dict(reversed(tuple(rules.items()))),
        ("C","A","B"), ("B","A"),max_steps=1
    )
    assert a.fingerprint==b.fingerprint
    assert a.full_comparison_fingerprint==b.full_comparison_fingerprint
    assert a.filtered_comparison_fingerprint==b.filtered_comparison_fingerprint


@pytest.mark.parametrize("full,filtered,match",[
    (("A","B","C"),("A","B","C"),"proper subset"),
    (("A","B","C"),("A","D"),"outside the frozen universe"),
    (("A","B","C"),("A",),">=2 unique"),
    (("A","B"),("A","B"),"proper subset"),
    (("A","B","C"),("A","A"),">=2 unique"),
    (("A","B","C"),("B","D"),"outside the frozen universe"),
    (("A","B","C"),("A","C","X"),"outside the frozen universe"),
])
def test_illegal_occurrence_filters_fail_closed(full,filtered,match):
    with pytest.raises(ValueError,match=match):
        audit_occurrence_evidence_filter(
            selected_three(),full,filtered,max_steps=1
        )


def test_fixed_source_id_removed_or_all_remaining_nodes_sources_fails_closed():
    rules=selected_three()
    with pytest.raises(ValueError,match="may not remove fixed_source_ids"):
        audit_occurrence_evidence_filter(
            rules,("A","B","C"),("B","C"),
            fixed_source_ids=("A",),max_steps=1
        )
    with pytest.raises(ValueError,match="surviving non-source target"):
        audit_occurrence_evidence_filter(
            rules,("A","B","C"),("A","B"),
            fixed_source_ids=("A","B"),max_steps=1
        )


def test_changed_operator_node_universe_and_bad_numeric_contract_fail_closed():
    rules=selected_three()
    rules["changed"]=make_operator((("A","B"),),nodes=("A","B"))
    with pytest.raises(ValueError,match="same node universe"):
        audit_occurrence_evidence_filter(
            rules,("A","B","C"),("A","B"),max_steps=1
        )
    with pytest.raises(ValueError,match="operators"):
        audit_occurrence_evidence_filter(
            {},("A","B","C"),("A","B"),max_steps=1
        )
    with pytest.raises(ValueError,match="max_steps"):
        audit_occurrence_evidence_filter(
            selected_three(),("A","B","C"),("A","B"),max_steps=0
        )
    with pytest.raises(ValueError,match="support_floor"):
        audit_occurrence_evidence_filter(
            selected_three(),("A","B","C"),("A","B"),
            max_steps=1,support_floor=0.0
        )
