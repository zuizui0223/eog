from benchmarks.run_eog_original_idea_source_turnover_v20 import (
    STRATEGIES,
    _evaluate_row,
)


def _first_estimable():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"] and all(
            row["designs"][design]["estimable"]
            for design in ("clustered", "dispersed")
        ):
            return row
    raise AssertionError("expected estimable v20 row")


def test_replacement_networks_have_three_unique_sources_and_exclude_lost_source():
    row = _first_estimable()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        for strategy in STRATEGIES:
            srow = drow["replacements"][strategy]
            assert len(srow["source_ids"]) == 3
            assert len(set(srow["source_ids"])) == 3
            assert srow["replacement_source_id"] != drow["lost_source_id"]


def test_worst_source_loss_never_increases_coverage():
    row = _first_estimable()
    for design in ("clustered", "dispersed"):
        drow = row["designs"][design]
        assert (
            drow["post_loss"]["union_reachable_node_count"]
            <= drow["original"]["union_reachable_node_count"]
        )


def test_all_three_replacement_strategies_are_present():
    row = _first_estimable()
    for design in ("clustered", "dispersed"):
        assert set(row["designs"][design]["replacements"]) == set(STRATEGIES)
