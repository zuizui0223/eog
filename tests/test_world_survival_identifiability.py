import numpy as np

from eog.v2.world_survival_identifiability import (
    audit_positive_set_cardinality_exhaustive,
    audit_two_positive_survival_identifiability,
    one_step_positive_set_compatible,
)


def _symmetric(n, edges):
    adjacency = np.zeros((n, n), dtype=bool)
    for left, right in edges:
        adjacency[left, right] = True
        adjacency[right, left] = True
    return adjacency


def test_two_positive_compatibility_is_exactly_pair_adjacency():
    graph = _symmetric(4, [(0, 1), (1, 2)])
    assert one_step_positive_set_compatible(graph, (0, 1)) is True
    assert one_step_positive_set_compatible(graph, (0, 2)) is False


def test_nontrivial_graph_admits_both_survival_outcomes_with_same_positive_count():
    graph = _symmetric(4, [(0, 1), (1, 2)])
    audit = audit_two_positive_survival_identifiability(graph)

    assert audit.compatible_pair_witness is not None
    assert audit.incompatible_pair_witness is not None
    assert audit.both_outcomes_possible_for_two_positives is True
    assert audit.structurally_identifiable_for_two_positives is False

    assert one_step_positive_set_compatible(
        graph, audit.compatible_pair_witness.as_tuple
    )
    assert not one_step_positive_set_compatible(
        graph, audit.incompatible_pair_witness.as_tuple
    )


def test_complete_graph_is_structurally_identifiable_as_survival_for_two_positives():
    graph = np.ones((5, 5), dtype=bool)
    np.fill_diagonal(graph, False)

    audit = audit_two_positive_survival_identifiability(graph)

    assert audit.nonedge_count == 0
    assert audit.structurally_identifiable_for_two_positives is True
    assert audit.structural_outcome_if_identifiable == "survives"


def test_empty_graph_is_structurally_identifiable_as_failure_for_two_positives():
    graph = np.zeros((5, 5), dtype=bool)

    audit = audit_two_positive_survival_identifiability(graph)

    assert audit.edge_count == 0
    assert audit.structurally_identifiable_for_two_positives is True
    assert audit.structural_outcome_if_identifiable == "fails"


def test_same_graph_and_same_three_positive_count_can_still_admit_both_outcomes():
    # Triangle 0-1-2 survives. Set 0-1-3 leaves node 3 isolated and fails.
    graph = _symmetric(5, [(0, 1), (1, 2), (2, 0), (3, 4)])
    audit = audit_positive_set_cardinality_exhaustive(
        graph,
        positive_count=3,
    )

    assert audit.total_configuration_count == 10
    assert audit.compatible_configuration_count > 0
    assert audit.incompatible_configuration_count > 0
    assert audit.both_outcomes_possible is True
    assert audit.compatible_witness is not None
    assert audit.incompatible_witness is not None


def test_exhaustive_cardinality_audit_matches_direct_compatibility():
    graph = _symmetric(4, [(0, 1), (2, 3)])
    audit = audit_positive_set_cardinality_exhaustive(
        graph,
        positive_count=2,
    )

    # Two edge pairs survive; four cross-pairs fail.
    assert audit.compatible_configuration_count == 2
    assert audit.incompatible_configuration_count == 4
    assert audit.total_configuration_count == 6
