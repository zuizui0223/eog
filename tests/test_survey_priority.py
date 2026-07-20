from eog import (
    BridgeSensitivityResult,
    SurveyCandidate,
    SurveyPriorityWeights,
    rank_survey_candidates,
)


def sensitivity():
    return BridgeSensitivityResult(
        source_id="source",
        target_id="target",
        scenario_count=4,
        connected_count=3,
        connected_frequency=0.75,
        direct_edge_scenario_count=0,
        positive_bridge_gain_count=0,
        positive_bridge_gain_frequency=None,
        minimum_cost_node_support={"middle": 1.0, "alternative": 0.33},
        minimum_bottleneck_node_support={"middle": 0.67, "alternative": 0.67},
        minimum_cost_edge_support={},
        metric_summaries={},
        scenarios=(),
        fingerprint="sensitivity-fingerprint",
    )


def test_high_support_unsurveyed_node_ranks_first():
    result = rank_survey_candidates(
        sensitivity(),
        [SurveyCandidate("alternative"), SurveyCandidate("middle")],
    )
    assert result.rows[0].node_id == "middle"


def test_accessibility_penalty_can_change_priority():
    result = rank_survey_candidates(
        sensitivity(),
        [
            SurveyCandidate("middle", accessibility_cost=3.0),
            SurveyCandidate("alternative", accessibility_cost=0.0),
        ],
        weights=SurveyPriorityWeights(accessibility_penalty=1.0),
    )
    assert result.rows[0].node_id == "alternative"


def test_already_surveyed_node_is_demoted():
    result = rank_survey_candidates(
        sensitivity(),
        [SurveyCandidate("middle", already_surveyed=True), SurveyCandidate("alternative")],
    )
    assert result.rows[0].node_id == "alternative"
    assert next(row for row in result.rows if row.node_id == "middle").priority_score <= 0.0


def test_input_order_does_not_change_fingerprint():
    candidates = [SurveyCandidate("middle"), SurveyCandidate("alternative")]
    first = rank_survey_candidates(sensitivity(), candidates)
    second = rank_survey_candidates(sensitivity(), list(reversed(candidates)))
    assert first == second


def test_duplicate_candidate_ids_are_rejected():
    try:
        rank_survey_candidates(sensitivity(), [SurveyCandidate("middle"), SurveyCandidate("middle")])
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("expected duplicate candidate IDs to be rejected")
