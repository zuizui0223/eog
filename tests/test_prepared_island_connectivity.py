import numpy as np

from eog.island_reachability import (
    IslandReachabilityScenario,
    evaluate_island_reachability,
)
from eog.prepared_island_connectivity import (
    evaluate_prepared_connectivity,
    prepare_island_connectivity,
)


def test_prepared_connectivity_matches_full_graph_for_primary_fields():
    node_ids = [f"I{i}" for i in range(8)]
    lat = np.zeros(8)
    # Roughly 11 km per 0.1 degree at the equator; create chains and gaps.
    lon = np.array([0.0, 0.1, 0.2, 0.4, 0.5, 0.9, 1.0, 1.1])
    env = np.column_stack(
        [
            np.linspace(-1.0, 1.0, 8),
            np.array([0.0, 0.1, 0.2, 0.3, 1.2, 1.3, 1.4, 1.5]),
        ]
    )
    training = np.array([True, True, True, True, True, False, False, False])
    scenarios = (
        IslandReachabilityScenario("g20_env_none", 20.0, None),
        IslandReachabilityScenario("g50_env_none", 50.0, None),
        IslandReachabilityScenario("g50_env_q90", 50.0, 0.90),
        IslandReachabilityScenario("g50_env_q75", 50.0, 0.75),
    )
    prepared = prepare_island_connectivity(node_ids, lat, lon, env, training, scenarios)

    for anchors in (
        np.array([True, False, False, False, False, False, False, False]),
        np.array([False, False, True, False, True, False, False, False]),
    ):
        full = evaluate_island_reachability(
            node_ids, lat, lon, env, training, anchors, scenarios
        )
        fast = evaluate_prepared_connectivity(prepared, anchors)
        assert np.allclose(
            fast.nearest_anchor_distance_km, full.nearest_anchor_distance_km
        )
        assert np.allclose(fast.connected_frequency, full.connected_frequency)
        assert np.allclose(
            fast.geography_only_connected_frequency,
            full.geography_only_connected_frequency,
        )
        assert np.allclose(
            fast.environmentally_constrained_connected_frequency,
            full.environmentally_constrained_connected_frequency,
        )
