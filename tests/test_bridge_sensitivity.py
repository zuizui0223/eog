import numpy as np
import pytest

from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    BridgeSensitivityScenario,
    BridgeWeights,
    evaluate_bridge_sensitivity,
    fit_robust_reference,
)


def node(node_id, lon, env, *, lat=0.0):
    return BridgeNode(node_id, lat, lon, tuple(env))


def reference():
    return fit_robust_reference(
        np.array([[-2.0], [-1.0], [0.0], [1.0], [2.0]]),
        provenance="sensitivity-test",
    )


def test_connected_frequency_keeps_disconnected_scenarios_in_denominator():
    nodes = [
        node("source", 0.0, [0.0]),
        node("middle", 1.0, [0.1]),
        node("target", 2.0, [0.0]),
    ]
    scenarios = [
        BridgeSensitivityScenario(
            "radius",
            BridgeGraphDeclaration(max_geographic_km=120.0),
        ),
        BridgeSensitivityScenario(
            "knn",
            BridgeGraphDeclaration(k_nearest=1, max_geographic_km=150.0),
        ),
        BridgeSensitivityScenario(
            "disconnected",
            BridgeGraphDeclaration(max_geographic_km=50.0),
        ),
    ]
    result = evaluate_bridge_sensitivity(nodes, reference(), scenarios, "source", "target")
    assert result.scenario_count == 3
    assert result.connected_count == 2
    assert result.connected_frequency == pytest.approx(2 / 3)
    assert result.minimum_cost_node_support == {"middle": 1.0}
    failed = next(item for item in result.scenarios if item.scenario_id == "disconnected")
    assert not failed.connected
    assert "disconnected" in failed.failure_reason


def test_direct_barrier_creates_positive_bridge_gain():
    nodes = [
        node("source", 0.0, [0.0]),
        node("middle", 1.0, [0.0]),
        node("target", 2.0, [0.0]),
    ]
    scenario = BridgeSensitivityScenario(
        "barrier-direct",
        BridgeGraphDeclaration(max_geographic_km=250.0),
        weights=BridgeWeights(geographic=0.0, environmental=0.0, barrier=1.0),
        barriers=(("source", "target", 10.0),),
    )
    result = evaluate_bridge_sensitivity(nodes, reference(), [scenario], "source", "target")
    assert result.direct_edge_scenario_count == 1
    assert result.positive_bridge_gain_count == 1
    assert result.positive_bridge_gain_frequency == 1.0
    assert result.minimum_cost_node_support == {"middle": 1.0}


def test_scenario_and_node_order_do_not_change_summary():
    nodes = [
        node("source", 0.0, [0.0]),
        node("middle", 1.0, [0.2]),
        node("target", 2.0, [0.0]),
    ]
    scenarios = [
        BridgeSensitivityScenario("b", BridgeGraphDeclaration(k_nearest=1, max_geographic_km=150.0)),
        BridgeSensitivityScenario("a", BridgeGraphDeclaration(max_geographic_km=120.0)),
    ]
    first = evaluate_bridge_sensitivity(nodes, reference(), scenarios, "source", "target")
    second = evaluate_bridge_sensitivity(
        list(reversed(nodes)), reference(), list(reversed(scenarios)), "source", "target"
    )
    assert first.fingerprint == second.fingerprint
    assert first.scenarios == second.scenarios
    assert first.minimum_cost_edge_support == second.minimum_cost_edge_support


def test_alternative_routes_have_fractional_node_support():
    nodes = [
        node("source", 0.0, [0.0], lat=0.0),
        node("north", 1.0, [0.0], lat=0.2),
        node("south", 1.0, [0.0], lat=-0.2),
        node("target", 2.0, [0.0], lat=0.0),
    ]
    scenarios = [
        BridgeSensitivityScenario(
            "north-open",
            BridgeGraphDeclaration(max_geographic_km=130.0),
            barriers=(("source", "south", 100.0),),
        ),
        BridgeSensitivityScenario(
            "south-open",
            BridgeGraphDeclaration(max_geographic_km=130.0),
            barriers=(("source", "north", 100.0),),
        ),
    ]
    result = evaluate_bridge_sensitivity(nodes, reference(), scenarios, "source", "target")
    assert result.connected_frequency == 1.0
    assert result.minimum_cost_node_support["north"] == pytest.approx(0.5)
    assert result.minimum_cost_node_support["south"] == pytest.approx(0.5)
    assert "cumulative_cost" in result.metric_summaries


def test_duplicate_scenario_ids_are_rejected():
    scenario = BridgeSensitivityScenario("same", BridgeGraphDeclaration(max_geographic_km=120.0))
    nodes = [node("source", 0.0, [0.0]), node("target", 1.0, [0.0])]
    with pytest.raises(ValueError, match="scenario IDs"):
        evaluate_bridge_sensitivity(nodes, reference(), [scenario, scenario], "source", "target")
