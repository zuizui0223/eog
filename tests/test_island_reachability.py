import numpy as np

from eog.island_reachability import (
    IslandReachabilityScenario,
    default_aislands_reachability_scenarios,
    evaluate_island_reachability,
)


def test_default_scenario_family_is_frozen_and_complete():
    scenarios = default_aislands_reachability_scenarios()
    assert len(scenarios) == 12
    assert {scenario.max_geographic_km for scenario in scenarios} == {25.0, 50.0, 125.0, 250.0}
    assert {scenario.environmental_edge_quantile for scenario in scenarios} == {None, 0.90, 0.75}
    assert len({scenario.scenario_id for scenario in scenarios}) == 12


def test_unlabelled_stepping_stone_changes_structure_beyond_nearest_anchor_distance():
    # Approx. longitude distances at the equator: A->X and X->T_chain ~20 km;
    # A->T_isolated is also ~40 km direct but has no intermediate island.
    node_ids = ["anchor", "step", "target_chain", "target_isolated", "train_far"]
    lat = [0.0, 0.0, 0.0, 0.36, 2.0]
    lon = [0.0, 0.18, 0.36, 0.0, 2.0]
    env = np.array([
        [0.0, 0.0],
        [0.0, 0.1],
        [0.0, 0.2],
        [0.0, 0.2],
        [0.2, 0.0],
    ])
    training = [True, True, False, False, True]
    anchors = [True, False, False, False, False]
    scenario = [IslandReachabilityScenario("r25", 25.0, None)]
    result = evaluate_island_reachability(node_ids, lat, lon, env, training, anchors, scenario)
    chain = node_ids.index("target_chain")
    isolated = node_ids.index("target_isolated")
    assert abs(result.nearest_anchor_distance_km[chain] - result.nearest_anchor_distance_km[isolated]) < 1.0
    assert result.connected_frequency[chain] == 1.0
    assert result.connected_frequency[isolated] == 0.0


def test_environmental_threshold_is_derived_from_training_edges_only():
    node_ids = ["a", "b", "c", "held"]
    lat = [0.0, 0.0, 0.0, 0.0]
    lon = [0.0, 0.1, 0.2, 0.3]
    training = [True, True, True, False]
    anchors = [True, False, False, False]
    scenario = [IslandReachabilityScenario("env", 100.0, 0.75)]
    base_env = np.array([[0.0], [1.0], [2.0], [3.0]])
    extreme_env = np.array([[0.0], [1.0], [2.0], [3000.0]])
    base = evaluate_island_reachability(node_ids, lat, lon, base_env, training, anchors, scenario)
    extreme = evaluate_island_reachability(node_ids, lat, lon, extreme_env, training, anchors, scenario)
    assert base.scenarios[0].environmental_threshold == extreme.scenarios[0].environmental_threshold


def test_anchor_must_be_training_island():
    node_ids = ["a", "b", "c"]
    lat = [0.0, 0.0, 0.0]
    lon = [0.0, 0.1, 0.2]
    env = np.array([[0.0], [1.0], [2.0]])
    try:
        evaluate_island_reachability(
            node_ids,
            lat,
            lon,
            env,
            training_mask=[True, True, False],
            anchor_mask=[False, False, True],
            scenarios=[IslandReachabilityScenario("r", 100.0, None)],
        )
    except ValueError as exc:
        assert "training islands" in str(exc)
    else:
        raise AssertionError("held-out anchor was not rejected")
