"""End-to-end bridge-hypothesis survey prioritization."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from .bridge_sensitivity import BridgeSensitivityResult
from .hypothesis_adapter import (
    HypothesisAdapterResult,
    HypothesisFamilyDeclaration,
    build_bridge_hypotheses,
)
from .hypothesis_discrimination import (
    HypothesisDiscriminationResult,
    HypothesisDiscriminationWeights,
    rank_hypothesis_discriminating_sites,
)
from .survey_priority import SurveyCandidate


@dataclass(frozen=True)
class HypothesisSurveyPipelineResult:
    """Auditable outputs from scenario families through survey ranking."""

    adapter: HypothesisAdapterResult
    ranking: HypothesisDiscriminationResult
    informative_candidate_ids: tuple[str, ...]
    zero_information_candidate_ids: tuple[str, ...]
    fingerprint: str


def run_hypothesis_survey_pipeline(
    sensitivity: BridgeSensitivityResult,
    families: Sequence[HypothesisFamilyDeclaration],
    candidates: Sequence[SurveyCandidate],
    *,
    weights: HypothesisDiscriminationWeights = HypothesisDiscriminationWeights(),
    require_complete_assignment: bool = False,
    allow_scenario_overlap: bool = False,
) -> HypothesisSurveyPipelineResult:
    """Build hypothesis supports and rank surveys in one reproducible operation.

    The resulting scores summarize disagreement among declared scenario families.
    They are not occurrence probabilities, posterior model probabilities, or
    expected information gain.
    """
    adapter = build_bridge_hypotheses(
        sensitivity,
        families,
        require_complete_assignment=require_complete_assignment,
        allow_scenario_overlap=allow_scenario_overlap,
    )
    ranking = rank_hypothesis_discriminating_sites(
        adapter.hypotheses,
        candidates,
        weights=weights,
    )

    informative = tuple(
        sorted(row.node_id for row in ranking.rows if row.support_range > 0.0)
    )
    zero_information = tuple(
        sorted(row.node_id for row in ranking.rows if row.support_range == 0.0)
    )
    payload = {
        "sensitivity_fingerprint": sensitivity.fingerprint,
        "adapter_fingerprint": adapter.fingerprint,
        "ranking_fingerprint": ranking.fingerprint,
        "informative_candidate_ids": informative,
        "zero_information_candidate_ids": zero_information,
        "require_complete_assignment": require_complete_assignment,
        "allow_scenario_overlap": allow_scenario_overlap,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HypothesisSurveyPipelineResult(
        adapter=adapter,
        ranking=ranking,
        informative_candidate_ids=informative,
        zero_information_candidate_ids=zero_information,
        fingerprint=fingerprint,
    )
