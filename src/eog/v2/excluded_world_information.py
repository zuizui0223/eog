"""Secondary explanatory diagnostics for excluded-world predictive information.

This module does not fit a model, change the primary complementarity endpoint, or add
an ecological transition operator. It freezes and computes a descriptive question for
one heldout outer unit: is EOG's paired log-loss gain concentrated where the baseline
learner is uncertain and surviving accessibility-compatible worlds disagree?

Thresholds are estimated from the corresponding outer training partition only. The
heldout response is used only after those thresholds, predictions and Layer-B state are
fixed. Empty strata remain empty; no response-driven rebinning or rescue tuning is
performed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from statistics import median
from typing import Literal, Sequence


ExplanatoryStratum = Literal[
    "low_local_uncertainty_low_world_disagreement",
    "low_local_uncertainty_high_world_disagreement",
    "high_local_uncertainty_low_world_disagreement",
    "high_local_uncertainty_high_world_disagreement",
]

STRUCTURAL_STATUSES = {
    "excluded_in_all_worlds",
    "robustly_supported",
    "contingent",
}
PROBABILITY_CLIP = 1e-15


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


def _clean_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric, not bool")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _probability(value: object, label: str) -> float:
    number = _finite(value, label)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{label} must lie in [0, 1]")
    return number


def binary_entropy(probability: float) -> float:
    """Return Bernoulli entropy after a fixed numerical clip."""

    p = min(
        max(_probability(probability, "probability"), PROBABILITY_CLIP),
        1.0 - PROBABILITY_CLIP,
    )
    return -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))


def binary_log_loss(outcome: int, probability: float) -> float:
    """Return one-row binary log loss after the same fixed numerical clip."""

    if isinstance(outcome, bool) or outcome not in (0, 1):
        raise ValueError("outcome must be integer 0 or 1")
    p = min(
        max(_probability(probability, "probability"), PROBABILITY_CLIP),
        1.0 - PROBABILITY_CLIP,
    )
    return -(outcome * math.log(p) + (1 - outcome) * math.log(1.0 - p))


@dataclass(frozen=True)
class ExplanatoryTrainingRow:
    """Response-blind training quantity used only to freeze stratum thresholds."""

    row_id: str
    baseline_probability: float
    support_range: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "row_id", _clean_required(self.row_id, "row_id"))
        object.__setattr__(
            self,
            "baseline_probability",
            _probability(self.baseline_probability, "baseline_probability"),
        )
        support_range = _finite(self.support_range, "support_range")
        if support_range < 0.0:
            raise ValueError("support_range must be non-negative")
        object.__setattr__(self, "support_range", support_range)


@dataclass(frozen=True)
class ExcludedWorldInformationThresholds:
    """Outer-training medians fixed before heldout response access."""

    training_row_count: int
    local_uncertainty_entropy_threshold: float
    world_disagreement_support_range_threshold: float
    fingerprint: str


def freeze_excluded_world_information_thresholds(
    training_rows: Sequence[ExplanatoryTrainingRow],
) -> ExcludedWorldInformationThresholds:
    """Freeze order-invariant medians from one outer training partition."""

    rows = tuple(training_rows)
    if not rows:
        raise ValueError("training_rows must not be empty")
    if not all(isinstance(row, ExplanatoryTrainingRow) for row in rows):
        raise TypeError("training_rows must contain only ExplanatoryTrainingRow values")
    ids = tuple(row.row_id for row in rows)
    if len(set(ids)) != len(ids):
        raise ValueError("training row_id values must be unique")

    uncertainty = float(median(binary_entropy(row.baseline_probability) for row in rows))
    disagreement = float(median(row.support_range for row in rows))
    payload = {
        "training_rows": sorted(
            [
                [
                    row.row_id,
                    row.baseline_probability,
                    row.support_range,
                ]
                for row in rows
            ],
            key=lambda values: values[0],
        ),
        "training_row_count": len(rows),
        "local_uncertainty_entropy_threshold": uncertainty,
        "world_disagreement_support_range_threshold": disagreement,
        "tie_rule": "threshold_value_is_high",
        "probability_clip": PROBABILITY_CLIP,
    }
    return ExcludedWorldInformationThresholds(
        training_row_count=len(rows),
        local_uncertainty_entropy_threshold=uncertainty,
        world_disagreement_support_range_threshold=disagreement,
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class ExplanatoryHeldoutRow:
    """Heldout predictions, fixed Layer-B state and the once-opened binary outcome."""

    row_id: str
    outcome: int
    baseline_probability: float
    augmented_probability: float
    support_range: float
    support_std: float
    surviving_world_fraction: float
    structural_status: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "row_id", _clean_required(self.row_id, "row_id"))
        if isinstance(self.outcome, bool) or self.outcome not in (0, 1):
            raise ValueError("outcome must be integer 0 or 1")
        object.__setattr__(
            self,
            "baseline_probability",
            _probability(self.baseline_probability, "baseline_probability"),
        )
        object.__setattr__(
            self,
            "augmented_probability",
            _probability(self.augmented_probability, "augmented_probability"),
        )
        for label in ("support_range", "support_std"):
            value = _finite(getattr(self, label), label)
            if value < 0.0:
                raise ValueError(f"{label} must be non-negative")
            object.__setattr__(self, label, value)
        surviving_fraction = _finite(
            self.surviving_world_fraction,
            "surviving_world_fraction",
        )
        if surviving_fraction <= 0.0 or surviving_fraction > 1.0:
            raise ValueError("surviving_world_fraction must lie in (0, 1]")
        object.__setattr__(self, "surviving_world_fraction", surviving_fraction)
        status = _clean_required(self.structural_status, "structural_status")
        if status not in STRUCTURAL_STATUSES:
            raise ValueError("structural_status is not a frozen Layer-B status")
        object.__setattr__(self, "structural_status", status)


@dataclass(frozen=True)
class ExplanatoryStratumSummary:
    """Descriptive heldout loss summary for one frozen two-by-two stratum."""

    stratum: ExplanatoryStratum
    row_count: int
    event_count: int
    non_event_count: int
    baseline_mean_log_loss: float | None
    augmented_mean_log_loss: float | None
    augmented_minus_baseline_mean_log_loss: float | None
    fingerprint: str


@dataclass(frozen=True)
class ExcludedWorldInformationDiagnostic:
    """One outer unit's secondary excluded-world information diagnostic."""

    outer_unit_id: str
    threshold_fingerprint: str
    row_count: int
    event_count: int
    non_event_count: int
    declared_world_count: int
    surviving_world_count: int
    world_contraction_fraction: float
    mean_support_range: float
    mean_support_std: float
    contingent_row_fraction: float
    baseline_macro_log_loss: float
    augmented_macro_log_loss: float
    augmented_minus_baseline_log_loss: float
    structurally_informative: bool
    primary_terminal_status_mutable: bool
    strata: tuple[ExplanatoryStratumSummary, ...]
    fingerprint: str


