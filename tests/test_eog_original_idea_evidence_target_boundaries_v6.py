from benchmarks.run_eog_original_idea_evidence_target_boundaries_v6 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected at least one v6 eligible row")


def test_target_burden_cannot_exceed_world_burden():
    row = _first_eligible()
    assert (
        row["minimum_reachability_target_burden"]
        <= row["minimum_full_world_burden"]
    )


def test_direct_source_barrier_rule_identifies_truth_world():
    row = _first_eligible()
    assert row["subsets"]["S_source+B_barrier+R_analyst"][
        "truth_world_identified"
    ] is True


def test_single_channel_classification_is_from_frozen_vocabulary():
    row = _first_eligible()
    allowed = {
        "redundant",
        "identity_only",
        "target_refining",
        "envelope_changing",
    }
    assert {
        item["classification"]
        for item in row["single_channels"].values()
    }.issubset(allowed)
