from benchmarks.run_eog_original_idea_history_observability_v22 import (
    SNAPSHOT_TIMES,
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v22 row")


def test_snapshot_library_starts_after_all_sources_are_active():
    assert SNAPSHOT_TIMES == (4, 5, 6, 8)


def test_equilibrium_snapshot_is_identical_across_histories():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert row["designs"][design]["equilibrium_snapshot_identical"] is True


def test_provenance_target_never_has_more_classes_than_full_history():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert row["designs"][design]["provenance_class_count"] <= 3
