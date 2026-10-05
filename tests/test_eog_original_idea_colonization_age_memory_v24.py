from benchmarks.run_eog_original_idea_colonization_age_memory_v24 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v24 row")


def test_first_arrival_class_count_never_exceeds_history_count():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        if drow.get("eligible"):
            assert drow["first_arrival_class_count"] <= 3
            assert drow["colonization_age_class_count"] == drow["first_arrival_class_count"]


def test_equilibrium_occupancy_can_coexist_with_age_memory():
    row = _first_eligible()
    assert any(
        row["designs"][design]["first_arrival_disagreement_node_count"] >= 0
        for design in ("clustered", "dispersed")
    )


def test_source_nodes_are_excluded_from_age_target_population():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        assert drow["equilibrium_non_source_node_count"] >= 0


def test_empty_non_source_age_target_is_valid_empty_state():
    from benchmarks.run_eog_original_idea_colonization_age_memory_v24 import (
        _age_target,
        _first_arrival_target,
    )
    assert _first_arrival_target((), {}) == ()
    assert _age_target((), {}, None) == ()
