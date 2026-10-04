from benchmarks.run_eog_original_idea_random_relational_v14 import (
    _evaluate_row,
)


def test_adaptive_worst_case_never_exceeds_fixed_panel_on_fixture():
    row = _evaluate_row(8, 0)
    for spec in row["targets"].values():
        assert spec["adaptive_resolvable"] is True
        assert spec["adaptive_worst_case_depth"] <= spec["fixed_minimum_size"]


def test_narrow_targets_never_require_more_than_topology_identity():
    row = _evaluate_row(8, 1)
    full = row["targets"]["full_topology_identity"]["adaptive_worst_case_depth"]
    for target in (
        "pairwise_relation",
        "first_passage",
        "intervention",
        "critical_node_count",
    ):
        assert row["targets"][target]["adaptive_worst_case_depth"] <= full


def test_canonical_policy_mean_depth_cannot_exceed_its_worst_case_depth():
    row = _evaluate_row(12, 0)
    for spec in row["targets"].values():
        assert spec["mean_realized_depth"] <= spec["adaptive_worst_case_depth"]
