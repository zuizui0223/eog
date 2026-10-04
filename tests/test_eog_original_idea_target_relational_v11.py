from benchmarks.run_eog_original_idea_target_relational_v11 import (
    _evaluate_row,
)


def test_all_declared_targets_are_resolvable_in_example_row():
    row = _evaluate_row(10, 0)
    assert all(
        target["all_features_sufficient"]
        for target in row["targets"].values()
    )


def test_first_passage_and_intervention_are_coarser_than_full_topology():
    row = _evaluate_row(10, 1)
    assert row["targets"]["first_passage"]["target_class_count"] < 4
    assert row["targets"]["intervention"]["target_class_count"] < 4


def test_minimum_design_is_strictly_smaller_than_full_atomic_library():
    row = _evaluate_row(14, 2)
    for target in ("pairwise_relation", "first_passage", "intervention"):
        assert row["targets"][target]["minimum_size"] < row["atomic_feature_count"]
