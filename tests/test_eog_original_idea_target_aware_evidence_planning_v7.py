from benchmarks.run_eog_original_idea_target_aware_evidence_planning_v7 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected one v7 eligible row")


def test_target_depth_never_exceeds_world_depth():
    row = _first_eligible()
    assert (
        row["target_optimal_worst_case_depth"]
        <= row["world_optimal_worst_case_depth"]
    )


def test_target_truth_path_stops_at_one_target_class():
    row = _first_eligible()
    assert row["target_truth_path"]["final_target_class_count"] == 1


def test_action_scores_cover_all_three_frozen_actions_when_target_unresolved():
    row = _first_eligible()
    if not row["target_already_identified"]:
        assert set(row["first_action_worst_case_target_class_counts"]) == {
            "S_source",
            "B_barrier",
            "R_analyst",
        }
