import runpy

import pytest


def _matrix():
    namespace = runpy.run_path("benchmarks/finite_world_archetype_matrix.py")
    return namespace["run_archetype_matrix"]()


def test_archetype_matrix_covers_the_declared_finite_core_boundaries():
    result = _matrix()
    assert result["schema_version"] == 1
    assert result["claim_boundary"] == "known-truth structural benchmark; no empirical promotion"
    assert set(result["scenarios"]) == {
        "ibd_dominated",
        "ibe_dominated",
        "barrier_dominated",
        "niche_desert_tradeoff",
        "stepping_stone_reconstructability",
        "rare_long_jump",
        "branch_and_confluence",
        "analytical_ambiguity",
        "robust_exclusion_under_universe_expansion",
    }


def test_ibd_ibe_and_barrier_rescue_axes_remain_separate():
    scenarios = _matrix()["scenarios"]

    ibd = scenarios["ibd_dominated"]
    assert ibd["compatible_world_ids"] == ["geo_relaxed"]
    assert ibd["axis_separated"] is True
    assert ibd["frontier"][0]["geographic_relaxation"] == pytest.approx(1.0)
    assert ibd["frontier"][0]["environmental_relaxation"] == pytest.approx(0.0)
    assert ibd["frontier"][0]["barrier_relaxation"] == pytest.approx(0.0)

    ibe = scenarios["ibe_dominated"]
    assert ibe["compatible_world_ids"] == ["env_relaxed"]
    assert ibe["axis_separated"] is True
    assert ibe["frontier"][0]["geographic_relaxation"] == pytest.approx(0.0)
    assert ibe["frontier"][0]["environmental_relaxation"] == pytest.approx(1.0)
    assert ibe["frontier"][0]["barrier_relaxation"] == pytest.approx(0.0)

    barrier = scenarios["barrier_dominated"]
    assert barrier["compatible_world_ids"] == ["barrier_relaxed"]
    assert barrier["axis_separated"] is True
    assert barrier["frontier"][0]["geographic_relaxation"] == pytest.approx(0.0)
    assert barrier["frontier"][0]["environmental_relaxation"] == pytest.approx(0.0)
    assert barrier["frontier"][0]["barrier_relaxation"] == pytest.approx(1.0)


def test_niche_desert_does_not_get_collapsed_to_one_rescue_story():
    scenario = _matrix()["scenarios"]["niche_desert_tradeoff"]
    assert scenario["compatible_world_ids"] == ["env_rescue", "jump_rescue"]
    assert scenario["alternative_explanations_retained"] is True
    assert {row["world_id"] for row in scenario["frontier"]} == {"env_rescue", "jump_rescue"}

    by_world = {row["world_id"]: row for row in scenario["frontier"]}
    assert by_world["env_rescue"]["environmental_relaxation"] == pytest.approx(1.0)
    assert by_world["env_rescue"]["geographic_relaxation"] == pytest.approx(0.0)
    assert by_world["jump_rescue"]["geographic_relaxation"] == pytest.approx(1.0)
    assert by_world["jump_rescue"]["environmental_relaxation"] == pytest.approx(0.0)


def test_stepping_stone_observation_shrinks_the_world_set_instead_of_rewriting_history():
    scenario = _matrix()["scenarios"]["stepping_stone_reconstructability"]
    assert scenario["before_world_ids"] == ["direct", "stepping"]
    assert scenario["before_identifiable"] is False
    assert scenario["candidate_status"] == "discriminating"
    assert scenario["candidate_reachable_world_ids"] == ["stepping"]
    assert scenario["positive_elimination_fraction"] == pytest.approx(0.5)
    assert scenario["after_world_ids"] == ["stepping"]
    assert scenario["after_identifiable"] is True


def test_rare_long_jump_remains_possible_without_becoming_high_support():
    scenario = _matrix()["scenarios"]["rare_long_jump"]
    assert scenario["compatible"] is True
    assert scenario["support_positive"] is True
    assert scenario["support_below_1e-6"] is True
    assert scenario["treated_as_impossible"] is False


def test_branching_and_reconvergence_are_preserved_by_flow_propagation():
    scenario = _matrix()["scenarios"]["branch_and_confluence"]
    assert scenario["all_declared_branch_edges_used"] is True
    assert scenario["positive_branch_edge_count"] == 4
    assert scenario["confluence_first_arrival_step"] == 2
    assert scenario["target_support_positive"] is True


def test_analytical_ambiguity_separates_possible_from_robust_basin_merge():
    scenario = _matrix()["scenarios"]["analytical_ambiguity"]
    assert scenario["first_possible_level"] == pytest.approx(1.0)
    assert scenario["first_robust_level"] == pytest.approx(2.0)
    assert scenario["possible_but_variant_dependent"] is True
    assert scenario["coverage_certificate"] == "exhaustive_declared_monotone_family_and_variants"


def test_robust_exclusion_survives_a_declared_world_universe_expansion():
    scenario = _matrix()["scenarios"]["robust_exclusion_under_universe_expansion"]
    assert scenario["base_robustly_unreachable_ids"] == ["E"]
    assert scenario["expanded_robustly_unreachable_ids"] == ["E"]
    assert scenario["exclusion_survives_expansion"] is True
    assert scenario["expanded_world_count"] == 3
