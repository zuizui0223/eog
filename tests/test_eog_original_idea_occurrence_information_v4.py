from benchmarks.run_eog_original_idea_occurrence_information_v4 import (
    _candidate_worlds,
    _evaluate_row,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _generate_base


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected at least one eligible frozen row")


def test_candidate_universe_is_source_x_barrier_x_analyst_cartesian_product():
    base = _generate_base(0, "low", "rook")
    worlds = _candidate_worlds(base)
    assert len(worlds) == len(base["permissive"]) * 3 * 3


def test_nested_occurrence_evidence_never_increases_survivor_count():
    row = _first_eligible()
    for design in ("clustered_near_source", "dispersed_farthest_first"):
        counts = [
            row["designs"][design][key]["survivor_world_count"]
            for key in ("0.10", "0.25", "0.50", "1.00")
        ]
        assert all(a >= b for a, b in zip(counts[:-1], counts[1:], strict=True))


def test_truth_world_prevents_false_robust_exclusion():
    row = _first_eligible()
    for design in ("clustered_near_source", "dispersed_farthest_first"):
        for key in ("0.10", "0.25", "0.50", "1.00"):
            assert (
                row["designs"][design][key]["false_robust_exclusion_count"] == 0
            )
            assert row["designs"][design][key]["truth_world_survives"] is True
