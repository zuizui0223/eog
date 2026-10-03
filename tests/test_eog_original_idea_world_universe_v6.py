from benchmarks.run_eog_original_idea_world_universe_v6 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"] and row["levels"]:
            return row
    raise AssertionError("expected eligible v6 row")


def test_candidate_universes_are_nested_in_size():
    row = _first_eligible()
    counts = [
        row["levels"][level]["candidate_world_count"]
        for level in ("U0_source_only", "U1_plus_barrier", "U2_plus_analyst")
    ]
    assert counts[0] <= counts[1] <= counts[2]


def test_world_expansion_does_not_create_false_universal_certificates():
    row = _first_eligible()
    for level in ("U0_source_only", "U1_plus_barrier", "U2_plus_analyst"):
        assert row["levels"][level]["false_robust_impossible_count"] == 0
        assert row["levels"][level]["false_robust_reachable_count"] == 0


def test_universe_expansion_only_erodes_or_preserves_certificates():
    row = _first_eligible()
    assert row["monotonicity_violation_count"] == 0
