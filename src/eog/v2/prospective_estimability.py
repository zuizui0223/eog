"""Prospective response-blind estimability screening for fresh EOG validation systems.

The purpose of this module is narrow: use only pre-response aggregate study evidence to
reject systems that are clearly too sparse for a frozen validation endpoint, or mark
them uncertain before any row-level ecological response is opened.

It is validation infrastructure, not an ecological operator and not evidence of model
performance.  A prospective PASS means only that published aggregate evidence makes
the planned empirical endpoint plausibly estimable.  The once-only empirical runner
must still enforce its exact row-level count gate after response access.

An ``uncertain_pre_response`` result is deliberately different from both PASS and known
ineligibility.  It never authorizes response access, but it may continue through purely
response-blind gates.  If all those gates are frozen, the unchanged once-only empirical
runner may then open the response and enforce the exact count gate *before* any model is
fit or any held-out prediction is scored.  This mirrors the already-used Chiricahua
execution order without weakening any count threshold.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping


ProspectiveEstimabilityStatus = Literal[
    "plausibly_eligible_pre_response",
    "ineligible_pre_response",
    "uncertain_pre_response",
]

ProspectiveEstimabilityDisposition = Literal[
    "continue_response_blind_with_pre_response_support",
    "continue_response_blind_exact_gate_required",
    "stop_known_ineligible_pre_response",
]

REQUIRED_KEYS = (
    "calibration_events",
    "calibration_non_events",
    "heldout_events",
    "heldout_non_events",
    "heldout_outer_units_with_both_classes",
)


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


def _validated_count(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer or None")
    return value


@dataclass(frozen=True)
class AggregateCountInterval:
    """Published or documented count interval for one planned validation quantity."""

    lower: int | None = None
    upper: int | None = None

    def __post_init__(self) -> None:
        lower = _validated_count(self.lower, "lower")
        upper = _validated_count(self.upper, "upper")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("aggregate count lower bound cannot exceed upper bound")


@dataclass(frozen=True)
class ProspectiveEstimabilityDeclaration:
    """Frozen minimum counts required by the planned empirical endpoint."""

    calibration_events: int
    calibration_non_events: int
    heldout_events: int
    heldout_non_events: int
    heldout_outer_units_with_both_classes: int

    def __post_init__(self) -> None:
        for key in REQUIRED_KEYS:
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a non-negative integer")


@dataclass(frozen=True)
class AggregateEstimabilityEvidence:
    """Pre-response aggregate evidence with an explicit semantic-match declaration."""

    source_label: str
    endpoint_definition_matches: bool
    response_rows_opened: bool
    intervals: Mapping[str, AggregateCountInterval]
    note: str = ""

    def __post_init__(self) -> None:
        if not str(self.source_label).strip():
            raise ValueError("source_label must be non-empty")
        if self.response_rows_opened:
            raise ValueError(
                "prospective estimability evidence must be fixed before row-level response access"
            )
        unknown = set(self.intervals).difference(REQUIRED_KEYS)
        if unknown:
            raise ValueError(f"unsupported estimability evidence keys: {sorted(unknown)}")
        for key, interval in self.intervals.items():
            if not isinstance(interval, AggregateCountInterval):
                raise TypeError(f"interval for {key!r} must be AggregateCountInterval")


@dataclass(frozen=True)
class ProspectiveEstimabilityResult:
    status: ProspectiveEstimabilityStatus
    required_counts: tuple[tuple[str, int], ...]
    evidence_intervals: tuple[tuple[str, int | None, int | None], ...]
    failing_keys: tuple[str, ...]
    unresolved_keys: tuple[str, ...]
    source_label: str
    endpoint_definition_matches: bool
    note: str
    fingerprint: str


def prospective_estimability_disposition(
    result: ProspectiveEstimabilityResult,
) -> ProspectiveEstimabilityDisposition:
    """Return the allowed *pre-response* execution path for a screening result.

    This function never authorizes row-level response access.

    ``ineligible_pre_response``
        A known upper bound already violates a frozen minimum.  Stop before any further
        candidate-specific validation work that would only serve this empirical test.

    ``uncertain_pre_response``
        Published/documented aggregate evidence is incomplete.  The candidate may
        continue through response-blind source/geometry/scale/implementation freezes,
        but an unchanged once-only empirical runner must enforce the exact row-level
        count gate before fitting or scoring.  Uncertainty is not silently promoted to
        PASS.

    ``plausibly_eligible_pre_response``
        Published lower bounds clear all minima.  Response-blind work may continue, but
        the exact once-only row-level gate remains mandatory because aggregate evidence
        is only a prospective screen.
    """

    if not isinstance(result, ProspectiveEstimabilityResult):
        raise TypeError("result must be ProspectiveEstimabilityResult")
    if result.status == "ineligible_pre_response":
        return "stop_known_ineligible_pre_response"
    if result.status == "uncertain_pre_response":
        return "continue_response_blind_exact_gate_required"
    return "continue_response_blind_with_pre_response_support"


def evaluate_prospective_estimability(
    declaration: ProspectiveEstimabilityDeclaration,
    evidence: AggregateEstimabilityEvidence,
) -> ProspectiveEstimabilityResult:
    """Screen a candidate without opening row-level response data.

    Rules are intentionally conservative:

    * if the published/documented endpoint does not match the planned endpoint, return
      ``uncertain_pre_response``;
    * if any known upper bound is below the frozen required minimum, return
      ``ineligible_pre_response``;
    * PASS only when every required quantity has a known lower bound at or above the
      frozen minimum;
    * otherwise return ``uncertain_pre_response``.

    The result classifies pre-response evidence only.  Use
    :func:`prospective_estimability_disposition` to determine whether additional
    response-blind validation work is allowed.  Any eventual empirical run must still
    enforce the exact row-level count gate before model fitting/scoring.
    """

    required = tuple((key, int(getattr(declaration, key))) for key in REQUIRED_KEYS)
    intervals = tuple(
        (
            key,
            evidence.intervals.get(key, AggregateCountInterval()).lower,
            evidence.intervals.get(key, AggregateCountInterval()).upper,
        )
        for key in REQUIRED_KEYS
    )

    failing: list[str] = []
    unresolved: list[str] = []

    if evidence.endpoint_definition_matches:
        for key, minimum in required:
            interval = evidence.intervals.get(key, AggregateCountInterval())
            if interval.upper is not None and interval.upper < minimum:
                failing.append(key)
            elif interval.lower is None or interval.lower < minimum:
                unresolved.append(key)
    else:
        unresolved.extend(REQUIRED_KEYS)

    if failing:
        status: ProspectiveEstimabilityStatus = "ineligible_pre_response"
    elif unresolved:
        status = "uncertain_pre_response"
    else:
        status = "plausibly_eligible_pre_response"

    payload = {
        "status": status,
        "required_counts": [list(row) for row in required],
        "evidence_intervals": [list(row) for row in intervals],
        "failing_keys": failing,
        "unresolved_keys": unresolved,
        "source_label": evidence.source_label,
        "endpoint_definition_matches": evidence.endpoint_definition_matches,
        "note": evidence.note,
    }
    return ProspectiveEstimabilityResult(
        status=status,
        required_counts=required,
        evidence_intervals=intervals,
        failing_keys=tuple(failing),
        unresolved_keys=tuple(unresolved),
        source_label=evidence.source_label,
        endpoint_definition_matches=evidence.endpoint_definition_matches,
        note=evidence.note,
        fingerprint=_canonical_sha256(payload),
    )
