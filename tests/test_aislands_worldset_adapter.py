import runpy

import numpy as np
import pytest

from eog.island_reachability import (
    IslandReachabilityScenario,
    default_aislands_reachability_scenarios,
    evaluate_island_reachability,
)
from eog.prepared_island_connectivity import (
    PreparedIslandConnectivity,
    evaluate_prepared_connectivity,
    prepare_island_connectivity,
)


_NAMESPACE = runpy.run_path("benchmarks/aislands_worldset_adapter.py")
worldset_from_full = _NAMESPACE["worldset_from_full"]
worldset_from_prepared = _NAMESPACE["worldset_from_prepared"]
summarize_worldset = _NAMESPACE["summarize_worldset"]


def _small_graph_fixture():
    node_ids = [f"I{i}" for i in range(8)]
    lat = np.zeros(8)
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
    return node_ids, lat, lon, env, training, scenarios


def test_worldset_recovery_from_prepared_geometry_matches_full_scenario_results():
    node_ids, lat, lon, env, training, scenarios = _small_graph_fixture()
    anchors = np.array([False, False, True, False, True, False, False, False])

    full = evaluate_island_reachability(
        node_ids, lat, lon, env, training, anchors, scenarios
    )
    prepared = prepare_island_connectivity(node_ids, lat, lon, env, training, scenarios)
    fast = evaluate_prepared_connectivity(prepared, anchors)

    full_rows = worldset_from_full(full)
    prepared_rows = worldset_from_prepared(prepared, anchors)

    assert full_rows == prepared_rows
    for index, row in enumerate(prepared_rows):
        assert row["connected_frequency"] == pytest.approx(
            fast.connected_frequency[index]
        )
        assert row["geography_connected_frequency"] == pytest.approx(
            fast.geography_only_connected_frequency[index]
        )
        assert row["environment_connected_frequency"] == pytest.approx(
            fast.environmentally_constrained_connected_frequency[index]
        )


def _default_prepared_worldset_fixture():
    scenarios = default_aislands_reachability_scenarios()
    scenario_ids = tuple(scenario.scenario_id for scenario in scenarios)
    labels = []
    for scenario_id in scenario_ids:
        # Node A is the anchor. R is robust. C is reachable in all geography-only
        # worlds and only q90 environment worlds. E is excluded in every world.
        c_same_component = scenario_id.endswith("env_none") or scenario_id.endswith("env_q90")
        labels.append(
            np.array(
                [
                    0,  # A anchor
                    0,  # R robust
                    0 if c_same_component else 1,
                    2,  # E excluded
                ],
                dtype=int,
            )
        )
    return PreparedIslandConnectivity(
        node_ids=("A", "R", "C", "E"),
        geographic_distance_km=np.zeros((4, 4), dtype=float),
        scenario_ids=scenario_ids,
        component_labels=tuple(labels),
    )


def test_default_twelve_worlds_produce_robust_contingent_and_excluded_classes():
    prepared = _default_prepared_worldset_fixture()
    rows = worldset_from_prepared(prepared, np.array([True, False, False, False]))
    by_node = {row["node_id"]: row for row in rows}

    assert by_node["A"]["world_count"] == 12
    assert by_node["R"]["world_class"] == "robust"
    assert by_node["R"]["support_count"] == 12

    assert by_node["C"]["world_class"] == "contingent"
    assert by_node["C"]["geography_world_class"] == "robust"
    assert by_node["C"]["geography_support_count"] == 4
    assert by_node["C"]["environment_world_class"] == "contingent"
    assert by_node["C"]["environment_support_count"] == 4
    assert by_node["C"]["geo_environment_class_disagreement"] is True

    assert by_node["E"]["world_class"] == "excluded_under_declared_scenarios"
    assert by_node["E"]["support_count"] == 0


def test_worldset_is_invariant_to_scenario_order():
    prepared = _default_prepared_worldset_fixture()
    anchors = np.array([True, False, False, False])
    first = worldset_from_prepared(prepared, anchors)
    reversed_prepared = PreparedIslandConnectivity(
        node_ids=prepared.node_ids,
        geographic_distance_km=prepared.geographic_distance_km,
        scenario_ids=tuple(reversed(prepared.scenario_ids)),
        component_labels=tuple(reversed(prepared.component_labels)),
    )
    second = worldset_from_prepared(reversed_prepared, anchors)
    assert first == second


def test_worldset_summary_keeps_class_and_support_count_information():
    prepared = _default_prepared_worldset_fixture()
    rows = worldset_from_prepared(prepared, np.array([True, False, False, False]))
    summary = summarize_worldset(rows)

    assert summary["n_nodes"] == 4
    assert summary["world_count"] == 12
    assert summary["class_counts"] == {
        "robust": 2,
        "contingent": 1,
        "excluded_under_declared_scenarios": 1,
    }
    assert summary["support_count_distribution"] == {"0": 1, "8": 1, "12": 2}
    assert summary["geo_environment_class_disagreement_count"] == 1
