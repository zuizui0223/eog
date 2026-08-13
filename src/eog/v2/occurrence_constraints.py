"""Occurrence-conditioned constraints on candidate EOG v2 transition rules.

This module asks whether a frozen transition operator can support declared observed
occurrences under an explicit source policy. It does not infer a unique historical
route, ancestry, colonisation sequence, migration rate, or occupancy probability.

Two source policies are kept distinct:

- fixed-source: declared historical/training sources are held fixed and only other
  occurrences are evaluated as targets;
- self-excluded: every occurrence is evaluated once as a target while all other
  occurrences act as an equal-weight peer-source envelope.

The self-excluded diagnostic is intentionally not a directional-history test: a true
ancestral source in a one-way colonisation chain need not be reachable from its
descendants.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from ..dynamic_island_reachability import DynamicTransitionOperator, summarize_first_passage


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ordered_subset(operator: DynamicTransitionOperator, values: Sequence[str], label: str) -> tuple[str, ...]:
    requested = tuple(str(value) for value in values)
    if not requested or len(set(requested)) != len(requested):
        raise ValueError(f"{label} must contain unique non-empty node IDs")
    if any(not value.strip() for value in requested):
        raise ValueError(f"{label} must contain unique non-empty node IDs")
    requested_set = set(requested)
    missing = requested_set.difference(operator.node_ids)
    if missing:
        raise ValueError(f"{label} contains nodes outside the transition operator: {sorted(missing)}")
    return tuple(node_id for node_id in operator.node_ids if node_id in requested_set)


@dataclass(frozen=True)
class OccurrenceTargetCompatibility:
    """First-passage compatibility support for one observed target occurrence."""

    target_id: str
    source_ids: tuple[str, ...]
    first_passage_support: float
    first_positive_step: int | None


@dataclass(frozen=True)
class OccurrenceRuleCompatibility:
    """Occurrence constraints and operator permissiveness for one frozen rule."""

    rule_id: str
    source_policy: str
    occurrence_ids: tuple[str, ...]
    fixed_source_ids: tuple[str, ...]
    targets: tuple[OccurrenceTargetCompatibility, ...]
    unsupported_occurrence_ids: tuple[str, ...]
    coverage_fraction: float
    mean_log_support: float
    median_support: float
    operator_mean_outgoing_mass: float
    operator_active_edge_fraction: float
    max_steps: int
    support_floor: float
    operator_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class OccurrenceRuleComparison:
    """Unranked comparison of candidate rules on one declared occurrence set."""

    occurrence_ids: tuple[str, ...]
    rule_results: tuple[OccurrenceRuleCompatibility, ...]
    max_steps: int
    support_floor: float
    fingerprint: str


def _operator_permissiveness(operator: DynamicTransitionOperator) -> tuple[float, float]:
    transition = np.asarray(operator.transition, dtype=float)
    n = transition.shape[0]
    mean_outgoing_mass = float(np.mean(np.sum(transition, axis=1)))
    denominator = n * (n - 1)
    active_edge_fraction = 0.0 if denominator == 0 else float(np.count_nonzero(transition > 0.0) / denominator)
    return mean_outgoing_mass, active_edge_fraction


def evaluate_occurrence_rule_compatibility(
    operator: DynamicTransitionOperator,
    occurrence_ids: Sequence[str],
    *,
    rule_id: str,
    max_steps: int,
    fixed_source_ids: Sequence[str] | None = None,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> OccurrenceRuleCompatibility:
    """Evaluate observed occurrences under one frozen transition rule.

    With ``fixed_source_ids`` supplied, those occurrences are treated as declared
    sources and are excluded from target scoring. Without them, each occurrence is
    self-excluded in turn and all remaining occurrences act as possible sources.

    ``mean_log_support`` uses ``support_floor`` only for numerical reporting. Coverage
    and unsupported-target status use ``support_tolerance`` and therefore preserve
    explicit disconnection.
    """

    if not str(rule_id).strip():
        raise ValueError("rule_id must be non-empty")
    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(support_floor) or not 0.0 < support_floor < 1.0:
        raise ValueError("support_floor must lie strictly between 0 and 1")
    if not np.isfinite(support_tolerance) or support_tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")

    occurrences = _ordered_subset(operator, occurrence_ids, "occurrence_ids")
    if len(occurrences) < 2:
        raise ValueError("at least two occurrence nodes are required")

    if fixed_source_ids is None:
        source_policy = "self_excluded"
        fixed_sources: tuple[str, ...] = ()
        target_ids = occurrences
    else:
        source_policy = "fixed"
        fixed_sources = _ordered_subset(operator, fixed_source_ids, "fixed_source_ids")
        if not set(fixed_sources).issubset(occurrences):
            raise ValueError("fixed_source_ids must be a subset of occurrence_ids")
        target_ids = tuple(node_id for node_id in occurrences if node_id not in set(fixed_sources))
        if not target_ids:
            raise ValueError("fixed-source evaluation requires at least one non-source occurrence target")

    target_rows: list[OccurrenceTargetCompatibility] = []
    for target_id in target_ids:
        if source_policy == "fixed":
            sources = fixed_sources
        else:
            sources = tuple(node_id for node_id in occurrences if node_id != target_id)
        summary = summarize_first_passage(
            operator,
            sources,
            target_id,
            max_steps=max_steps,
            support_tolerance=support_tolerance,
        )
        target_rows.append(
            OccurrenceTargetCompatibility(
                target_id=target_id,
                source_ids=sources,
                first_passage_support=float(summary.horizon_support),
                first_positive_step=summary.first_positive_step,
            )
        )

    support = np.asarray([row.first_passage_support for row in target_rows], dtype=float)
    unsupported = tuple(
        row.target_id for row in target_rows if row.first_passage_support <= support_tolerance
    )
    coverage = float(np.mean(support > support_tolerance))
    mean_log_support = float(np.mean(np.log(np.maximum(support, support_floor))))
    median_support = float(np.median(support))
    mean_outgoing_mass, active_edge_fraction = _operator_permissiveness(operator)

    payload = {
        "rule_id": str(rule_id),
        "source_policy": source_policy,
        "occurrence_ids": list(occurrences),
        "fixed_source_ids": list(fixed_sources),
        "targets": [
            {
                "target_id": row.target_id,
                "source_ids": list(row.source_ids),
                "first_passage_support": row.first_passage_support,
                "first_positive_step": row.first_positive_step,
            }
            for row in target_rows
        ],
        "unsupported_occurrence_ids": list(unsupported),
        "coverage_fraction": coverage,
        "mean_log_support": mean_log_support,
        "median_support": median_support,
        "operator_mean_outgoing_mass": mean_outgoing_mass,
        "operator_active_edge_fraction": active_edge_fraction,
        "max_steps": int(max_steps),
        "support_floor": float(support_floor),
        "operator_fingerprint": operator.fingerprint,
    }
    return OccurrenceRuleCompatibility(
        rule_id=str(rule_id),
        source_policy=source_policy,
        occurrence_ids=occurrences,
        fixed_source_ids=fixed_sources,
        targets=tuple(target_rows),
        unsupported_occurrence_ids=unsupported,
        coverage_fraction=coverage,
        mean_log_support=mean_log_support,
        median_support=median_support,
        operator_mean_outgoing_mass=mean_outgoing_mass,
        operator_active_edge_fraction=active_edge_fraction,
        max_steps=int(max_steps),
        support_floor=float(support_floor),
        operator_fingerprint=operator.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def compare_occurrence_transition_rules(
    operators: Mapping[str, DynamicTransitionOperator],
    occurrence_ids: Sequence[str],
    *,
    max_steps: int,
    fixed_source_ids: Sequence[str] | None = None,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> OccurrenceRuleComparison:
    """Evaluate multiple candidate rules without collapsing them into a winner score.

    Candidate operators must share exactly the same declared node universe and order.
    The result intentionally reports occurrence compatibility and operator
    permissiveness side by side. A more permissive rule may fit every occurrence while
    being less informative; this function does not reward or penalize that trade-off.
    """

    if not operators:
        raise ValueError("operators must contain at least one candidate rule")
    ordered_rules = tuple(sorted((str(rule_id), operator) for rule_id, operator in operators.items()))
    if any(not rule_id.strip() for rule_id, _ in ordered_rules):
        raise ValueError("candidate rule IDs must be non-empty")
    first_nodes = ordered_rules[0][1].node_ids
    if any(operator.node_ids != first_nodes for _, operator in ordered_rules[1:]):
        raise ValueError("candidate operators must share the same node IDs and order")

    occurrence_order = _ordered_subset(ordered_rules[0][1], occurrence_ids, "occurrence_ids")
    results = tuple(
        evaluate_occurrence_rule_compatibility(
            operator,
            occurrence_order,
            rule_id=rule_id,
            max_steps=max_steps,
            fixed_source_ids=fixed_source_ids,
            support_floor=support_floor,
            support_tolerance=support_tolerance,
        )
        for rule_id, operator in ordered_rules
    )
    payload = {
        "occurrence_ids": list(occurrence_order),
        "rule_results": [result.fingerprint for result in results],
        "max_steps": int(max_steps),
        "support_floor": float(support_floor),
    }
    return OccurrenceRuleComparison(
        occurrence_ids=occurrence_order,
        rule_results=results,
        max_steps=int(max_steps),
        support_floor=float(support_floor),
        fingerprint=_canonical_sha256(payload),
    )
