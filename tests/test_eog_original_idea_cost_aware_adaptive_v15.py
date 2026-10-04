from functools import lru_cache

from benchmarks.run_eog_original_idea_cost_aware_adaptive_v15 import (
    COST_WORLDS,
    _evaluate_row,
)
from benchmarks.run_eog_original_idea_random_relational_v14 import (
    _evaluate_row as evaluate_v14,
)


@lru_cache(maxsize=None)
def _row(active_n=8, replicate=0):
    return _evaluate_row(active_n, replicate)


def test_equal_cost_world_reproduces_v14_and_v13_burdens():
    v15 = _row()
    v14 = evaluate_v14(8, 0)
    for target, spec in v15["cost_worlds"]["equal"]["targets"].items():
        assert spec["fixed_minimum_cost"] == v14["targets"][target]["fixed_minimum_size"]
        assert (
            spec["adaptive_worst_case_cost"]
            == v14["targets"][target]["adaptive_worst_case_depth"]
        )


def test_adaptive_cost_never_exceeds_fixed_cost_in_example_row():
    row = _row()
    for cost_world in COST_WORLDS:
        for spec in row["cost_worlds"][cost_world]["targets"].values():
            assert spec["adaptive_worst_case_cost"] <= spec["fixed_minimum_cost"]


def test_all_cost_worlds_preserve_exact_topology_resolution():
    row = _row()
    for cost_world in COST_WORLDS:
        spec = row["cost_worlds"][cost_world]["targets"]["full_topology_identity"]
        assert spec["fixed_resolvable"] is True
        assert spec["adaptive_resolvable"] is True
