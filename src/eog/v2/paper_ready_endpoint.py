"""Final response-blind binding gate for the third paper-ready EOG endpoint.

This module does not select a dataset, inspect response values, fit a model, or add an
ecological operator. It binds already-existing validation objects so the third fresh
endpoint cannot reach its once-only runner with a detached decision rule, a changed
Layer-B representation, or post-freeze synthesis, placebo, or excluded-world
explanatory contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

from .candidate_preflight import CandidatePreflightDeclaration, CandidatePreflightResult
from .outcome_access import FrozenOutcomeAccessContract, OutcomeAccessGateResult
from .predictive_complementarity import PredictiveComplementarityDeclaration


FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT = (
    "1617b18b6b0c3e2797945c3d30111a4e3e6941a560a6b8a39b8d117e84c82b02"
)
FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT = (
    "72129df202a4d8c0203b507f82c3cbc6c612feb028d12b6386dc39abde4de8cd"
)
FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT = (
    "4fc5818c79cbe026e69f97f1eeb085ee46563e586349ca762b322f67201a08cd"
)


PaperReadyEndpoint3Status = Literal[
    "ready_for_endpoint_3_once_only_runner",
    "blocked_terminal_candidate_reuse",
    "blocked_response_already_opened",
    "blocked_attempt_identity_mismatch",
    "blocked_candidate_preflight",
    "blocked_outcome_access",
    "blocked_metrics_decision_binding",
    "blocked_layer_b_binding",
    "blocked_cross_ecosystem_contract_drift",
    "blocked_feature_count_placebo_contract_drift",
    "blocked_excluded_world_information_contract_drift",
    "blocked_missing_post_terminal_hard_stop",
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


def _clean_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


@dataclass(frozen=True)
class FrozenPaperReadyEndpoint3Boundary:
    """Paper-level freezes that must accompany one fresh endpoint-3 attempt."""

    attempt_id: str
    cross_ecosystem_synthesis_fingerprint: str
    feature_count_placebo_fingerprint: str
    excluded_world_information_fingerprint: str = (
        FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT
    )
    response_rows_opened: bool = False
    reuses_terminal_candidate: bool = False
    stop_candidate_hunting_after_predictive_terminal: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _clean_required(self.attempt_id, "attempt_id"))
        object.__setattr__(
            self,
            "cross_ecosystem_synthesis_fingerprint",
            _clean_required(
                self.cross_ecosystem_synthesis_fingerprint,
                "cross_ecosystem_synthesis_fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "feature_count_placebo_fingerprint",
            _clean_required(
                self.feature_count_placebo_fingerprint,
                "feature_count_placebo_fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "excluded_world_information_fingerprint",
            _clean_required(
                self.excluded_world_information_fingerprint,
                "excluded_world_information_fingerprint",
            ),
        )
        _require_bool(self.response_rows_opened, "response_rows_opened")
        _require_bool(self.reuses_terminal_candidate, "reuses_terminal_candidate")
        _require_bool(
            self.stop_candidate_hunting_after_predictive_terminal,
            "stop_candidate_hunting_after_predictive_terminal",
        )
        if not isinstance(self.note, str):
            raise TypeError("note must be str")

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "attempt_id": self.attempt_id,
                "cross_ecosystem_synthesis_fingerprint": (
                    self.cross_ecosystem_synthesis_fingerprint
                ),
                "feature_count_placebo_fingerprint": self.feature_count_placebo_fingerprint,
                "excluded_world_information_fingerprint": (
                    self.excluded_world_information_fingerprint
                ),
                "response_rows_opened": self.response_rows_opened,
                "reuses_terminal_candidate": self.reuses_terminal_candidate,
                "stop_candidate_hunting_after_predictive_terminal": (
                    self.stop_candidate_hunting_after_predictive_terminal
                ),
                "note": self.note,
            }
        )


@dataclass(frozen=True)
class PaperReadyEndpoint3GateResult:
    """Machine-checkable pre-response receipt for one endpoint-3 attempt."""

    status: PaperReadyEndpoint3Status
    authorized: bool
    attempt_id: str
    boundary_fingerprint: str
    candidate_preflight_fingerprint: str
    outcome_access_fingerprint: str
    predictive_declaration_fingerprint: str
    reason: str
    fingerprint: str


def evaluate_paper_ready_endpoint_3_gate(
    boundary: FrozenPaperReadyEndpoint3Boundary,
    candidate_declaration: CandidatePreflightDeclaration,
    candidate_preflight: CandidatePreflightResult,
    outcome_contract: FrozenOutcomeAccessContract,
    outcome_access: OutcomeAccessGateResult,
    predictive_declaration: PredictiveComplementarityDeclaration,
) -> PaperReadyEndpoint3GateResult:
    """Bind every endpoint-3 paper boundary before once-only response access.

    This is deliberately downstream of the reusable metadata preflight and outcome-
    access gates. It verifies their identities rather than reimplementing their
    scientific decisions. A positive result authorizes only the already-approved
    once-only exact-count-first runner; exact-count failure still stops with zero fits.
    """

    expected_types = (
        (boundary, FrozenPaperReadyEndpoint3Boundary, "boundary"),
        (candidate_declaration, CandidatePreflightDeclaration, "candidate_declaration"),
        (candidate_preflight, CandidatePreflightResult, "candidate_preflight"),
        (outcome_contract, FrozenOutcomeAccessContract, "outcome_contract"),
        (outcome_access, OutcomeAccessGateResult, "outcome_access"),
        (
            predictive_declaration,
            PredictiveComplementarityDeclaration,
            "predictive_declaration",
        ),
    )
    for value, expected, label in expected_types:
        if not isinstance(value, expected):
            raise TypeError(f"{label} must be {expected.__name__}")

    if boundary.reuses_terminal_candidate:
        status: PaperReadyEndpoint3Status = "blocked_terminal_candidate_reuse"
        reason = "a consumed or terminal candidate cannot be repaired or relabeled as endpoint 3"
    elif boundary.response_rows_opened:
        status = "blocked_response_already_opened"
        reason = "the paper-ready endpoint-3 boundary must be frozen before response rows open"
    elif not (
        boundary.attempt_id
        == candidate_declaration.attempt_id
        == outcome_contract.attempt_id
    ):
        status = "blocked_attempt_identity_mismatch"
        reason = "candidate, outcome-access, and paper-boundary attempt identities differ"
    elif (
        not candidate_preflight.ready
        or candidate_preflight.status != "ready_for_geometry_gate"
        or candidate_preflight.declaration_fingerprint != candidate_declaration.fingerprint
    ):
        status = "blocked_candidate_preflight"
        reason = "response-blind candidate preflight is not ready or is detached from its declaration"
    elif (
        not outcome_access.authorized
        or outcome_access.status != "authorized_once_only_exact_count_gate_required"
        or outcome_access.contract_fingerprint != outcome_contract.fingerprint
    ):
        status = "blocked_outcome_access"
        reason = "once-only outcome access is not authorized or is detached from its contract"
    elif (
        str(outcome_contract.freeze_fingerprints.get("metrics_decision", "")).strip()
        != predictive_declaration.fingerprint
    ):
        status = "blocked_metrics_decision_binding"
        reason = "the outcome-access metrics decision does not bind the predictive declaration"
    elif (
        str(outcome_contract.freeze_fingerprints.get("layer_b_representation", "")).strip()
        != predictive_declaration.eog_feature_fingerprint.strip()
    ):
        status = "blocked_layer_b_binding"
        reason = "the outcome-access Layer-B identity does not match the predictive declaration"
    elif (
        boundary.cross_ecosystem_synthesis_fingerprint
        != FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT
    ):
        status = "blocked_cross_ecosystem_contract_drift"
        reason = "the pre-endpoint cross-ecosystem synthesis contract fingerprint changed"
    elif (
        boundary.feature_count_placebo_fingerprint
        != FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT
    ):
        status = "blocked_feature_count_placebo_contract_drift"
        reason = "the pre-endpoint feature-count placebo contract fingerprint changed"
    elif (
        boundary.excluded_world_information_fingerprint
        != FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT
    ):
        status = "blocked_excluded_world_information_contract_drift"
        reason = "the pre-endpoint excluded-world explanatory contract fingerprint changed"
    elif not boundary.stop_candidate_hunting_after_predictive_terminal:
        status = "blocked_missing_post_terminal_hard_stop"
        reason = "endpoint 3 must freeze the stop on further dataset hunting after its terminal result"
    else:
        status = "ready_for_endpoint_3_once_only_runner"
        reason = (
            "all reusable and paper-level freezes are identity-bound; the endpoint-3 runner may "
            "begin once, with the exact count gate first and no post-open redesign"
        )

    authorized = status == "ready_for_endpoint_3_once_only_runner"
    payload = {
        "status": status,
        "authorized": authorized,
        "attempt_id": boundary.attempt_id,
        "boundary_fingerprint": boundary.fingerprint,
        "candidate_preflight_fingerprint": candidate_preflight.fingerprint,
        "outcome_access_fingerprint": outcome_access.fingerprint,
        "predictive_declaration_fingerprint": predictive_declaration.fingerprint,
        "reason": reason,
    }
    return PaperReadyEndpoint3GateResult(
        status=status,
        authorized=authorized,
        attempt_id=boundary.attempt_id,
        boundary_fingerprint=boundary.fingerprint,
        candidate_preflight_fingerprint=candidate_preflight.fingerprint,
        outcome_access_fingerprint=outcome_access.fingerprint,
        predictive_declaration_fingerprint=predictive_declaration.fingerprint,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
