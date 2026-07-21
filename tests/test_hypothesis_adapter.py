import pytest

from eog import (
    BridgeScenarioResult,
    BridgeSensitivityResult,
    HypothesisFamilyDeclaration,
    build_bridge_hypotheses,
)


def scenario(scenario_id, *, connected=True, cost_path=(), bottleneck_path=()):
    return BridgeScenarioResult(
        scenario_id=scenario_id,
        scenario_fingerprint=f"fp-{scenario_id}",
        graph_fingerprint=f"graph-{scenario_id}" if connected else None,
        connected=connected,
        failure_reason="" if connected else "disconnected",
        minimum_cost_nodes=tuple(cost_path),
        minimum_bottleneck_nodes=tuple(bottleneck_path),
        cumulative_cost=1.0 if connected else None,
        bottleneck_cost=1.0 if connected else None,
        geographic_cost=1.0 if connected else None,
        environmental_cost=0.0 if connected else None,
        barrier_cost=0.0 if connected else None,
        bridge_gain=None,
        edge_disjoint_path_count=1 if connected else None,
    )


def sensitivity():
    scenarios = (
        scenario("north-1", cost_path=("source", "north", "target"), bottleneck_path=("source", "north", "target")),
        scenario("north-2", connected=False),
        scenario("south-1", cost_path=("source", "south", "target"), bottleneck_path=("source", "shared", "target")),
        scenario("south-2", cost_path=("source", "south", "target"), bottleneck_path=("source", "south", "target")),
    )
    return BridgeSensitivityResult(
        source_id="source",
        target_id="target",
        scenario_count=4,
        connected_count=3,
        connected_frequency=0.75,
        direct_edge_scenario_count=0,
        positive_bridge_gain_count=0,
        positive_bridge_gain_frequency=None,
        minimum_cost_node_support={},
        minimum_bottleneck_node_support={},
        minimum_cost_edge_support={},
        metric_summaries={},
        scenarios=scenarios,
        fingerprint="sensitivity-fingerprint",
    )


def test_disconnected_scenarios_remain_in_family_denominator():
    result = build_bridge_hypotheses(
        sensitivity(),
        [
            HypothesisFamilyDeclaration("north", ("north-1", "north-2")),
            HypothesisFamilyDeclaration("south", ("south-1", "south-2")),
        ],
    )
    north = next(item for item in result.hypotheses if item.hypothesis_id == "north")
    assert north.node_support == {"north": 0.5}
    north_summary = next(item for item in result.summaries if item.hypothesis_id == "north")
    assert north_summary.connected_frequency == 0.5


def test_union_mode_combines_cost_and_bottleneck_paths():
    result = build_bridge_hypotheses(
        sensitivity(),
        [
            HypothesisFamilyDeclaration("north", ("north-1", "north-2")),
            HypothesisFamilyDeclaration("south", ("south-1", "south-2"), path_mode="union"),
        ],
    )
    south = next(item for item in result.hypotheses if item.hypothesis_id == "south")
    assert south.node_support["south"] == 1.0
    assert south.node_support["shared"] == 0.5


def test_unassigned_scenarios_are_reported():
    result = build_bridge_hypotheses(
        sensitivity(),
        [
            HypothesisFamilyDeclaration("north", ("north-1",)),
            HypothesisFamilyDeclaration("south", ("south-1",)),
        ],
    )
    assert result.unassigned_scenario_ids == ("north-2", "south-2")


def test_complete_assignment_can_be_required():
    with pytest.raises(ValueError, match="all sensitivity scenarios"):
        build_bridge_hypotheses(
            sensitivity(),
            [
                HypothesisFamilyDeclaration("north", ("north-1",)),
                HypothesisFamilyDeclaration("south", ("south-1",)),
            ],
            require_complete_assignment=True,
        )


def test_overlap_is_rejected_by_default():
    with pytest.raises(ValueError, match="multiple hypothesis families"):
        build_bridge_hypotheses(
            sensitivity(),
            [
                HypothesisFamilyDeclaration("north", ("north-1",)),
                HypothesisFamilyDeclaration("south", ("north-1", "south-1")),
            ],
        )


def test_family_order_does_not_change_result():
    families = [
        HypothesisFamilyDeclaration("north", ("north-1", "north-2")),
        HypothesisFamilyDeclaration("south", ("south-1", "south-2")),
    ]
    first = build_bridge_hypotheses(sensitivity(), families)
    second = build_bridge_hypotheses(sensitivity(), list(reversed(families)))
    assert first == second
