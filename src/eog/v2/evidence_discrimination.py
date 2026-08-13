"""Independent directional evidence for discriminating EOG v2 transition rules.

This module is intentionally downstream of occurrence-rule compatibility. It evaluates
prospectively declared directional/order evidence against frozen transition operators.
The outputs are qualitative evidence statuses under declared thresholds; they are not
posterior model probabilities, migration rates, ancestry estimates, or unique route
reconstructions.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Sequence

import numpy as np

from ..dynamic_island_reachability import DynamicTransitionOperator, summarize_first_passage
from .occurrence_constraints import OccurrenceRuleComparison


DirectionalStatus = Literal[
    "supports_declared_direction",
    "contradicts_declared_direction",
    "bidirectional_or_ambiguous",
    "unresolved",
]
CombinedRuleStatus = Literal[
    "occurrence_incompatible",
    "contradicted_by_directional_evidence",
    "compatible_with_occurrence_and_direction",
    "indistinguishable_directional_evidence",
    "unresolved",
]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class DirectionalOrderConstraint:
    """Independent evidence that one declared node precedes/reaches another."""

    earlier_id: str
    later_id: str
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.earlier_id.strip() or not self.later_id.strip() or not self.evidence_id.strip():
            raise ValueError("directional constraint IDs must be non-empty")
        if self.earlier_id == self.later_id:
            raise ValueError("earlier_id and later_id must differ")


@dataclass(frozen=True)
class DirectionalEvidenceRow:
    evidence_id: str
    earlier_id: str
    later_id: str
    forward_support: float
    reverse_support: float
    log_support_ratio: float | None
    status: DirectionalStatus


@dataclass(frozen=True)
class DirectionalRuleEvidence:
    rule_id: str
    rows: tuple[DirectionalEvidenceRow, ...]
    supports_count: int
    contradicts_count: int
    ambiguous_count: int
    unresolved_count: int
    max_steps: int
    minimum_support_ratio: float
    support_tolerance: float
    operator_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class RuleEvidenceStatus:
    rule_id: str
    occurrence_coverage: float
    occurrence_fingerprint: str
    directional_fingerprint: str
    status: CombinedRuleStatus


@dataclass(frozen=True)
class TransitionRuleEvidenceComparison:
    rule_statuses: tuple[RuleEvidenceStatus, ...]
    occurrence_comparison_fingerprint: str
    directional_evidence_fingerprints: tuple[str, ...]
    fingerprint: str


def _classify_direction(
    forward: float,
    reverse: float,
    *,
    minimum_support_ratio: float,
    support_tolerance: float,
) -> tuple[DirectionalStatus, float | None]:
    if forward <= support_tolerance and reverse <= support_tolerance:
        return "unresolved", None
    if forward > support_tolerance and reverse <= support_tolerance:
        return "supports_declared_direction", None
    if forward <= support_tolerance and reverse > support_tolerance:
        return "contradicts_declared_direction", None

    log_ratio = float(np.log(forward) - np.log(reverse))
    threshold = float(np.log(minimum_support_ratio))
    if log_ratio >= threshold:
        return "supports_declared_direction", log_ratio
    if log_ratio <= -threshold:
        return "contradicts_declared_direction", log_ratio
    return "bidirectional_or_ambiguous", log_ratio


def evaluate_directional_order_evidence(
    operator: DynamicTransitionOperator,
    constraints: Sequence[DirectionalOrderConstraint],
    *,
    rule_id: str,
    max_steps: int,
    minimum_support_ratio: float = 2.0,
    support_tolerance: float = 1e-15,
) -> DirectionalRuleEvidence:
    """Evaluate independent directional/order evidence against one frozen operator.

    ``minimum_support_ratio`` is a declared evidential resolution threshold, not a
    universal biological constant. If both directions have positive support but differ
    by less than this factor, the result remains ambiguous rather than being forced into
    a direction.
    """

    if not str(rule_id).strip():
        raise ValueError("rule_id must be non-empty")
    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(minimum_support_ratio) or minimum_support_ratio <= 1.0:
        raise ValueError("minimum_support_ratio must be finite and > 1")
    if not np.isfinite(support_tolerance) or support_tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")

    declared = tuple(constraints)
    if not declared:
        raise ValueError("at least one directional constraint is required")
    evidence_ids = [constraint.evidence_id for constraint in declared]
    if len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError("directional evidence IDs must be unique")
    node_set = set(operator.node_ids)
    for constraint in declared:
        if constraint.earlier_id not in node_set or constraint.later_id not in node_set:
            raise ValueError("directional evidence nodes must occur in the transition operator")

    ordered = tuple(sorted(declared, key=lambda item: item.evidence_id))
    rows: list[DirectionalEvidenceRow] = []
    for constraint in ordered:
        forward = summarize_first_passage(
            operator,
            [constraint.earlier_id],
            constraint.later_id,
            max_steps=max_steps,
            support_tolerance=support_tolerance,
        ).horizon_support
        reverse = summarize_first_passage(
            operator,
            [constraint.later_id],
            constraint.earlier_id,
            max_steps=max_steps,
            support_tolerance=support_tolerance,
        ).horizon_support
        status, log_ratio = _classify_direction(
            float(forward),
            float(reverse),
            minimum_support_ratio=minimum_support_ratio,
            support_tolerance=support_tolerance,
        )
        rows.append(
            DirectionalEvidenceRow(
                evidence_id=constraint.evidence_id,
                earlier_id=constraint.earlier_id,
                later_id=constraint.later_id,
                forward_support=float(forward),
                reverse_support=float(reverse),
                log_support_ratio=log_ratio,
                status=status,
            )
        )

    counts = {
        status: sum(row.status == status for row in rows)
        for status in (
            "supports_declared_direction",
            "contradicts_declared_direction",
            "bidirectional_or_ambiguous",
            "unresolved",
        )
    }
    payload = {
        "rule_id": str(rule_id),
        "rows": [
            {
                "evidence_id": row.evidence_id,
                "earlier_id": row.earlier_id,
                "later_id": row.later_id,
                "forward_support": row.forward_support,
                "reverse_support": row.reverse_support,
                "log_support_ratio": row.log_support_ratio,
                "status": row.status,
            }
            for row in rows
        ],
        "counts": counts,
        "max_steps": int(max_steps),
        "minimum_support_ratio": float(minimum_support_ratio),
        "support_tolerance": float(support_tolerance),
        "operator_fingerprint": operator.fingerprint,
    }
    return DirectionalRuleEvidence(
        rule_id=str(rule_id),
        rows=tuple(rows),
        supports_count=int(counts["supports_declared_direction"]),
        contradicts_count=int(counts["contradicts_declared_direction"]),
        ambiguous_count=int(counts["bidirectional_or_ambiguous"]),
        unresolved_count=int(counts["unresolved"]),
        max_steps=int(max_steps),
        minimum_support_ratio=float(minimum_support_ratio),
        support_tolerance=float(support_tolerance),
        operator_fingerprint=operator.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def combine_occurrence_and_directional_evidence(
    occurrence_comparison: OccurrenceRuleComparison,
    directional_evidence: Mapping[str, DirectionalRuleEvidence],
) -> TransitionRuleEvidenceComparison:
    """Combine evidence as qualitative statuses without selecting a winning rule."""

    occurrence_by_rule = {result.rule_id: result for result in occurrence_comparison.rule_results}
    if set(occurrence_by_rule) != set(directional_evidence):
        raise ValueError("occurrence and directional evidence must cover the same candidate rule IDs")

    statuses: list[RuleEvidenceStatus] = []
    for rule_id in sorted(occurrence_by_rule):
        occurrence = occurrence_by_rule[rule_id]
        directional = directional_evidence[rule_id]
        if occurrence.operator_fingerprint != directional.operator_fingerprint:
            raise ValueError(f"operator fingerprint mismatch for rule {rule_id}")

        if occurrence.coverage_fraction < 1.0:
            status: CombinedRuleStatus = "occurrence_incompatible"
        elif directional.contradicts_count > 0:
            status = "contradicted_by_directional_evidence"
        elif directional.unresolved_count > 0:
            status = "unresolved"
        elif directional.ambiguous_count > 0:
            status = "indistinguishable_directional_evidence"
        else:
            status = "compatible_with_occurrence_and_direction"

        statuses.append(
            RuleEvidenceStatus(
                rule_id=rule_id,
                occurrence_coverage=occurrence.coverage_fraction,
                occurrence_fingerprint=occurrence.fingerprint,
                directional_fingerprint=directional.fingerprint,
                status=status,
            )
        )

    payload = {
        "rule_statuses": [
            {
                "rule_id": row.rule_id,
                "occurrence_coverage": row.occurrence_coverage,
                "occurrence_fingerprint": row.occurrence_fingerprint,
                "directional_fingerprint": row.directional_fingerprint,
                "status": row.status,
            }
            for row in statuses
        ],
        "occurrence_comparison_fingerprint": occurrence_comparison.fingerprint,
        "directional_evidence_fingerprints": [
            directional_evidence[rule_id].fingerprint for rule_id in sorted(directional_evidence)
        ],
    }
    return TransitionRuleEvidenceComparison(
        rule_statuses=tuple(statuses),
        occurrence_comparison_fingerprint=occurrence_comparison.fingerprint,
        directional_evidence_fingerprints=tuple(
            directional_evidence[rule_id].fingerprint for rule_id in sorted(directional_evidence)
        ),
        fingerprint=_canonical_sha256(payload),
    )
