from benchmarks.run_eog_original_idea_source_placement_v18 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected an eligible v18 row")


def test_nested_source_sets_make_union_reachability_monotone():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        values = [
            row["designs"][design][str(k)]["union_reachable_node_count"]
            for k in (1, 2, 3)
        ]
        assert all(a <= b for a, b in zip(values[:-1], values[1:], strict=True))


def test_nested_source_sets_make_multi_source_count_monotone():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        values = [
            row["designs"][design][str(k)]["multi_source_node_count"]
            for k in (1, 2, 3)
        ]
        assert all(a <= b for a, b in zip(values[:-1], values[1:], strict=True))


def test_one_source_designs_are_identical():
    row = _first_eligible()
    assert (
        row["designs"]["clustered"]["1"]["source_ids"]
        == row["designs"]["dispersed"]["1"]["source_ids"]
    )
    assert (
        row["designs"]["clustered"]["1"]["union_reachable_node_count"]
        == row["designs"]["dispersed"]["1"]["union_reachable_node_count"]
    )
