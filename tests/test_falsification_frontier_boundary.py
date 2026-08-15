import runpy


def _benchmark():
    namespace = runpy.run_path("benchmarks/falsification_frontier_boundary.py")
    return namespace["run_falsification_frontier_boundary"]()


def test_falsification_frontier_boundary_records_primary_reference_and_scope():
    result = _benchmark()
    boundary = result["literature_boundary"]
    assert boundary["method"] == "falsification frontier / falsification adaptive set"
    assert boundary["reference"] == "Masten & Poirier 2021, Econometrica 89:1449-1469"
    assert boundary["doi"] == "10.3982/ECTA17969"
    assert boundary["prior_art_boundary"] == (
        "smallest relaxations of a falsified baseline model that are not falsified"
    )
    assert "discrete deterministic relaxation vectors" in result[
        "finite_special_case_boundary"
    ]


def test_baseline_is_falsified_and_relaxed_worlds_remain_compatible():
    result = _benchmark()
    assert result["baseline"]["world_id"] == "baseline_fail"
    assert result["baseline"]["relaxation"] == [0.0, 0.0, 0.0]
    assert result["baseline"]["compatible_with_A_C"] is False
    assert set(result["compatible_world_ids"]) == {
        "barrier_rescue",
        "dominated_rescue",
        "env_rescue",
        "geo_rescue",
        "mixed_rescue",
    }


def test_generic_falsification_frontier_matches_eog_minimum_relaxation_frontier():
    result = _benchmark()
    assert result["generic_falsification_frontier"] == result[
        "eog_minimum_relaxation_frontier"
    ]
    assert {row["world_id"] for row in result["generic_falsification_frontier"]} == {
        "geo_rescue",
        "env_rescue",
        "barrier_rescue",
        "mixed_rescue",
    }


def test_dominated_all_axis_rescue_is_removed_from_both_frontiers():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["frontier_world_ids_match"] is True
    assert boundary["frontier_vectors_match"] is True
    assert boundary["dominated_world_removed_by_both"] is True


def test_minimum_relaxation_and_pareto_frontier_math_are_removed_from_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["do_not_claim_minimum_relaxation_frontier_math_as_unique"] is True
    assert boundary["do_not_claim_pareto_rescue_set_as_unique"] is True
    assert "ecological and analyst-choice biogeographic worlds" in boundary[
        "remaining_eog_question"
    ]
