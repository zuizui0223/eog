from benchmarks.run_eog_original_idea_source_history_memory_v21 import (
    ACTIVATION_HISTORIES,
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v21 row")


def test_histories_use_same_source_set_and_activation_time_multiset():
    row = _first_eligible()
    assert set(ACTIVATION_HISTORIES) == {
        "H_anchor_first",
        "H_second_first",
        "H_third_first",
    }
    assert all(
        sorted(times) == [0, 2, 4]
        for times in ACTIVATION_HISTORIES.values()
    )
    for design in ("clustered", "dispersed"):
        assert len(row["designs"][design]["source_ids"]) == 3


def test_equilibrium_occupancy_is_identical_across_histories():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert (
            row["designs"][design][
                "equilibrium_occupancy_equal_across_histories"
            ]
            is True
        )


def test_provenance_disagreement_fraction_is_bounded():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        value = row["designs"][design]["provenance_disagreement_fraction"]
        assert 0.0 <= value <= 1.0
