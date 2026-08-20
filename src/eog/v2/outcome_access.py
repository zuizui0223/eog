"""Machine-checkable authorization gate for once-only empirical outcome access.

This module is validation infrastructure, not an ecological operator.  Its purpose is
to ensure that a fresh EOG-WF attempt cannot open row-level outcome data until every
prospectively required scientific/modeling choice has been frozen and fingerprinted.

Authorization means only: the once-only outcome runner may start and must execute the
exact frozen count gate first.  It does *not* authorize model fitting or heldout scoring
unless that exact count gate subsequently passes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping

from .prospective_estimability import (
    ProspectiveEstimabilityResult,
    prospective_estimability_disposition,
)


OutcomeAccessStatus = Literal[
    "authorized_once_only_exact_count_gate_required",
    "blocked_known_ineligible_pre_response",
    "blocked_incomplete_freeze_contract",
    "blocked_safety_contract",
]

REQUIRED_FREEZE_KEYS: tuple[str, ...] = (
    "source_identity",
    "response_identity",
    "node_geometry",
    "response_semantics",
    "temporal_split",
    "count_gate",
    "process_source",
    "world_scale",
    "structural_adequacy",
    "layer_a_rules",
    "layer_b_representation",
    "comparators",
    "preprocessing_model_fit",
    "metrics_decision",
    "runtime_runner",
    "non_estimable_stop",
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


def _clean_text(value: object) -> str:
    return str(value).strip()


@dataclass(frozen=True)
class FrozenOutcomeAccessContract:
    """Response-blind freeze ledger required before the once-only outcome runner."""

    attempt_id: str
    freeze_fingerprints: Mapping[str, str]
    response_rows_opened: bool = False
    exact_count_gate_first: bool = True
    zero_fit_on_count_failure: bool = True
    no_post_open_redesign: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        if not _clean_text(self.attempt_id):
            raise ValueError("attempt_id must be non-empty")
        unknown = set(self.freeze_fingerprints).difference(REQUIRED_FREEZE_KEYS)
        if unknown:
            raise ValueError(f"unsupported outcome-access freeze keys: {sorted(unknown)}")
        if self.response_rows_opened:
            raise ValueError("outcome-access contract must be frozen before row-level response access")

    @property
    def missing_freeze_keys(self) -> tuple[str, ...]:
        return tuple(
            key
            for key in REQUIRED_FREEZE_KEYS
            if not _clean_text(self.freeze_fingerprints.get(key, ""))
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "attempt_id": self.attempt_id,
            "freeze_fingerprints": [
                [key, _clean_text(self.freeze_fingerprints.get(key, ""))]
                for key in REQUIRED_FREEZE_KEYS
            ],
            "response_rows_opened": self.response_rows_opened,
            "exact_count_gate_first": self.exact_count_gate_first,
            "zero_fit_on_count_failure": self.zero_fit_on_count_failure,
            "no_post_open_redesign": self.no_post_open_redesign,
            "note": self.note,
        }
        return _canonical_sha256(payload)


@dataclass(frozen=True)
class OutcomeAccessGateResult:
    """Authorization decision made without inspecting row-level outcome values."""

    status: OutcomeAccessStatus
    authorized: bool
    prospective_disposition: str
    missing_freeze_keys: tuple[str, ...]
    contract_fingerprint: str
    estimability_fingerprint: str
    exact_count_gate_first: bool
    zero_fit_on_count_failure: bool
    no_post_open_redesign: bool
    reason: str
    fingerprint: str


def evaluate_outcome_access_gate(
    contract: FrozenOutcomeAccessContract,
    estimability: ProspectiveEstimabilityResult,
) -> OutcomeAccessGateResult:
    """Decide whether the once-only outcome runner may begin.

    Known pre-response ineligibility always blocks.  Uncertain and prospectively
    supported attempts may be authorized only after the full freeze ledger is complete
    and all safety invariants are explicit.  Even an authorized attempt must run the
    exact frozen count gate before any model fit or heldout score.
    """

    disposition = prospective_estimability_disposition(estimability)
    missing = contract.missing_freeze_keys

    if disposition == "stop_known_ineligible_pre_response":
        status: OutcomeAccessStatus = "blocked_known_ineligible_pre_response"
        reason = "published/documented evidence already proves a frozen minimum cannot be met"
    elif missing:
        status = "blocked_incomplete_freeze_contract"
        reason = "one or more required response-blind scientific/modeling freezes are missing"
    elif not (
        contract.exact_count_gate_first
        and contract.zero_fit_on_count_failure
        and contract.no_post_open_redesign
    ):
        status = "blocked_safety_contract"
        reason = "once-only runner safety invariants are not all enabled"
    else:
        status = "authorized_once_only_exact_count_gate_required"
        reason = (
            "all response-blind freezes are present; outcome runner may begin with the exact "
            "count gate and must stop before fitting/scoring if that gate fails"
        )

    authorized = status == "authorized_once_only_exact_count_gate_required"
    payload = {
        "status": status,
        "authorized": authorized,
        "prospective_disposition": disposition,
        "missing_freeze_keys": list(missing),
        "contract_fingerprint": contract.fingerprint,
        "estimability_fingerprint": estimability.fingerprint,
        "exact_count_gate_first": contract.exact_count_gate_first,
        "zero_fit_on_count_failure": contract.zero_fit_on_count_failure,
        "no_post_open_redesign": contract.no_post_open_redesign,
        "reason": reason,
    }
    return OutcomeAccessGateResult(
        status=status,
        authorized=authorized,
        prospective_disposition=disposition,
        missing_freeze_keys=missing,
        contract_fingerprint=contract.fingerprint,
        estimability_fingerprint=estimability.fingerprint,
        exact_count_gate_first=contract.exact_count_gate_first,
        zero_fit_on_count_failure=contract.zero_fit_on_count_failure,
        no_post_open_redesign=contract.no_post_open_redesign,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
