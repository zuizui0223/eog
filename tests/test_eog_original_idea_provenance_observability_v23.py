from benchmarks.run_eog_original_idea_provenance_observability_v23 import (
    _evaluate_row,
    _minimum_action_design,
)


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected eligible v23 row")


def test_exact_action_cover_resolves_two_discordant_pairs_with_one_action_when_possible():
    actions = {
        "a": {"h1": 0, "h2": 1, "h3": 2},
        "b": {"h1": 0, "h2": 0, "h3": 1},
    }
    target = {"h1": "x", "h2": "y", "h3": "z"}
    plan = _minimum_action_design(actions, target)
    assert plan["identified"] is True
    assert plan["minimum_size"] == 1
    assert plan["minimum_action_ids"] == ("a",)


def test_unique_origin_provenance_actions_are_history_invariant():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        assert (
            row["designs"][design][
                "informative_unique_origin_provenance_action_count"
            ]
            == 0
        )


def test_provenance_target_never_harder_in_fixture_row():
    row = _first_eligible()
    for design in ("clustered", "dispersed"):
        for library in ("occupancy_only", "provenance_only", "combined"):
            full = row["designs"][design]["plans"][library]["full_history"]
            prov = row["designs"][design]["plans"][library]["provenance_class"]
            full_size = float("inf") if full["minimum_size"] is None else full["minimum_size"]
            prov_size = float("inf") if prov["minimum_size"] is None else prov["minimum_size"]
            assert prov_size <= full_size
