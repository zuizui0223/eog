from eog import (
    BridgeScenarioResult,
    BridgeSensitivityResult,
    HypothesisFamilyDeclaration,
    SurveyCandidate,
    run_hypothesis_survey_pipeline,
)


def scenario(scenario_id, path):
    return BridgeScenarioResult(
        scenario_id=scenario_id,
        scenario_fingerprint=f"fp-{scenario_id}",
        graph_fingerprint=f"graph-{scenario_id}",
        connected=True,
        failure_reason="",
        minimum_cost_nodes=tuple(path),
        minimum_bottleneck_nodes=tuple(path),
        cumulative_cost=1.0,
        bottleneck_cost=1.0,
        geographic_cost=1.0,
        environmental_cost=0.0,
        barrier_cost=0.0,
        bridge_gain=None,
        edge_disjoint_path_count=1,
    )


def sensitivity():
    scenarios = (
        scenario("north-1", ("source", "north", "shared", "target")),
        scenario("north-2", ("source", "north", "target")),
        scenario("south-1", ("source", "south", "shared", "target")),
        scenario("south-2", ("source", "south", "target")),
    )
    return BridgeSensitivityResult(
        source_id="source",
        target_id="target",
        scenario_count=4,
        connected_count=4,
        connected_frequency=1.0,
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


def families():
    return [
        HypothesisFamilyDeclaration("north", ("north-1", "north-2")),
        HypothesisFamilyDeclaration("south", ("south-1", "south-2")),
    ]


def test_pipeline_ranks_hypothesis_separating_sites_first():
    result = run_hypothesis_survey_pipeline(
        sensitivity(),
        families(),
        [SurveyCandidate("shared"), SurveyCandidate("north"), SurveyCandidate("south")],
    )
    assert result.ranking.rows[0].node_id in {"north", "south"}
    assert result.zero_information_candidate_ids == ("shared",)
    assert result.informative_candidate_ids == ("north", "south")


def test_pipeline_propagates_unassigned_scenario_audit():
    result = run_hypothesis_survey_pipeline(
        sensitivity(),
        [
            HypothesisFamilyDeclaration("north", ("north-1",)),
            HypothesisFamilyDeclaration("south", ("south-1",)),
        ],
        [SurveyCandidate("north"), SurveyCandidate("south")],
    )
    assert result.adapter.unassigned_scenario_ids == ("north-2", "south-2")


def test_pipeline_is_order_invariant():
    candidates = [SurveyCandidate("north"), SurveyCandidate("south"), SurveyCandidate("shared")]
    first = run_hypothesis_survey_pipeline(sensitivity(), families(), candidates)
    second = run_hypothesis_survey_pipeline(
        sensitivity(), list(reversed(families())), list(reversed(candidates))
    )
    assert first == second