def _stratum_name(
    *,
    high_uncertainty: bool,
    high_disagreement: bool,
) -> ExplanatoryStratum:
    uncertainty = "high" if high_uncertainty else "low"
    disagreement = "high" if high_disagreement else "low"
    return f"{uncertainty}_local_uncertainty_{disagreement}_world_disagreement"  # type: ignore[return-value]


def evaluate_excluded_world_information(
    *,
    outer_unit_id: str,
    thresholds: ExcludedWorldInformationThresholds,
    heldout_rows: Sequence[ExplanatoryHeldoutRow],
    declared_world_count: int,
    surviving_world_count: int,
) -> ExcludedWorldInformationDiagnostic:
    """Evaluate the frozen secondary diagnostic without changing the primary result."""

    unit_id = _clean_required(outer_unit_id, "outer_unit_id")
    if not isinstance(thresholds, ExcludedWorldInformationThresholds):
        raise TypeError("thresholds must be ExcludedWorldInformationThresholds")
    rows = tuple(heldout_rows)
    if not rows:
        raise ValueError("heldout_rows must not be empty")
    if not all(isinstance(row, ExplanatoryHeldoutRow) for row in rows):
        raise TypeError("heldout_rows must contain only ExplanatoryHeldoutRow values")
    ids = tuple(row.row_id for row in rows)
    if len(set(ids)) != len(ids):
        raise ValueError("heldout row_id values must be unique")

    for label, value in (
        ("declared_world_count", declared_world_count),
        ("surviving_world_count", surviving_world_count),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer")
    if surviving_world_count > declared_world_count:
        raise ValueError("surviving_world_count cannot exceed declared_world_count")

    expected_fraction = surviving_world_count / declared_world_count
    if any(
        not math.isclose(
            row.surviving_world_fraction,
            expected_fraction,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        for row in rows
    ):
        raise ValueError(
            "heldout surviving_world_fraction is inconsistent with declared/surviving counts"
        )

    grouped: dict[ExplanatoryStratum, list[ExplanatoryHeldoutRow]] = {
        "low_local_uncertainty_low_world_disagreement": [],
        "low_local_uncertainty_high_world_disagreement": [],
        "high_local_uncertainty_low_world_disagreement": [],
        "high_local_uncertainty_high_world_disagreement": [],
    }
    for row in rows:
        stratum = _stratum_name(
            high_uncertainty=(
                binary_entropy(row.baseline_probability)
                >= thresholds.local_uncertainty_entropy_threshold
            ),
            high_disagreement=(
                row.support_range
                >= thresholds.world_disagreement_support_range_threshold
            ),
        )
        grouped[stratum].append(row)

    stratum_summaries: list[ExplanatoryStratumSummary] = []
    for stratum in grouped:
        subset = tuple(grouped[stratum])
        if subset:
            baseline_losses = tuple(
                binary_log_loss(row.outcome, row.baseline_probability) for row in subset
            )
            augmented_losses = tuple(
                binary_log_loss(row.outcome, row.augmented_probability) for row in subset
            )
            baseline_mean = sum(baseline_losses) / len(subset)
            augmented_mean = sum(augmented_losses) / len(subset)
            delta = augmented_mean - baseline_mean
        else:
            baseline_mean = None
            augmented_mean = None
            delta = None
        event_count = sum(row.outcome for row in subset)
        payload = {
            "stratum": stratum,
            "row_count": len(subset),
            "event_count": event_count,
            "non_event_count": len(subset) - event_count,
            "baseline_mean_log_loss": baseline_mean,
            "augmented_mean_log_loss": augmented_mean,
            "augmented_minus_baseline_mean_log_loss": delta,
        }
        stratum_summaries.append(
            ExplanatoryStratumSummary(
                stratum=stratum,
                row_count=len(subset),
                event_count=event_count,
                non_event_count=len(subset) - event_count,
                baseline_mean_log_loss=baseline_mean,
                augmented_mean_log_loss=augmented_mean,
                augmented_minus_baseline_mean_log_loss=delta,
                fingerprint=_canonical_sha256(payload),
            )
        )

    baseline_losses = tuple(
        binary_log_loss(row.outcome, row.baseline_probability) for row in rows
    )
    augmented_losses = tuple(
        binary_log_loss(row.outcome, row.augmented_probability) for row in rows
    )
    baseline_macro = sum(baseline_losses) / len(rows)
    augmented_macro = sum(augmented_losses) / len(rows)
    contraction = 1.0 - expected_fraction
    mean_range = sum(row.support_range for row in rows) / len(rows)
    mean_std = sum(row.support_std for row in rows) / len(rows)
    contingent_fraction = (
        sum(row.structural_status == "contingent" for row in rows) / len(rows)
    )
    informative = any(
        value > 0.0
        for value in (contraction, mean_range, mean_std, contingent_fraction)
    )
    event_count = sum(row.outcome for row in rows)
    payload = {
        "outer_unit_id": unit_id,
        "threshold_fingerprint": thresholds.fingerprint,
        "row_count": len(rows),
        "event_count": event_count,
        "non_event_count": len(rows) - event_count,
        "declared_world_count": declared_world_count,
        "surviving_world_count": surviving_world_count,
        "world_contraction_fraction": contraction,
        "mean_support_range": mean_range,
        "mean_support_std": mean_std,
        "contingent_row_fraction": contingent_fraction,
        "baseline_macro_log_loss": baseline_macro,
        "augmented_macro_log_loss": augmented_macro,
        "augmented_minus_baseline_log_loss": augmented_macro - baseline_macro,
        "structurally_informative": informative,
        "primary_terminal_status_mutable": False,
        "strata": [
            {
                "stratum": summary.stratum,
                "fingerprint": summary.fingerprint,
            }
            for summary in stratum_summaries
        ],
    }
    return ExcludedWorldInformationDiagnostic(
        outer_unit_id=unit_id,
        threshold_fingerprint=thresholds.fingerprint,
        row_count=len(rows),
        event_count=event_count,
        non_event_count=len(rows) - event_count,
        declared_world_count=declared_world_count,
        surviving_world_count=surviving_world_count,
        world_contraction_fraction=contraction,
        mean_support_range=mean_range,
        mean_support_std=mean_std,
        contingent_row_fraction=contingent_fraction,
        baseline_macro_log_loss=baseline_macro,
        augmented_macro_log_loss=augmented_macro,
        augmented_minus_baseline_log_loss=augmented_macro - baseline_macro,
        structurally_informative=informative,
        primary_terminal_status_mutable=False,
        strata=tuple(stratum_summaries),
        fingerprint=_canonical_sha256(payload),
    )
