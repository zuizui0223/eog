"""Conditional source projection after DECLARED independent directed-edge evidence.

The same already-defined native EOG graph rule universe is filtered by
externally DECLARED directed edge statuses before projecting source hypotheses.
A declared zero-support edge is NOT an empirically verified dispersal barrier;
these statements are assertions, not validated here. Missing species
detections and unsurveyed/missing network rows are NEVER structural nonedges.

All post-filter compatibility and projection use the native EOG v2 source
hypothesis APIs, no new movement fit, ecology posterior, historical origin
claim, response access, or EOG-WF endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Sequence

from ..dynamic_island_reachability import DynamicTransitionOperator
from .fixed_source_hypothesis_sensitivity import (
    FixedSourceHypothesisIdentifiability,
    audit_fixed_source_hypotheses,
    summarize_fixed_source_hypothesis_identifiability,
)

EdgeStatus = Literal["present", "structurally_unavailable"]
EvidenceBasis = Literal[
    "synthetic_known_truth", "declared_external_structural_assessment"
]
_ALLOWED_STATUSES = frozenset(("present", "structurally_unavailable"))
_ALLOWED_BASES = frozenset((
    "synthetic_known_truth", "declared_external_structural_assessment"
))


def _digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class DeclaredDirectedEdgeEvidence:
    """Caller-declared edge-state statement, NOT independent field validation."""

    source_id: str
    target_id: str
    status: EdgeStatus
    evidence_basis: EvidenceBasis
    evidence_ref: str


@dataclass(frozen=True)
class DirectedNetworkEvidenceSourceProjection:
    """Exact finite rule/source evidence projection, conditional on declarations.

    This result cannot validate claimed external edge measurements, identify
    historical founders, or claim true ecological movement impossibility.
    """

    declared_edge_evidence: tuple[DeclaredDirectedEdgeEvidence, ...]
    original_rule_operator_fingerprints: tuple[tuple[str, str], ...]
    admitted_rule_ids: tuple[str, ...]
    excluded_rule_ids: tuple[str, ...]
    before_source_projection: FixedSourceHypothesisIdentifiability
    after_source_projection: FixedSourceHypothesisIdentifiability | None
    compatible_pairs_before: int
    compatible_pairs_after: int
    possible_source_hypotheses_before: tuple[str, ...]
    possible_source_hypotheses_after: tuple[str, ...]
    source_identification_status: str
    source_historical_origin_verified: bool
    input_structural_edge_truth_independently_verified: bool
    omitted_species_records_are_NOT_structural_absence_evidence: bool
    max_steps: int
    coverage_certificate: str
    fingerprint: str


def audit_declared_directed_network_evidence(
    operators: Mapping[str, DynamicTransitionOperator],
    positive_occurrence_ids: Sequence[str],
    source_hypotheses: Mapping[str, Sequence[str]],
    evidence: Sequence[DeclaredDirectedEdgeEvidence],
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> DirectedNetworkEvidenceSourceProjection:
    """Safely apply explicitly declared edge statuses to a frozen graph roster.

    Preconditions:
      - All graph rules have the same original node universe/order, and all
        source hypotheses remain within the same observed positive nodes.
      - Every directed-edge declaration has an explicit status, a stated
        provenance *basis* and a nonblank source reference.
      - Status 'structurally_unavailable' refers to a DECLARED zero-support
        directed graph edge; no survey nondetection can be passed as that
        status, and no externally declared basis is independently checked.
      - Selected graph operators are the ORIGINAL unchanged objects.
      - A zero-graph result is a declared-universe STOP, never a unique source.

    The result is a conditional finite candidate-rule statement, not a
    transport, detection, occupancy or historical-source inference.
    """
    parent = audit_fixed_source_hypotheses(
        operators, positive_occurrence_ids, source_hypotheses,
        max_steps=max_steps,
        support_floor=support_floor,
        support_tolerance=support_tolerance,
    )
    before = summarize_fixed_source_hypothesis_identifiability(parent)
    node_ids = next(iter(operators.values())).node_ids
    if isinstance(evidence, (str, bytes)):
        raise ValueError("edge evidence must be a sequence of declarations")
    raw_evidence = tuple(evidence)
    seen = set()
    for row in raw_evidence:
        if not isinstance(row, DeclaredDirectedEdgeEvidence):
            raise TypeError("each edge evidence row must be DeclaredDirectedEdgeEvidence")
        if (not isinstance(row.source_id, str) or
            not isinstance(row.target_id, str) or
            row.source_id not in node_ids or row.target_id not in node_ids):
            raise ValueError("edge endpoints must be known frozen graph node IDs")
        if row.source_id == row.target_id:
            raise ValueError("self-loop edge evidence is not part of this graph universe")
        if row.status not in _ALLOWED_STATUSES:
            raise ValueError("edge status must be present or structurally_unavailable")
        if row.evidence_basis not in _ALLOWED_BASES:
            raise ValueError(
                "evidence_basis must be synthetic_known_truth or "
                "declared_external_structural_assessment; a field species "
                "nondetection is NOT a structural nonedge"
            )
        if not isinstance(row.evidence_ref, str) or not row.evidence_ref.strip():
            raise ValueError("every edge statement needs a nonblank evidence_ref")
        key = (row.source_id, row.target_id)
        if key in seen:
            raise ValueError("duplicate or contradictory directed edge evidence")
        seen.add(key)
    ordered = tuple(sorted(
        raw_evidence, key=lambda x:(x.source_id, x.target_id)
    ))

    index = {n: i for i, n in enumerate(node_ids)}
    original_ids = tuple(row.rule_id for row in parent.rule_status)
    old_fingerprints = parent.rule_operator_fingerprints
    admissible: dict[str, DynamicTransitionOperator] = {}
    for rule_id in original_ids:
        op = operators[rule_id]
        if all(
            (float(op.transition[index[statement.source_id],
                                 index[statement.target_id]]) > 0.0)
            == (statement.status == "present")
            for statement in ordered
        ):
            admissible[rule_id] = op
    selected_ids = tuple(admissible)
    excluded_ids = tuple(k for k in original_ids if k not in admissible)
    if len(selected_ids) + len(excluded_ids) != len(original_ids):
        raise RuntimeError("candidate graph identity coverage is incomplete")

    if not admissible:
        after = None
        possible = ()
        pair_count = 0
        status = "declared_graph_rule_universe_exhausted"
    else:
        # All selected graph objects and their fingerprints are unchanged.
        # Evidence filters graph identity, not the source policy or rule.
        new_parent = audit_fixed_source_hypotheses(
            admissible, positive_occurrence_ids, source_hypotheses,
            max_steps=max_steps, support_floor=support_floor,
            support_tolerance=support_tolerance
        )
        if tuple(
            (rid, op.fingerprint) for rid, op in admissible.items()
        ) != new_parent.rule_operator_fingerprints:
            raise RuntimeError("frozen rule operators changed during evidence filter")
        after = summarize_fixed_source_hypothesis_identifiability(new_parent)
        possible = after.possible_source_hypotheses_after_marginalizing_rule
        pair_count = after.compatible_rule_source_assignment_count
        if pair_count == 0:
            status = "declared_graph_source_pair_universe_falsified"
        elif len(parent.source_hypotheses) == 1:
            status = "single_source_hypothesis_declared_not_identified"
        elif len(possible) == 1:
            status = "one_source_supported_within_declared_edge_rule_universe"
        else:
            status = "multiple_sources_possible_under_declared_edge_evidence"

    cert = "declared_edge_states_on_frozen_EOG_rule_universe_not_field_verification"
    payload = {
        "declared_edge_evidence": [
            {
                "source_id":row.source_id,
                "target_id":row.target_id,
                "status":row.status,
                "evidence_basis":row.evidence_basis,
                "evidence_ref":row.evidence_ref,
            }for row in ordered
        ],
        "original_rule_operator_fingerprints":old_fingerprints,
        "admitted_rule_ids":selected_ids,
        "excluded_rule_ids":excluded_ids,
        "before_source_projection_fingerprint":before.fingerprint,
        "after_source_projection_fingerprint":(
            after.fingerprint if after is not None else None
        ),
        "compatible_pairs_before":before.compatible_rule_source_assignment_count,
        "compatible_pairs_after":pair_count,
        "possible_source_hypotheses_before":(
            before.possible_source_hypotheses_after_marginalizing_rule
        ),
        "possible_source_hypotheses_after":possible,
        "source_identification_status":status,
        "source_historical_origin_verified":False,
        "input_structural_edge_truth_independently_verified":False,
        "omitted_species_records_are_NOT_structural_absence_evidence":True,
        "max_steps":max_steps,
        "coverage_certificate":cert
    }
    return DirectedNetworkEvidenceSourceProjection(
        declared_edge_evidence=ordered,
        original_rule_operator_fingerprints=old_fingerprints,
        admitted_rule_ids=selected_ids,
        excluded_rule_ids=excluded_ids,
        before_source_projection=before,
        after_source_projection=after,
        compatible_pairs_before=before.compatible_rule_source_assignment_count,
        compatible_pairs_after=pair_count,
        possible_source_hypotheses_before=(
            before.possible_source_hypotheses_after_marginalizing_rule
        ),
        possible_source_hypotheses_after=possible,
        source_identification_status=status,
        source_historical_origin_verified=False,
        input_structural_edge_truth_independently_verified=False,
        omitted_species_records_are_NOT_structural_absence_evidence=True,
        max_steps=max_steps,
        coverage_certificate=cert,
        fingerprint=_digest(payload)
    )
