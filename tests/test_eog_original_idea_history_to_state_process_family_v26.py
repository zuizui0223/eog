from benchmarks.run_eog_original_idea_history_to_state_process_family_v26 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v26 row")


def test_history_blind_process_has_one_class():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert (
            row["designs"][design]["process_class_counts"][
                "history_blind_occupancy"
            ]
            == 1
        )


def test_cap3_is_no_finer_than_exact_age_and_no_coarser_than_binary_targets():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        cap3 = drow["process_class_counts"]["saturating_age_class_cap3"]
        assert cap3 <= drow["exact_age_class_count"]
        assert cap3 >= drow["process_class_counts"]["persistent_threshold_lag2"]
        assert cap3 >= drow["process_class_counts"]["transient_window_age1_2"]


def test_process_family_is_exactly_frozen():
    from benchmarks.run_eog_original_idea_history_to_state_process_family_v26 import PROCESS_IDS
    assert PROCESS_IDS == (
        "history_blind_occupancy",
        "persistent_threshold_lag2",
        "transient_window_age1_2",
        "saturating_age_class_cap3",
    )
