import pytest

from eog import (
    BridgeHypothesis,
    HypothesisDiscriminationWeights,
    SurveyCandidate,
    rank_hypothesis_discriminating_sites,
)


def hypotheses():
    return [
        BridgeHypothesis("direct_jump", {"middle": 0.05, "coast": 0.80}),
        BridgeHypothesis("stepping_stone", {"middle": 0.95, "coast": 0.20}),
        BridgeHypothesis("southern_route", {"middle": 0.10, "coast": 0.75}),
    ]


def test_site_with_strongest_hypothesis_disagreement_ranks_first():
    result = rank_hypothesis_discriminating_sites(
        hypotheses(), [SurveyCandidate("coast"), SurveyCandidate("middle")]
    )
    assert result.rows[0].node_id == "middle"
    assert result.rows[0].most_separated_hypotheses == ("direct_jump", "stepping_stone")


def test_accessibility_penalty_can_change_rank():
    result = rank_hypothesis_discriminating_sites(
        hypotheses(),
        [SurveyCandidate("middle", accessibility_cost=2.0), SurveyCandidate("coast")],
        weights=HypothesisDiscriminationWeights(accessibility_penalty=1.0),
    )
    assert result.rows[0].node_id == "coast"


def test_already_surveyed_site_is_demoted():
    result = rank_hypothesis_discriminating_sites(
        hypotheses(),
        [SurveyCandidate("middle", already_surveyed=True), SurveyCandidate("coast")],
    )
    assert result.rows[0].node_id == "coast"


def test_order_does_not_change_result_or_fingerprint():
    candidates = [SurveyCandidate("middle"), SurveyCandidate("coast")]
    first = rank_hypothesis_discriminating_sites(hypotheses(), candidates)
    second = rank_hypothesis_discriminating_sites(
        list(reversed(hypotheses())), list(reversed(candidates))
    )
    assert first == second


def test_at_least_two_hypotheses_are_required():
    with pytest.raises(ValueError, match="at least two"):
        rank_hypothesis_discriminating_sites(
            [BridgeHypothesis("only", {"middle": 0.5})], [SurveyCandidate("middle")]
        )


def test_support_must_be_bounded():
    with pytest.raises(ValueError, match="\[0, 1\]"):
        BridgeHypothesis("invalid", {"middle": 1.1})
