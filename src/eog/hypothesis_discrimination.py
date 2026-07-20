"""Rank surveys by how strongly declared bridge hypotheses disagree."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import combinations
from typing import Mapping, Sequence

import numpy as np

from .survey_priority import SurveyCandidate


@dataclass(frozen=True)
class BridgeHypothesis:
    hypothesis_id: str
    node_support: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must be non-empty")
        for node_id, value in self.node_support.items():
            if not str(node_id).strip():
                raise ValueError("node support IDs must be non-empty")
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("node support must be finite and in [0, 1]")


@dataclass(frozen=True)
class HypothesisDiscriminationWeights:
    support_range: float = 1.0
    pairwise_separation: float = 1.0
    survey_deficit: float = 1.0
    accessibility_penalty: float = 1.0

    def __post_init__(self) -> None:
        values = tuple(self.__dict__.values())
        if not all(np.isfinite(values)) or any(value < 0 for value in values):
            raise ValueError("weights must be finite and non-negative")
        if not any(value > 0 for value in values):
            raise ValueError("at least one weight must be positive")


@dataclass(frozen=True)
class HypothesisDiscriminationRow:
    node_id: str
    discrimination_score: float
    support_range: float
    mean_pairwise_separation: float
    most_separated_hypotheses: tuple[str, str]
    support_by_hypothesis: Mapping[str, float]
    survey_deficit: float
    accessibility_cost: float
    already_surveyed: bool


@dataclass(frozen=True)
class HypothesisDiscriminationResult:
    hypothesis_ids: tuple[str, ...]
    rows: tuple[HypothesisDiscriminationRow, ...]
    fingerprint: str


def rank_hypothesis_discriminating_sites(
    hypotheses: Sequence[BridgeHypothesis],
    candidates: Sequence[SurveyCandidate],
    *,
    weights: HypothesisDiscriminationWeights = HypothesisDiscriminationWeights(),
) -> HypothesisDiscriminationResult:
    """Rank sites where predeclared bridge hypotheses disagree most.

    Scores summarize contrasts among declared support surfaces. They are not
    expected information gain, posterior model probabilities, or occurrence probabilities.
    """
    ordered_hypotheses = tuple(sorted(hypotheses, key=lambda item: item.hypothesis_id))
    if len(ordered_hypotheses) < 2:
        raise ValueError("at least two hypotheses are required")
    if len({item.hypothesis_id for item in ordered_hypotheses}) != len(ordered_hypotheses):
        raise ValueError("hypothesis IDs must be unique")
    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.node_id))
    if len({item.node_id for item in ordered_candidates}) != len(ordered_candidates):
        raise ValueError("candidate node IDs must be unique")

    max_effort = max((item.survey_effort for item in ordered_candidates), default=0.0)
    effort_scale = max(max_effort, 1.0)
    rows: list[HypothesisDiscriminationRow] = []
    for candidate in ordered_candidates:
        support = {
            hypothesis.hypothesis_id: float(hypothesis.node_support.get(candidate.node_id, 0.0))
            for hypothesis in ordered_hypotheses
        }
        pairs = [
            (abs(support[a] - support[b]), a, b)
            for a, b in combinations(support, 2)
        ]
        separation, first, second = max(pairs, key=lambda item: (item[0], item[1], item[2]))
        support_range = max(support.values()) - min(support.values())
        mean_pairwise = float(np.mean([item[0] for item in pairs]))
        survey_deficit = 1.0 - min(1.0, candidate.survey_effort / effort_scale)
        score = (
            weights.support_range * support_range
            + weights.pairwise_separation * mean_pairwise
            + weights.survey_deficit * survey_deficit
            - weights.accessibility_penalty * candidate.accessibility_cost
        )
        if candidate.already_surveyed:
            score = min(score, 0.0)
        rows.append(
            HypothesisDiscriminationRow(
                node_id=candidate.node_id,
                discrimination_score=float(score),
                support_range=float(support_range),
                mean_pairwise_separation=mean_pairwise,
                most_separated_hypotheses=(first, second),
                support_by_hypothesis=support,
                survey_deficit=float(survey_deficit),
                accessibility_cost=float(candidate.accessibility_cost),
                already_surveyed=candidate.already_surveyed,
            )
        )

    rows.sort(key=lambda row: (-row.discrimination_score, row.node_id))
    payload = {
        "hypotheses": [
            {"hypothesis_id": item.hypothesis_id, "node_support": dict(sorted(item.node_support.items()))}
            for item in ordered_hypotheses
        ],
        "candidates": [item.__dict__ for item in ordered_candidates],
        "weights": weights.__dict__,
        "rows": [
            {**row.__dict__, "support_by_hypothesis": dict(sorted(row.support_by_hypothesis.items()))}
            for row in rows
        ],
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return HypothesisDiscriminationResult(
        tuple(item.hypothesis_id for item in ordered_hypotheses), tuple(rows), fingerprint
    )
