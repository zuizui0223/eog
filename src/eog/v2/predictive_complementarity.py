"""Prospective paired added-value evaluation for EOG predictive features.

This module does not fit a predictor and does not add an ecological operator. It
formalizes the post-Daphnia mainline question: when a strong external learner is
already frozen, do unchanged EOG Layer-B features improve that *same learner* on the
same heldout outer units?

The contract is deliberately paired. A baseline score and an augmented score must
refer to the same outer unit, learner/fit policy, response endpoint, split and external
feature set. The only declared augmentation is the frozen EOG feature representation.
This prevents a favourable result from being manufactured by changing the model family,
hyperparameters, split or conventional covariates together with the EOG features.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Sequence


ComplementarityStatus = Literal[
    "favorable_complementary_added_value",
    "adverse_complementary_added_value",
    "no_confirmed_complementary_added_value",
]


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _finite_score(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric, not bool")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


@dataclass(frozen=True)
class PredictiveComplementarityDeclaration:
    """Frozen prospective contract for one paired added-value endpoint."""

    metric_name: str
    lower_is_better: bool
    expected_outer_unit_count: int
    favorable_min_augmented_wins: int
    adverse_min_baseline_wins: int
    learner_fit_fingerprint: str
    response_endpoint_fingerprint: str
    split_fingerprint: str
    external_feature_fingerprint: str
    eog_feature_fingerprint: str

    def __post_init__(self) -> None:
        _nonempty_string(self.metric_name, "metric_name")
        if not isinstance(self.lower_is_better, bool):
            raise TypeError("lower_is_better must be bool")
        for label in (
            "learner_fit_fingerprint",
            "response_endpoint_fingerprint",
            "split_fingerprint",
            "external_feature_fingerprint",
            "eog_feature_fingerprint",
        ):
            _nonempty_string(getattr(self, label), label)
        if (
            isinstance(self.expected_outer_unit_count, bool)
            or not isinstance(self.expected_outer_unit_count, int)
            or self.expected_outer_unit_count <= 0
        ):
            raise ValueError("expected_outer_unit_count must be a positive integer")
        for label in ("favorable_min_augmented_wins", "adverse_min_baseline_wins"):
            value = getattr(self, label)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{label} must be a non-negative integer")
            if value > self.expected_outer_unit_count:
                raise ValueError(f"{label} cannot exceed expected_outer_unit_count")

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "metric_name": self.metric_name,
                "lower_is_better": self.lower_is_better,
                "expected_outer_unit_count": self.expected_outer_unit_count,
                "favorable_min_augmented_wins": self.favorable_min_augmented_wins,
                "adverse_min_baseline_wins": self.adverse_min_baseline_wins,
                "learner_fit_fingerprint": self.learner_fit_fingerprint,
                "response_endpoint_fingerprint": self.response_endpoint_fingerprint,
                "split_fingerprint": self.split_fingerprint,
                "external_feature_fingerprint": self.external_feature_fingerprint,
                "eog_feature_fingerprint": self.eog_feature_fingerprint,
            }
        )


@dataclass(frozen=True)
class PairedOuterUnitScore:
    """Heldout score pair from one unchanged outer validation unit."""

    outer_unit_id: str
    baseline_score: float
    augmented_score: float

    def __post_init__(self) -> None:
        _nonempty_string(self.outer_unit_id, "outer_unit_id")
        object.__setattr__(
            self,
            "baseline_score",
            _finite_score(self.baseline_score, "baseline_score"),
        )
        object.__setattr__(
            self,
            "augmented_score",
            _finite_score(self.augmented_score, "augmented_score"),
        )


@dataclass(frozen=True)
class PredictiveComplementarityResult:
    """Paired heldout decision for strong learner vs the same learner + EOG."""

    status: ComplementarityStatus
    metric_name: str
    lower_is_better: bool
    outer_unit_count: int
    baseline_macro_score: float
    augmented_macro_score: float
    augmented_minus_baseline: float
    augmented_better_outer_units: int
    baseline_better_outer_units: int
    tied_outer_units: int
    declaration_fingerprint: str
    paired_score_fingerprint: str
    fingerprint: str


def evaluate_predictive_complementarity(
    declaration: PredictiveComplementarityDeclaration,
    paired_scores: Sequence[PairedOuterUnitScore],
    *,
    tie_tolerance: float = 0.0,
) -> PredictiveComplementarityResult:
    """Evaluate prospectively frozen paired complementary added value.

    For a lower-is-better metric, favourable requires both a lower augmented macro score
    and at least ``favorable_min_augmented_wins`` paired outer-unit wins. Adverse
    requires the reverse macro direction and at least ``adverse_min_baseline_wins``
    baseline wins. Higher-is-better metrics reverse only the score direction.

    Anything else is preserved as ``no_confirmed_complementary_added_value``. The
    function never changes thresholds or resolves ambiguous results by tuning.
    """

    if not isinstance(declaration, PredictiveComplementarityDeclaration):
        raise TypeError("declaration must be PredictiveComplementarityDeclaration")
    if isinstance(tie_tolerance, bool):
        raise TypeError("tie_tolerance must be numeric, not bool")
    tolerance = float(tie_tolerance)
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tie_tolerance must be finite and non-negative")

    rows = tuple(paired_scores)
    if len(rows) != declaration.expected_outer_unit_count:
        raise ValueError(
            "paired score count differs from prospectively declared outer-unit count: "
            f"{len(rows)} != {declaration.expected_outer_unit_count}"
        )
    if not all(isinstance(row, PairedOuterUnitScore) for row in rows):
        raise TypeError("paired_scores must contain only PairedOuterUnitScore values")

    normalized = tuple(sorted(rows, key=lambda row: row.outer_unit_id))
    ids = tuple(row.outer_unit_id for row in normalized)
    if len(set(ids)) != len(ids):
        raise ValueError("outer_unit_id values must be unique")

    baseline_macro = sum(row.baseline_score for row in normalized) / len(normalized)
    augmented_macro = sum(row.augmented_score for row in normalized) / len(normalized)
    delta = augmented_macro - baseline_macro

    augmented_wins = 0
    baseline_wins = 0
    ties = 0
    for row in normalized:
        difference = row.augmented_score - row.baseline_score
        if abs(difference) <= tolerance:
            ties += 1
            continue
        augmented_is_better = difference < 0 if declaration.lower_is_better else difference > 0
        if augmented_is_better:
            augmented_wins += 1
        else:
            baseline_wins += 1

    macro_augmented_is_better = (
        delta < -tolerance if declaration.lower_is_better else delta > tolerance
    )
    macro_baseline_is_better = (
        delta > tolerance if declaration.lower_is_better else delta < -tolerance
    )

    if (
        macro_augmented_is_better
        and augmented_wins >= declaration.favorable_min_augmented_wins
    ):
        status: ComplementarityStatus = "favorable_complementary_added_value"
    elif (
        macro_baseline_is_better
        and baseline_wins >= declaration.adverse_min_baseline_wins
    ):
        status = "adverse_complementary_added_value"
    else:
        status = "no_confirmed_complementary_added_value"

    score_payload = [
        [row.outer_unit_id, row.baseline_score, row.augmented_score]
        for row in normalized
    ]
    score_fingerprint = _canonical_sha256(score_payload)
    payload = {
        "status": status,
        "metric_name": declaration.metric_name,
        "lower_is_better": declaration.lower_is_better,
        "outer_unit_count": len(normalized),
        "baseline_macro_score": baseline_macro,
        "augmented_macro_score": augmented_macro,
        "augmented_minus_baseline": delta,
        "augmented_better_outer_units": augmented_wins,
        "baseline_better_outer_units": baseline_wins,
        "tied_outer_units": ties,
        "declaration_fingerprint": declaration.fingerprint,
        "paired_score_fingerprint": score_fingerprint,
        "tie_tolerance": tolerance,
    }
    return PredictiveComplementarityResult(
        status=status,
        metric_name=declaration.metric_name,
        lower_is_better=declaration.lower_is_better,
        outer_unit_count=len(normalized),
        baseline_macro_score=baseline_macro,
        augmented_macro_score=augmented_macro,
        augmented_minus_baseline=delta,
        augmented_better_outer_units=augmented_wins,
        baseline_better_outer_units=baseline_wins,
        tied_outer_units=ties,
        declaration_fingerprint=declaration.fingerprint,
        paired_score_fingerprint=score_fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
