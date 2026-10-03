import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.distributional_history import summarize_occurrence_relations
from eog.v2.world_reconstruction import FiniteWorld, reconstruct_compatible_worlds


NODES = ("A", "B", "C")


def _operator(edges):
    index = {node_id: i for i, node_id in enumerate(NODES)}
    return build_dynamic_transition_operator(
        NODES,
        tuple(
            DynamicReachabilityEdge(
                index[source],
                index[target],
                geographic_support=1.0,
            )
            for source, target in edges
        ),
        loss_support=1.0,
    )


def _worlds():
    stepping = FiniteWorld(
        "stepping",
        _operator((("A", "B"), ("B", "C"))),
        ("A",),
    )
    branching = FiniteWorld(
        "branching",
        _operator((("A", "B"), ("A", "C"))),
        ("A",),
    )
    return stepping, branching


def test_occurrence_relations_retain_pairwise_history_uncertainty():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("A", "B", "C"),
        max_steps=2,
    )
    assert reconstruction.compatible_world_ids == ("branching", "stepping")

    graph = summarize_occurrence_relations(reconstruction, worlds)

    a_b = graph.relation("A", "B")
    assert a_b.reachability_status == "reachable_in_all"
    assert a_b.arrival_depth_status == "fixed"
    assert a_b.fixed_first_arrival_step == 1

    a_c = graph.relation("A", "C")
    assert a_c.reachability_status == "reachable_in_all"
    assert a_c.arrival_depth_status == "variable"
    assert a_c.possible_first_arrival_steps == (1, 2)

    b_c = graph.relation("B", "C")
    assert b_c.reachability_status == "contingent"
    assert b_c.arrival_depth_status == "partial"
    assert b_c.supporting_world_count == 1

    c_b = graph.relation("C", "B")
    assert c_b.reachability_status == "robustly_unreachable"
    assert c_b.arrival_depth_status == "undefined"

    assert graph.robust_relation_count == 2
    assert graph.contingent_relation_count == 1
    assert graph.robustly_unreachable_relation_count == 3
    assert graph.arrival_depth_unresolved_relation_count == 2


def test_relation_summary_is_invariant_to_input_world_order():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("A", "B", "C"),
        max_steps=2,
    )
    one = summarize_occurrence_relations(reconstruction, worlds)
    two = summarize_occurrence_relations(
        reconstruction,
        tuple(reversed(worlds)),
    )
    assert one.fingerprint == two.fingerprint
    assert one.relations == two.relations


def test_relation_summary_cannot_add_unconditioned_occurrences():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("A", "C"),
        max_steps=2,
    )
    with pytest.raises(ValueError, match="only use occurrences already conditioned"):
        summarize_occurrence_relations(
            reconstruction,
            worlds,
            occurrence_ids=("A", "B", "C"),
        )
