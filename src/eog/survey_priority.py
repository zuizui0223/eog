"""Survey-priority diagnostics derived from bridge sensitivity results."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .bridge_sensitivity import BridgeSensitivityResult


@dataclass(frozen=True)
class SurveyCandidate:
    node_id: str
    survey_effort: float = 0.0
    accessibility_cost: float = 0.0
    already_surveyed: bool = False

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        for value, name in ((self.survey_effort, "survey_effort"), (self.accessibility_cost, "accessibility_cost")):
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class SurveyPriorityWeights:
    minimum_cost_support: float = 1.0
    minimax_support: float = 1.0
    uncertainty: float = 1.0
    low_effort: float = 1.0
    accessibility_penalty: float = 1.0

    def __post_init__(self) -> None:
        values = tuple(self.__dict__.values())
        if not all(np.isfinite(values)) or any(value < 0 for value in values):
            raise ValueError("priority weights must be finite and non-negative")
        if not any(value > 0 for value in values):
            raise ValueError("at least one priority weight must be positive")


@dataclass(frozen=True)
class SurveyPriorityRow:
    node_id: str
    priority_score: float
    minimum_cost_support: float
    minimax_support: float
    structural_uncertainty: float
    survey_deficit: float
    accessibility_cost: float
    already_surveyed: bool


@dataclass(frozen=True)
class SurveyPriorityResult:
    rows: tuple[SurveyPriorityRow, ...]
    fingerprint: str


def rank_survey_candidates(
    sensitivity: BridgeSensitivityResult,
    candidates: Sequence[SurveyCandidate],
    *,
    weights: SurveyPriorityWeights = SurveyPriorityWeights(),
) -> SurveyPriorityResult:
    """Rank candidate nodes by bridge relevance, uncertainty and survey deficit.

    Scores are decision-support diagnostics under declared sensitivity scenarios.
    They are not occurrence probabilities or expected-value-of-information estimates.
    """
    ordered = tuple(sorted(candidates, key=lambda item: item.node_id))
    if len({item.node_id for item in ordered}) != len(ordered):
        raise ValueError("candidate node IDs must be unique")

    min_support: Mapping[str, float] = sensitivity.minimum_cost_node_support
    bottleneck_support: Mapping[str, float] = sensitivity.minimax_node_support
    rows: list[SurveyPriorityRow] = []
    max_effort = max((item.survey_effort for item in ordered), default=0.0)
    effort_scale = max(max_effort, 1.0)

    for item in ordered:
        a = float(min_support.get(item.node_id, 0.0))
        b = float(bottleneck_support.get(item.node_id, 0.0))
        uncertainty = 1.0 - abs(a - b)
        survey_deficit = 1.0 - min(1.0, item.survey_effort / effort_scale)
        score = (
            weights.minimum_cost_support * a
            + weights.minimax_support * b
            + weights.uncertainty * uncertainty
            + weights.low_effort * survey_deficit
            - weights.accessibility_penalty * item.accessibility_cost
        )
        if item.already_surveyed:
            score = min(score, 0.0)
        rows.append(
            SurveyPriorityRow(
                node_id=item.node_id,
                priority_score=float(score),
                minimum_cost_support=a,
                minimax_support=b,
                structural_uncertainty=float(uncertainty),
                survey_deficit=float(survey_deficit),
                accessibility_cost=float(item.accessibility_cost),
                already_surveyed=item.already_surveyed,
            )
        )

    rows.sort(key=lambda row: (-row.priority_score, row.node_id))
    payload = {
        "sensitivity_fingerprint": sensitivity.fingerprint,
        "weights": weights.__dict__,
        "candidates": [item.__dict__ for item in ordered],
        "rows": [row.__dict__ for row in rows],
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return SurveyPriorityResult(tuple(rows), fingerprint)
