from benchmarks.run_eog_original_idea_marginal_topology_v10 import (
    _evaluate,
)


def test_static_representation_is_identical_but_topology_differs():
    row = _evaluate(10, 0)
    assert row["static_fingerprint_count"] == 1
    assert row["topology_fingerprint_count"] >= 2


def test_relation_passage_and_intervention_targets_split_static_class():
    row = _evaluate(10, 1)
    assert row["distinct_relation_signature_count"] >= 2
    assert row["distinct_first_passage_signature_count"] >= 2
    assert row["distinct_intervention_signature_count"] >= 2


def test_redundant_world_is_more_single_node_knockout_robust_than_chain():
    row = _evaluate(14, 2)
    assert row["redundant_minus_chain_knockout_retained_fraction"] > 0
