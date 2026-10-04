from benchmarks.run_eog_original_idea_random_topology_v12 import (
    _evaluate,
)


def test_random_worlds_share_static_representation_and_keep_multiple_topologies():
    row = _evaluate(12, 0)
    assert row["static_fingerprint_count"] == 1
    assert row["distinct_edge_topology_count"] >= 2


def test_random_worlds_share_the_same_M_mask_but_vary_relational_targets():
    row = _evaluate(12, 1)
    assert row["distinct_relation_target_count"] > 1
    assert row["distinct_first_passage_target_count"] > 1
    assert row["distinct_intervention_target_count"] > 1


def test_target_quotients_are_well_defined():
    row = _evaluate(8, 2)
    assert row["relation_quotient_compression"] >= 1
    assert row["first_passage_quotient_compression"] >= 1
    assert row["intervention_quotient_compression"] >= 1
