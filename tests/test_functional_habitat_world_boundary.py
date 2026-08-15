import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/functional_habitat_world_boundary.py")
    return namespace["run_functional_habitat_world_boundary"]()


def test_functional_habitat_boundary_records_primary_reference_and_definition():
    boundary = _benchmark()["literature_boundary"]
    assert boundary["method"] == (
        "functional habitat: suitability in E-space plus accessibility in G/T-space"
    )
    assert boundary["reference"] == "Van Moorter et al. 2023, Ecology 104:e4105"
    assert boundary["doi"] == "10.1002/ecy.4105"
    assert boundary["landscape_matrix_definition"] == "m_st = q_s * q_t * k_st"


def test_equal_local_quality_can_have_different_functional_habitat_scores():
    result = _benchmark()
    scores = result["functional_habitat"]["scores_by_world"]
    assert result["local_quality"]["C"] == pytest.approx(1.0)
    assert scores["connected_representation"]["C"] == pytest.approx(2.0)
    assert scores["isolated_representation"]["C"] == pytest.approx(1.0)
    assert result["functional_habitat"][
        "C_same_local_quality_but_different_functionality"
    ] is True


def test_eog_keeps_candidate_C_contingent_across_alternative_analytical_worlds():
    world_set = _benchmark()["eog_world_set"]
    assert set(world_set["compatible_world_ids"]) == {
        "connected_representation",
        "isolated_representation",
    }
    assert world_set["identifiable"] is False
    assert set(world_set["reachable_in_all_ids"]) == {"A", "R"}
    assert world_set["contingent_ids"] == ["C"]
    assert world_set["C_is_contingent"] is True


def test_averaging_functional_habitat_worlds_creates_a_score_in_no_declared_world():
    aggregation = _benchmark()["world_aggregation"]
    assert aggregation["C_functional_scores_in_declared_worlds"] == [1.0, 2.0]
    assert aggregation["C_mean_score_after_collapse"] == pytest.approx(1.5)
    assert aggregation["mean_score_occurs_in_no_declared_world"] is True


def test_suitability_accessibility_integration_is_removed_from_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["suitable_plus_accessible_is_prior_art"] is True
    assert boundary["E_G_T_space_integration_is_not_unique_to_eog"] is True
    assert boundary["isolated_suitable_habitat_downranking_is_not_unique_to_eog"] is True
    assert "mutually alternative ecological/analytical connectivity worlds" in boundary[
        "remaining_eog_question"
    ]
