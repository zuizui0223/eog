import runpy


def _benchmark():
    namespace = runpy.run_path("benchmarks/dynamic_connectivity_negative_boundary.py")
    return namespace["run_dynamic_connectivity_negative_boundary"]()


def test_dynamic_connectivity_benchmark_is_explicitly_a_negative_novelty_boundary():
    result = _benchmark()
    assert result["schema_version"] == 1
    assert result["claim_boundary"] == (
        "negative novelty boundary: structural dynamic reachability and positive temporal "
        "filtering are reproducible by time-respecting Boolean connectivity"
    )


def test_boolean_time_respecting_reachability_matches_eog_structural_reachability():
    result = _benchmark()
    assert result["all_forward_reachability_equal"] is True
    assert set(result["scenario_equivalence"]) == {
        "ordered",
        "reversed",
        "branch_confluence",
        "low_positive_direct",
    }
    for scenario in result["scenario_equivalence"].values():
        assert scenario["exact_structural_equivalence"] is True
        assert scenario["boolean_reached_by_time"] == scenario["eog_reached_by_time"]


def test_positive_temporal_world_filter_is_also_reproducible_by_boolean_connectivity():
    result = _benchmark()["positive_observation_filter"]
    assert result["observations"] == [["C", "t2"]]
    assert result["boolean_compatible_world_ids"] == ["ordered"]
    assert result["eog_compatible_world_ids"] == ["ordered"]
    assert result["boolean_incompatible_world_ids"] == ["reversed"]
    assert result["eog_incompatible_world_ids"] == ["reversed"]
    assert result["exact_filter_equivalence"] is True


def test_forward_dynamic_reachability_is_removed_from_the_eog_novelty_claim():
    boundary = _benchmark()["novelty_boundary"]
    assert boundary["do_not_claim_forward_dynamic_reachability_as_unique"] is True
    assert boundary["do_not_claim_positive_world_filtering_as_unique"] is True
    assert "axis-preserving occurrence-conditioned minimum-relaxation frontiers" in boundary[
        "remaining_eog_layers_to_validate"
    ]
    assert "finite-universe robust/contingent/excluded certificates and monotonicity" in boundary[
        "remaining_eog_layers_to_validate"
    ]
