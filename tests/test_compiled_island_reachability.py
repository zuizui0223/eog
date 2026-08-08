import numpy as np

from eog.compiled_island_reachability import (
    compile_island_reachability_fold,
    evaluate_compiled_anchor_reachability,
)
from eog.island_reachability import (
    IslandReachabilityScenario,
    evaluate_island_reachability,
)


def test_compiled_components_match_direct_reachability_exactly():
    node_ids = [f"n{i}" for i in range(8)]
    lat = [0.0, 0.0, 0.0, 0.0, 0.2, 0.4, 0.6, 1.0]
    lon = [0.0, 0.1, 0.2, 0.4, 0.4, 0.4, 0.4, 1.0]
    env = np.array([
        [0.0, 0.0],
        [0.1, 0.0],
        [0.2, 0.1],
        [0.3, 0.2],
        [0.4, 0.3],
        [0.5, 0.4],
        [0.6, 0.5],
        [1.5, 1.5],
    ])
    training = np.array([True, True, True, True, True, False, False, False])
    anchors = np.array([True, False, True, False, False, False, False, False])
    scenarios = [
        IslandReachabilityScenario("g25", 25.0, None),
        IslandReachabilityScenario("g50", 50.0, None),
        IslandReachabilityScenario("g50_q90", 50.0, 0.90),
        IslandReachabilityScenario("g125_q75", 125.0, 0.75),
    ]

    direct = evaluate_island_reachability(
        node_ids,
        lat,
        lon,
        env,
        training,
        anchors,
        scenarios,
    )
    compiled = compile_island_reachability_fold(
        node_ids,
        lat,
        lon,
        env,
        training,
        scenarios,
    )
    fast = evaluate_compiled_anchor_reachability(compiled, anchors)

    assert np.allclose(fast.nearest_anchor_distance_km, direct.nearest_anchor_distance_km)
    assert np.allclose(fast.connected_frequency, direct.connected_frequency)
    assert np.allclose(
        fast.geography_only_connected_frequency,
        direct.geography_only_connected_frequency,
    )
    assert np.allclose(
        fast.environmentally_constrained_connected_frequency,
        direct.environmentally_constrained_connected_frequency,
    )
    for index, scenario in enumerate(direct.scenarios):
        assert np.array_equal(fast.scenario_reachable[index], scenario.reachable)


def test_compiled_species_evaluation_rejects_heldout_anchor():
    compiled = compile_island_reachability_fold(
        ["a", "b", "c"],
        [0.0, 0.0, 0.0],
        [0.0, 0.1, 0.2],
        np.array([[0.0], [1.0], [2.0]]),
        [True, True, False],
        [IslandReachabilityScenario("g", 100.0, None)],
    )
    try:
        evaluate_compiled_anchor_reachability(compiled, [False, False, True])
    except ValueError as exc:
        assert "training islands" in str(exc)
    else:
        raise AssertionError("held-out anchor was not rejected")
