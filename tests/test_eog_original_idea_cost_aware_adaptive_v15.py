from benchmarks.run_eog_original_idea_cost_aware_adaptive_v15 import (
    COST_WORLDS,
    _evaluate_row,
)


def test_equal_cost_world_reproduces_unit_cost_information_counts():
    row = _evaluate_row(8, 0)
    for target, spec in row["cost_worlds"]["equal"]["targets"].items():
        assert spec["fixed_minimum_cost"] is not None
        assert spec["adaptive_worst_case_cost"] is not None


def test_adaptive_cost_never_exceeds_fixed_cost_in_example_row():
    row = _evaluate_row(12, 1)
    for cost_world in COST_WORLDS:
        for spec in row["cost_worlds"][cost_world]["targets"].values():
            assert spec["adaptive_worst_case_cost"] <= spec["fixed_minimum_cost"]


def test_all_cost_worlds_preserve_exact_topology_resolution():
    row = _evaluate_row(16, 2)
    for cost_world in COST_WORLDS:
        spec = row["cost_worlds"][cost_world]["targets"]["full_topology_identity"]
        assert spec["fixed_resolvable"] is True
        assert spec["adaptive_resolvable"] is True
