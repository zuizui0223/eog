from benchmarks.run_eog_original_idea_expansion_direction_v7 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"] and row["universes"]:
            return row
    raise AssertionError("expected eligible v7 row")


def test_restrictive_expansion_never_breaks_baseline_impossibility():
    row = _first_eligible()
    assert row["restrictive_impossible_protection_violation_count"] == 0


def test_permissive_expansion_never_breaks_baseline_reachability():
    row = _first_eligible()
    assert row["permissive_reachable_protection_violation_count"] == 0


def test_same_source_and_all_source_universes_are_nested():
    row = _first_eligible()
    same = row["universes"]["B_same_source_full"]["world_count"]
    full = row["universes"]["B_all_source_full"]["world_count"]
    assert same <= full
