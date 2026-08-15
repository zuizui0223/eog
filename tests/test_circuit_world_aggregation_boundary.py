import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/circuit_world_aggregation_boundary.py")
    return namespace["run_circuit_world_aggregation_boundary"]()


def test_circuit_boundary_records_primary_reference_and_prior_art_scope():
    boundary = _benchmark()["literature_boundary"]
    assert boundary["method"] == "circuit-theoretic ecological connectivity"
    assert boundary["reference"] == "McRae et al. 2008, Ecology 89:2712-2724"
    assert boundary["doi"] == "10.1890/07-1861.1"
    assert boundary["prior_art_boundary"] == (
        "integration of contributions from multiple dispersal pathways"
    )


def test_each_declared_world_has_one_path_and_resistance_two():
    result = _benchmark()["within_world_connectivity"]
    assert result["world_B_bridge"]["minimum_path"] == ["A", "B", "C"]
    assert result["world_D_bridge"]["minimum_path"] == ["A", "D", "C"]
    assert result["world_B_bridge"]["edge_disjoint_path_count"] == 1
    assert result["world_D_bridge"]["edge_disjoint_path_count"] == 1
    assert result["world_B_effective_resistance"] == pytest.approx(2.0)
    assert result["world_D_effective_resistance"] == pytest.approx(2.0)


def test_union_graph_has_parallel_redundancy_that_no_world_contains():
    result = _benchmark()
    union = result["incorrect_world_union"]
    boundary = result["negative_boundary"]

    assert union["bridge"]["edge_disjoint_path_count"] == 2
    assert union["effective_resistance"] == pytest.approx(1.0)
    assert union["no_individual_world_contains_union_graph"] is True
    assert boundary["parallel_paths_reduce_effective_resistance"] is True
    assert boundary["aggregate_graph_manufactures_redundancy"] is True


def test_eog_world_set_keeps_alternative_corridors_separate_and_underidentified():
    worlds = _benchmark()["declared_worlds"]
    assert set(worlds["compatible_world_ids"]) == {"world_B", "world_D"}
    assert worlds["identifiable"] is False
    assert set(worlds["contingent_node_ids"]) == {"B", "D"}
    assert worlds["worlds_remain_separate"] is True


def test_multiple_paths_and_route_redundancy_are_removed_from_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["multiple_pathways_are_prior_art"] is True
    assert boundary["route_redundancy_is_not_unique_to_eog"] is True
    assert boundary["remaining_eog_question"] == (
        "whether alternative ecological/analytical world representations may be "
        "aggregated before connectivity inference, or must remain world-indexed"
    )
