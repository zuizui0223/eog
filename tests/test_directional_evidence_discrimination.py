import pytest

from eog.v2 import (
    DirectionalOrderConstraint,
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    combine_occurrence_and_directional_evidence,
    compare_occurrence_transition_rules,
    evaluate_directional_order_evidence,
)


NODE_IDS = ("A", "B", "C", "D")
CONSTRAINTS = (
    DirectionalOrderConstraint("A", "B", "order_ab"),
    DirectionalOrderConstraint("B", "C", "order_bc"),
    DirectionalOrderConstraint("C", "D", "order_cd"),
)


def _true_chain():
    return build_dynamic_transition_operator(
        NODE_IDS,
        [
            DynamicReachabilityEdge(0, 1, geographic_support=0.75),
            DynamicReachabilityEdge(1, 2, geographic_support=0.75),
            DynamicReachabilityEdge(2, 3, geographic_support=0.75),
        ],
        loss_support=0.5,
    )


def _symmetric_permissive():
    return build_dynamic_transition_operator(
        NODE_IDS,
        [
            DynamicReachabilityEdge(i, j, geographic_support=0.75)
            for i in range(4)
            for j in range(4)
            if i != j
        ],
        loss_support=0.5,
    )


def _reverse_dominant_chain():
    edges = []
    for i in range(3):
        edges.append(DynamicReachabilityEdge(i, i + 1, geographic_support=0.05))
        edges.append(DynamicReachabilityEdge(i + 1, i, geographic_support=0.90))
    return build_dynamic_transition_operator(NODE_IDS, edges, loss_support=0.5)


def test_directional_evidence_supports_true_one_way_chain():
    evidence = evaluate_directional_order_evidence(
        _true_chain(),
        CONSTRAINTS,
        rule_id="true_chain",
        max_steps=3,
        minimum_support_ratio=2.0,
    )
    assert evidence.supports_count == 3
    assert evidence.contradicts_count == 0
    assert evidence.ambiguous_count == 0
    assert evidence.unresolved_count == 0
    assert all(row.status == "supports_declared_direction" for row in evidence.rows)


def test_symmetric_rule_remains_ambiguous_instead_of_being_selected():
    evidence = evaluate_directional_order_evidence(
        _symmetric_permissive(),
        CONSTRAINTS,
        rule_id="permissive",
        max_steps=3,
        minimum_support_ratio=2.0,
    )
    assert evidence.supports_count == 0
    assert evidence.contradicts_count == 0
    assert evidence.ambiguous_count == 3
    assert all(row.log_support_ratio == pytest.approx(0.0) for row in evidence.rows)


def test_reverse_dominant_rule_is_contradicted_despite_occurrence_coverage():
    evidence = evaluate_directional_order_evidence(
        _reverse_dominant_chain(),
        CONSTRAINTS,
        rule_id="reverse_dominant",
        max_steps=3,
        minimum_support_ratio=2.0,
    )
    assert evidence.contradicts_count == 3
    assert all(row.status == "contradicts_declared_direction" for row in evidence.rows)


def test_combination_uses_statuses_not_a_winner_score():
    operators = {
        "true_chain": _true_chain(),
        "permissive": _symmetric_permissive(),
        "reverse_dominant": _reverse_dominant_chain(),
    }
    occurrence = compare_occurrence_transition_rules(
        operators,
        NODE_IDS,
        fixed_source_ids=["A"],
        max_steps=3,
    )
    directional = {
        rule_id: evaluate_directional_order_evidence(
            operator,
            CONSTRAINTS,
            rule_id=rule_id,
            max_steps=3,
            minimum_support_ratio=2.0,
        )
        for rule_id, operator in operators.items()
    }
    combined = combine_occurrence_and_directional_evidence(occurrence, directional)
    statuses = {row.rule_id: row.status for row in combined.rule_statuses}

    assert all(result.coverage_fraction == 1.0 for result in occurrence.rule_results)
    assert statuses == {
        "permissive": "indistinguishable_directional_evidence",
        "reverse_dominant": "contradicted_by_directional_evidence",
        "true_chain": "compatible_with_occurrence_and_direction",
    }
    assert not hasattr(combined, "winner")
    assert not hasattr(combined, "score")


def test_directional_resolution_ratio_must_be_declared_above_one():
    with pytest.raises(ValueError, match="> 1"):
        evaluate_directional_order_evidence(
            _true_chain(),
            CONSTRAINTS,
            rule_id="bad-threshold",
            max_steps=3,
            minimum_support_ratio=1.0,
        )
