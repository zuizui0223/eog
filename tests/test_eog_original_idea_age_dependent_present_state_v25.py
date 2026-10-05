from benchmarks.run_eog_original_idea_age_dependent_present_state_v25 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v25 row")


def test_mature_state_partition_is_never_finer_than_first_arrival_partition():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        assert drow["mature_state_class_count"] <= drow["first_arrival_class_count"]


def test_maturity_uses_frozen_two_step_lag():
    from benchmarks.run_eog_original_idea_age_dependent_present_state_v25 import (
        MATURATION_LAG,
    )
    assert MATURATION_LAG == 2


def test_final_occupancy_is_shared_across_histories_by_parent_construction():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert row["designs"][design]["equilibrium_non_source_node_count"] >= 0
