from benchmarks.run_eog_original_idea_source_confluence_v19 import (
    _evaluate_row,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v19 row")


def test_earliest_origin_is_never_outside_static_origin_set():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        for k in ("2", "3"):
            assert (
                row["designs"][design][k][
                    "earliest_origin_subset_violation_count"
                ]
                == 0
            )


def test_adding_source_does_not_reduce_static_ambiguous_node_count():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert (
            row["designs"][design]["2"]["static_ambiguous_node_count"]
            <= row["designs"][design]["3"]["static_ambiguous_node_count"]
        )


def test_residual_first_passage_ambiguity_is_subset_of_static_ambiguity():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        for k in ("2", "3"):
            metrics = row["designs"][design][k]
            assert (
                metrics["residual_ambiguous_node_count"]
                <= metrics["static_ambiguous_node_count"]
            )
