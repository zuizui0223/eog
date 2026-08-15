import runpy


def _benchmark():
    namespace = runpy.run_path("benchmarks/bridge_vs_temporal_reconstruction.py")
    return namespace["run_bridge_temporal_comparator"]()


def test_bridge_temporal_comparator_has_no_superiority_claim():
    result = _benchmark()
    assert result["schema_version"] == 1
    assert result["claim_boundary"] == (
        "known-truth static-connectivity vs temporal-realizability estimand separation; "
        "not method superiority"
    )


def test_ordered_and_reversed_worlds_have_the_same_time_aggregated_graph():
    graph = _benchmark()["time_aggregated_graph"]
    assert graph["ordered_edges"] == [["A", "B"], ["B", "C"]]
    assert graph["reversed_edges"] == [["A", "B"], ["B", "C"]]
    assert graph["identical_static_edge_set"] is True


def test_existing_bridge_operator_correctly_recovers_the_static_path():
    bridge = _benchmark()["static_bridge"]
    assert bridge["minimum_cost_nodes"] == [0, 1, 2]
    assert bridge["minimum_cost"] == 2.0
    assert bridge["minimum_bottleneck"] == 1.0
    assert bridge["geographic_cost"] == 2.0
    assert bridge["environmental_cost"] == 0.0
    assert bridge["barrier_cost"] == 0.0
    assert bridge["edge_disjoint_path_count"] == 1


def test_temporal_positive_observation_distinguishes_edge_order_that_static_bridge_cannot():
    temporal = _benchmark()["temporal_inverse"]
    checks = _benchmark()["separation_checks"]

    assert temporal["compatible_world_ids"] == ["ordered"]
    assert temporal["incompatible_world_ids"] == ["reversed"]
    assert temporal["reversed_unsupported_observations"] == [["C", "t2"]]
    assert temporal["identifiable_with_C_t2"] is True
    assert checks["static_bridge_is_well_defined"] is True
    assert checks["static_graph_cannot_encode_edge_order"] is True
    assert checks["temporal_order_changes_realizability"] is True
    assert checks["bridge_and_temporal_inverse_answer_different_questions"] is True
