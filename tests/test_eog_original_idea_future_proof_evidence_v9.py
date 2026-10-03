from benchmarks.run_eog_original_idea_future_proof_evidence_v9 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"] and row["actions"]:
            return row
    raise AssertionError("expected eligible v9 row")


def test_truth_consistent_action_never_eliminates_truth_baseline():
    row = _first_eligible()
    assert row["lifetime_violation_count"] == 0
    for action in ("S_source", "B_barrier", "R_analyst"):
        assert row["actions"][action]["current_B0_world_count_after"] >= 1


def test_barrier_and_rule_have_zero_current_B0_contraction_by_construction():
    row = _first_eligible()
    assert row["actions"]["B_barrier"]["current_contraction_fraction"] == 0
    assert row["actions"]["R_analyst"]["current_contraction_fraction"] == 0


def test_future_lifetime_is_bounded():
    row = _first_eligible()
    for action in ("S_source", "B_barrier", "R_analyst"):
        value = row["actions"][action]["mean_future_lifetime_after"]
        assert 0 <= value <= 1
