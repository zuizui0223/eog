"""Safe EOG rule comparison when a positive-occurrence observation is filtered.

The same operator map, horizon, support thresholds and source policy are
passed to both native EOG compatibility evaluations. Fixed-source monotonic
set inclusion is enforced; self-excluded peer sources can change, so their
compatible rule sets are compared by exact identity, never fixed-world logic.

This module makes no claims of true biological absence, occupancy,
identifiability of natural movement worlds, or causal restoration effects.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from ..dynamic_island_reachability import DynamicTransitionOperator
from .occurrence_constraints import compare_occurrence_transition_rules


def _canonical_digest(data: object) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True)
class RetainedTargetSourceChange:
    """Changed peer-source identities for a retained positive target."""

    rule_id: str
    target_id: str
    sources_before: tuple[str, ...]
    sources_after: tuple[str, ...]
    support_before: float
    support_after: float


@dataclass(frozen=True)
class OccurrenceEvidenceFilterAudit:
    """One source-policy-labeled audit over a frozen candidate rule universe.

    World counts here refer to candidate *rules*, NOT an empirical finite
    universe of ecological histories. Neither zeros nor filtered records are
    evidence of verified biological absence.
    """

    source_policy: str
    full_occurrence_ids: tuple[str, ...]
    filtered_occurrence_ids: tuple[str, ...]
    removed_occurrence_ids: tuple[str, ...]
    operator_fingerprints: tuple[tuple[str, str], ...]
    full_compatible_rule_ids: tuple[str, ...]
    filtered_compatible_rule_ids: tuple[str, ...]
    shared_compatible_rule_ids: tuple[str, ...]
    lost_compatible_rule_ids: tuple[str, ...]
    gained_compatible_rule_ids: tuple[str, ...]
    changed_retained_target_sources: tuple[RetainedTargetSourceChange, ...]
    fixed_source_monotonicity_certified: bool | None
    compatible_sets_nested: bool
    membership_change: str
    max_steps: int
    support_floor: float
    support_tolerance: float
    full_comparison_fingerprint: str
    filtered_comparison_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def audit_occurrence_evidence_filter(
    operators: Mapping[str, DynamicTransitionOperator],
    full_occurrence_ids: Sequence[str],
    filtered_occurrence_ids: Sequence[str],
    *,
    max_steps: int,
    fixed_source_ids: Sequence[str] | None = None,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> OccurrenceEvidenceFilterAudit:
    """Audit removed positive records under fixed or self-excluded sources.

    The filter is a proper subset of the original observed positives.
    It cannot remove a declared fixed source and must retain at least two
    positive nodes. Both native EOG evaluations use the same inputs by
    construction. Self-excluded peers must never be compared using EOG's
    fixed-source world reconstruction comparator.
    """
    if not operators:
        raise ValueError("operators must contain a frozen candidate rule universe")
    canonical_nodes = next(iter(operators.values())).node_ids
    if any(op.node_ids != canonical_nodes for op in operators.values()):
        raise ValueError("all candidate rules must share the same node universe and order")

    def ordered(values: Sequence[str], label: str) -> tuple[str, ...]:
        raw = tuple(str(value) for value in values)
        if (len(raw) < 2 or len(set(raw)) != len(raw)
                or any(not value.strip() for value in raw)):
            raise ValueError(f"{label} requires >=2 unique non-empty observed node IDs")
        if set(raw) - set(canonical_nodes):
            raise ValueError(f"{label} contains nodes outside the frozen universe")
        return tuple(node for node in canonical_nodes if node in set(raw))

    full = ordered(full_occurrence_ids, "full_occurrence_ids")
    filtered = ordered(filtered_occurrence_ids, "filtered_occurrence_ids")
    if not set(filtered) < set(full):
        raise ValueError("filtered_occurrence_ids must be a proper subset of the full positives")

    if fixed_source_ids is None:
        source_policy = "self_excluded"
        fixed_sources = None
    else:
        src = tuple(str(x) for x in fixed_source_ids)
        if not src or len(src) != len(set(src)) or any(not x.strip() for x in src):
            raise ValueError("fixed_source_ids must be unique and nonempty")
        if not set(src) <= set(filtered):
            raise ValueError("positive evidence filter may not remove fixed_source_ids")
        fixed_sources = tuple(node for node in canonical_nodes if node in set(src))
        if len(filtered) <= len(fixed_sources):
            raise ValueError("fixed-source comparison needs at least one surviving non-source target")
        source_policy = "fixed"

    before = compare_occurrence_transition_rules(
        operators, full, max_steps=max_steps,
        fixed_source_ids=fixed_sources,
        support_floor=support_floor, support_tolerance=support_tolerance,
    )
    after = compare_occurrence_transition_rules(
        operators, filtered, max_steps=max_steps,
        fixed_source_ids=fixed_sources,
        support_floor=support_floor, support_tolerance=support_tolerance,
    )
    before_by_rule = {row.rule_id: row for row in before.rule_results}
    after_by_rule = {row.rule_id: row for row in after.rule_results}
    if before_by_rule.keys() != after_by_rule.keys():
        raise RuntimeError("rule identities changed under the observation filter")
    fingerprints = tuple(
        (r.rule_id, r.operator_fingerprint) for r in before.rule_results
    )
    for rule_id, old in before_by_rule.items():
        new = after_by_rule[rule_id]
        if (old.source_policy != source_policy or new.source_policy != source_policy
                or old.operator_fingerprint != new.operator_fingerprint
                or old.max_steps != new.max_steps
                or old.support_floor != new.support_floor):
            raise RuntimeError("operator, source policy or numerical contract drift")

    full_ids = tuple(
        row.rule_id for row in before.rule_results
        if not row.unsupported_occurrence_ids
    )
    filtered_ids = tuple(
        row.rule_id for row in after.rule_results
        if not row.unsupported_occurrence_ids
    )
    bf = set(full_ids)
    af = set(filtered_ids)
    shared = tuple(k for k in full_ids if k in af)
    lost = tuple(k for k in full_ids if k not in af)
    gained = tuple(k for k in filtered_ids if k not in bf)
    if source_policy == "fixed" and lost:
        raise RuntimeError("fixed-source positive-only compatible rule monotonicity violated")

    target_source_changes = []
    for rule_id, old in before_by_rule.items():
        new = after_by_rule[rule_id]
        old_targets = {x.target_id: x for x in old.targets}
        for target in new.targets:
            earlier = old_targets.get(target.target_id)
            if earlier is None:
                raise RuntimeError("filtered observation unexpectedly added a target")
            if earlier.source_ids != target.source_ids:
                target_source_changes.append(
                    RetainedTargetSourceChange(
                        rule_id=rule_id, target_id=target.target_id,
                        sources_before=earlier.source_ids,
                        sources_after=target.source_ids,
                        support_before=earlier.first_passage_support,
                        support_after=target.first_passage_support,
                    )
                )
            elif source_policy == "self_excluded":
                raise RuntimeError("removed positive peer did not alter retained target sources")
    if source_policy == "fixed" and target_source_changes:
        raise RuntimeError("fixed-source filter unexpectedly changed the source identities")

    if gained and lost:
        change = "swapped"
    elif gained:
        change = "expanded"
    elif lost:
        change = "contracted"
    else:
        change = "unchanged"
    certificate = "frozen_candidate_operators_common_source_policy_and_numeric_contract"
    payload = {
        "source_policy": source_policy,
        "full": full, "filtered": filtered,
        "removed": tuple(node for node in full if node not in filtered),
        "operator_fingerprints": fingerprints,
        "full_compatible_rule_ids": full_ids,
        "filtered_compatible_rule_ids": filtered_ids,
        "shared_compatible_rule_ids": shared,
        "lost_compatible_rule_ids": lost,
        "gained_compatible_rule_ids": gained,
        "target_source_changes": [
            {
                "rule": t.rule_id, "target": t.target_id,
                "sources_before": t.sources_before,
                "sources_after": t.sources_after,
                "support_before": t.support_before,
                "support_after": t.support_after,
            }
            for t in target_source_changes
        ],
        "fixed_source_monotonicity_certified": (
            True if source_policy == "fixed" else None
        ),
        "compatible_sets_nested": bf <= af or af <= bf,
        "membership_change": change,
        "max_steps": max_steps,
        "support_floor": support_floor,
        "support_tolerance": support_tolerance,
        "full_comparison_fingerprint": before.fingerprint,
        "filtered_comparison_fingerprint": after.fingerprint,
        "coverage_certificate": certificate,
    }
    return OccurrenceEvidenceFilterAudit(
        source_policy=source_policy,
        full_occurrence_ids=full,
        filtered_occurrence_ids=filtered,
        removed_occurrence_ids=tuple(node for node in full if node not in filtered),
        operator_fingerprints=fingerprints,
        full_compatible_rule_ids=full_ids,
        filtered_compatible_rule_ids=filtered_ids,
        shared_compatible_rule_ids=shared,
        lost_compatible_rule_ids=lost,
        gained_compatible_rule_ids=gained,
        changed_retained_target_sources=tuple(target_source_changes),
        fixed_source_monotonicity_certified=(
            True if source_policy == "fixed" else None
        ),
        compatible_sets_nested=bf <= af or af <= bf,
        membership_change=change,
        max_steps=max_steps,
        support_floor=support_floor,
        support_tolerance=support_tolerance,
        full_comparison_fingerprint=before.fingerprint,
        filtered_comparison_fingerprint=after.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_digest(payload),
    )
