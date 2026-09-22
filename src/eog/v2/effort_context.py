"""Response-independent effort/context ledgers for generic EOG-WF adapters.

Different monitoring systems compute effort differently: deployment coverage, recorder
occasions, receiver activity, completed transects, or another declared design. EOG does
not need to standardize those raw calculations. It needs a common auditable boundary
stating which node-context units were eligible before focal outcomes were opened.

This module therefore records eligibility decisions and their provenance. Evidence
declared as focal-response-derived is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

from eog.v2.problem_contract import CandidateUnit


EffortEvidenceSource = Literal[
    "response_independent_registry",
    "response_independent_effort",
    "response_independent_design",
]
EffortAnalysisRole = Literal["scored", "initialization_only", "unsurveyed"]


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


@dataclass(frozen=True)
class EffortEligibilityPolicy:
    """Prospective description of how surveyed candidate units are defined."""

    unit_definition: str
    eligibility_rule: str
    unsurveyed_rule: str
    evidence_source: EffortEvidenceSource

    def __post_init__(self) -> None:
        for field in ("unit_definition", "eligibility_rule", "unsurveyed_rule"):
            value = _text(getattr(self, field), field)
            if value != getattr(self, field):
                object.__setattr__(self, field, value)
        if self.evidence_source not in {
            "response_independent_registry",
            "response_independent_effort",
            "response_independent_design",
        }:
            raise ValueError(
                "effort evidence must come from a declared response-independent source"
            )

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "schema": "eog.effort_eligibility_policy.v1",
                "unit_definition": self.unit_definition,
                "eligibility_rule": self.eligibility_rule,
                "unsurveyed_rule": self.unsurveyed_rule,
                "evidence_source": self.evidence_source,
            }
        )


@dataclass(frozen=True)
class EffortContextRow:
    """One potential node-context unit and its pre-response effort decision."""

    unit_id: str
    node_id: str
    context_id: str
    fold: int
    eligible: bool
    evidence_summary: str
    evidence_fingerprint: str
    analysis_role: EffortAnalysisRole | None = None

    def __post_init__(self) -> None:
        for field in ("unit_id", "node_id", "context_id", "evidence_summary"):
            value = _text(getattr(self, field), field)
            if value != getattr(self, field):
                object.__setattr__(self, field, value)
        if isinstance(self.fold, bool) or not isinstance(self.fold, int) or self.fold <= 0:
            raise ValueError("fold must be a positive integer")
        role = self.analysis_role
        if role is None:
            role = "scored" if self.eligible else "unsurveyed"
            object.__setattr__(self, "analysis_role", role)
        if role not in {"scored", "initialization_only", "unsurveyed"}:
            raise ValueError("unsupported effort analysis_role")
        if self.eligible and role == "unsurveyed":
            raise ValueError("eligible effort rows cannot use unsurveyed analysis_role")
        if (not self.eligible) and role != "unsurveyed":
            raise ValueError(
                "ineligible effort rows must use unsurveyed analysis_role"
            )
        fingerprint = str(self.evidence_fingerprint).strip().lower()
        if len(fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in fingerprint
        ):
            raise ValueError(
                "evidence_fingerprint must be a 64-character hexadecimal digest"
            )
        if fingerprint != self.evidence_fingerprint:
            object.__setattr__(self, "evidence_fingerprint", fingerprint)


@dataclass(frozen=True)
class EffortContextLedger:
    """Canonical potential-unit ledger with eligible CandidateUnit projection."""

    rows: tuple[EffortContextRow, ...]
    candidate_units: tuple[CandidateUnit, ...]
    initialization_unit_ids: tuple[str, ...]
    unsurveyed_unit_ids: tuple[str, ...]
    candidate_count: int
    initialization_count: int
    surveyed_count: int
    unsurveyed_count: int
    node_count: int
    context_count: int
    policy_fingerprint: str
    fingerprint: str


def evidence_fingerprint(payload: object) -> str:
    """Hash one response-independent effort evidence payload."""

    return _sha256(
        {
            "schema": "eog.effort_evidence.v1",
            "payload": payload,
        }
    )


def freeze_effort_context_ledger(
    *,
    node_ids: Sequence[str],
    context_ids: Sequence[str],
    rows: Sequence[EffortContextRow],
    policy: EffortEligibilityPolicy,
) -> EffortContextLedger:
    """Validate and freeze candidate eligibility before focal response access."""

    nodes = tuple(_text(value, "node_id") for value in node_ids)
    contexts = tuple(_text(value, "context_id") for value in context_ids)
    if not nodes or len(nodes) != len(set(nodes)):
        raise ValueError("node_ids must be non-empty and unique")
    if not contexts or len(contexts) != len(set(contexts)):
        raise ValueError("context_ids must be non-empty and unique")

    values = tuple(rows)
    if not values:
        raise ValueError("effort ledger rows must not be empty")
    if any(not isinstance(row, EffortContextRow) for row in values):
        raise TypeError("rows must contain EffortContextRow values")
    unit_ids = [row.unit_id for row in values]
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("effort ledger unit IDs must be unique")

    node_set = set(nodes)
    context_set = set(contexts)
    for row in values:
        if row.node_id not in node_set:
            raise ValueError(f"effort row references unknown node: {row.node_id}")
        if row.context_id not in context_set:
            raise ValueError(f"effort row references unknown context: {row.context_id}")

    ordered = tuple(sorted(values, key=lambda row: row.unit_id))
    candidate_units = tuple(
        CandidateUnit(
            unit_id=row.unit_id,
            node_id=row.node_id,
            context_id=row.context_id,
            fold=row.fold,
        )
        for row in ordered
        if row.analysis_role == "scored"
    )
    if not candidate_units:
        raise ValueError("effort ledger contains no scored candidate units")
    initialization = tuple(
        row.unit_id for row in ordered if row.analysis_role == "initialization_only"
    )
    unsurveyed = tuple(
        row.unit_id for row in ordered if row.analysis_role == "unsurveyed"
    )
    surveyed_count = len(candidate_units) + len(initialization)

    payload = {
        "schema": "eog.effort_context_ledger.v1",
        "node_ids": list(nodes),
        "context_ids": list(contexts),
        "policy_fingerprint": policy.fingerprint,
        "rows": [
            {
                "unit_id": row.unit_id,
                "node_id": row.node_id,
                "context_id": row.context_id,
                "fold": row.fold,
                "eligible": bool(row.eligible),
                "analysis_role": row.analysis_role,
                "evidence_summary": row.evidence_summary,
                "evidence_fingerprint": row.evidence_fingerprint,
            }
            for row in ordered
        ],
        "candidate_unit_ids": [unit.unit_id for unit in candidate_units],
        "initialization_unit_ids": list(initialization),
        "unsurveyed_unit_ids": list(unsurveyed),
    }
    return EffortContextLedger(
        rows=ordered,
        candidate_units=candidate_units,
        initialization_unit_ids=initialization,
        unsurveyed_unit_ids=unsurveyed,
        candidate_count=len(candidate_units),
        initialization_count=len(initialization),
        surveyed_count=surveyed_count,
        unsurveyed_count=len(unsurveyed),
        node_count=len(nodes),
        context_count=len(contexts),
        policy_fingerprint=policy.fingerprint,
        fingerprint=_sha256(payload),
    )
