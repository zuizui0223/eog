from benchmarks.run_eog_original_idea_random_relational_v13 import (
    _evaluate_row,
)


def test_complete_atomic_library_resolves_declared_target_fixture():
    row = _evaluate_row(8, 0)
    for target, spec in row["targets"].items():
        assert spec["complete_library_sufficient"] is True
        assert spec["minimum_size"] is not None


def test_joint_target_burden_is_not_smaller_than_component_targets():
    row = _evaluate_row(8, 0)
    joint = row["targets"]["joint_relational_suite"]["minimum_size"]
    assert joint >= row["targets"]["pairwise_relation"]["minimum_size"]
    assert joint >= row["targets"]["first_passage"]["minimum_size"]
    assert joint >= row["targets"]["intervention"]["minimum_size"]


def test_exact_minima_are_strictly_smaller_than_full_atomic_library_fixture():
    row = _evaluate_row(8, 0)
    for target in (
        "pairwise_relation",
        "first_passage",
        "intervention",
        "critical_node_count",
    ):
        assert row["targets"][target]["minimum_size"] < row["atomic_feature_count"]
