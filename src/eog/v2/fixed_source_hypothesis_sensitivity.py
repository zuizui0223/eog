"""EOG fixed-source hypothesis sensitivity over ONE frozen candidate-rule universe.

This is a *static*, source-declaration-conditional compatibility audit.
Source hypotheses are supplied by the analyst, not inferred as ancestors.
It reports rule identities compatible with all / some / no declared
source hypotheses, without assigning a prior or posterior to hypotheses.

Do not use for time-varying realized sources (sequential_world_forecast),
true biological absence, occupancy, real movement calibration, or EOG-WF
fresh endpoint scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from ..dynamic_island_reachability import DynamicTransitionOperator
from .occurrence_constraints import compare_occurrence_transition_rules


def _digest(data: object) -> str:
    return hashlib.sha256(
        json.dumps(
            data, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class FixedSourceHypothesisResult:
    """One explicitly declared hypothetical fixed-source support state."""

    hypothesis_id: str
    source_ids: tuple[str, ...]
    compatible_rule_ids: tuple[str, ...]
    incompatible_rule_ids: tuple[str, ...]
    comparison_fingerprint: str


@dataclass(frozen=True)
class FixedSourceRuleStatus:
    """Support across source choices plus native operator permissiveness."""

    rule_id: str
    compatible_hypothesis_ids: tuple[str, ...]
    incompatible_hypothesis_ids: tuple[str, ...]
    status: str
    operator_mean_outgoing_mass: float
    operator_active_edge_fraction: float


@dataclass(frozen=True)
class FixedSourceHypothesisSensitivity:
    """Source-robust rule intersection and source-possible rule union.

    This is NOT a world posterior, not self-excluded peer-source
    evaluation, and not a historical source certification.
    """

    positive_occurrence_ids: tuple[str, ...]
    rule_operator_fingerprints: tuple[tuple[str, str], ...]
    source_hypotheses: tuple[FixedSourceHypothesisResult, ...]
    rule_status: tuple[FixedSourceRuleStatus, ...]
    source_robust_rule_ids: tuple[str, ...]
    source_possible_rule_ids: tuple[str, ...]
    source_dependent_rule_ids: tuple[str, ...]
    source_impossible_under_declared_hypotheses_rule_ids: tuple[str, ...]
    max_steps: int
    support_floor: float
    support_tolerance: float
    source_hypotheses_are_NOT_independently_verified_historical_origins: bool
    source_state_scope: str
    coverage_certificate: str
    fingerprint: str


def audit_fixed_source_hypotheses(
    operators: Mapping[str, DynamicTransitionOperator],
    positive_occurrence_ids: Sequence[str],
    source_hypotheses: Mapping[str, Sequence[str]],
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> FixedSourceHypothesisSensitivity:
    """Evaluate distinct fixed source hypotheses without choosing a 'winner'.

    Each hypothesis keeps its own fixed source IDs across all tested targets.
    Every scenario uses the SAME candidate rules, full positive evidence,
    numerical threshold and first-passage horizon. The returned intersection
    and union are over the DECLARED candidates only; they say nothing about
    unlisted historical sources or real ecological processes.
    """
    if not isinstance(operators,Mapping) or not operators:
        raise ValueError("operators must declare at least one frozen rule")
    if not isinstance(source_hypotheses,Mapping) or not source_hypotheses:
        raise ValueError("source_hypotheses must contain at least one scenario")
    if any(not isinstance(k,str) or not k.strip() for k in operators):
        raise ValueError("candidate rule names must be nonblank strings")
    if any(not isinstance(k,str) or not k.strip() for k in source_hypotheses):
        raise ValueError("source hypothesis IDs must be nonblank strings")
    rule_items=tuple(sorted(operators.items()))
    node_ids=rule_items[0][1].node_ids
    if any(op.node_ids!=node_ids for _,op in rule_items):
        raise ValueError("every frozen rule must have the same node IDs and order")
    if any(not isinstance(k,str) or not k.strip() for k,_ in rule_items):
        raise ValueError("candidate rule names must be nonblank strings")

    if isinstance(positive_occurrence_ids,(str,bytes)):
        raise ValueError("positive_occurrence_ids requires a sequence, not a string")
    positive_raw=tuple(positive_occurrence_ids)
    if (len(positive_raw)<2
        or any(not isinstance(x,str) or not x.strip() for x in positive_raw)
        or len(set(positive_raw))!=len(positive_raw)
        or set(positive_raw)-set(node_ids)):
        raise ValueError(
            "positive_occurrence_ids must be >=2 unique known nonblank node IDs"
        )
    positive_set=set(positive_raw)
    positive=tuple(x for x in node_ids if x in positive_set)

    declared=[]
    seen_source_sets=set()
    for hypothesis_id,raw_sources in sorted(source_hypotheses.items()):
        if isinstance(raw_sources,(str,bytes)) or raw_sources is None:
            raise ValueError("source hypotheses need a sequence of node IDs, not a string")
        nodes=tuple(raw_sources)
        if (not nodes
            or any(not isinstance(x,str) or not x.strip() for x in nodes)
            or len(set(nodes))!=len(nodes)
            or not set(nodes)<=positive_set):
            raise ValueError(
                "each fixed source hypothesis needs distinct source IDs in positive occurrences"
            )
        canonical=tuple(x for x in node_ids if x in set(nodes))
        if canonical in seen_source_sets:
            raise ValueError("distinct source hypothesis IDs must use distinct fixed source sets")
        seen_source_sets.add(canonical)
        if len(canonical)>=len(positive):
            raise ValueError(
                "each source hypothesis must leave a non-source occurrence target"
            )
        declared.append((hypothesis_id,canonical))

    outcomes=[]
    per_rule={}
    fingerprints=None
    operator_permissiveness={}
    for hypothesis_id,source_ids in declared:
        result=compare_occurrence_transition_rules(
            operators,positive,
            max_steps=max_steps,
            fixed_source_ids=source_ids,
            support_floor=support_floor,
            support_tolerance=support_tolerance,
        )
        current=tuple(
            (r.rule_id,r.operator_fingerprint) for r in result.rule_results
        )
        if fingerprints is None:
            fingerprints=current
            operator_permissiveness={
                row.rule_id:(
                    row.operator_mean_outgoing_mass,
                    row.operator_active_edge_fraction,
                )
                for row in result.rule_results
            }
        elif current!=fingerprints:
            raise RuntimeError("candidate rule identity changed across source hypotheses")
        elif any(
            (row.operator_mean_outgoing_mass,row.operator_active_edge_fraction)
            !=operator_permissiveness[row.rule_id]
            for row in result.rule_results
        ):
            raise RuntimeError("operator permissiveness changed across source hypotheses")
        if any(
            row.source_policy!="fixed" or row.fixed_source_ids!=source_ids
            for row in result.rule_results
        ):
            raise RuntimeError("native EOG changed declared fixed source identities")
        compatible=tuple(
            row.rule_id for row in result.rule_results
            if not row.unsupported_occurrence_ids
        )
        incompatible=tuple(
            row.rule_id for row in result.rule_results
            if row.unsupported_occurrence_ids
        )
        outcomes.append(FixedSourceHypothesisResult(
            hypothesis_id=hypothesis_id,
            source_ids=source_ids,
            compatible_rule_ids=compatible,
            incompatible_rule_ids=incompatible,
            comparison_fingerprint=result.fingerprint,
        ))
        for name in compatible:
            per_rule.setdefault(name,set()).add(hypothesis_id)

    if fingerprints is None:
        raise ValueError("source hypotheses generated no native EOG outcomes")
    hypothesis_ids=tuple(x.hypothesis_id for x in outcomes)
    hypothesis_universe=set(hypothesis_ids)
    rule_status=[]
    robust=[]
    possible=[]
    contingent=[]
    excluded=[]
    for rule_id,_ in fingerprints:
        supported=per_rule.get(rule_id,set())
        supported_ids=tuple(h for h in hypothesis_ids if h in supported)
        rejected_ids=tuple(h for h in hypothesis_ids if h not in supported)
        if supported==hypothesis_universe:
            status="source_robust"
            robust.append(rule_id)
            possible.append(rule_id)
        elif supported:
            status="source_dependent"
            contingent.append(rule_id)
            possible.append(rule_id)
        else:
            status="unsupported_under_all_declared_sources"
            excluded.append(rule_id)
        rule_status.append(FixedSourceRuleStatus(
            rule_id=rule_id,
            compatible_hypothesis_ids=supported_ids,
            incompatible_hypothesis_ids=rejected_ids,
            status=status,
            operator_mean_outgoing_mass=operator_permissiveness[rule_id][0],
            operator_active_edge_fraction=operator_permissiveness[rule_id][1],
        ))
    if len(robust)+len(contingent)+len(excluded)!=len(fingerprints):
        raise RuntimeError("candidate rule/source-hypothesis partition incomplete")

    scope="static_alternative_declared_fixed_sources_not_sequential"
    cert="exhaustive_over_declared_fixed_source_hypotheses_and_frozen_rules"
    payload={
        "positive_occurrence_ids":positive,
        "rule_operator_fingerprints":fingerprints,
        "source_hypotheses":[
            {
                "hypothesis_id":x.hypothesis_id,
                "source_ids":x.source_ids,
                "compatible_rule_ids":x.compatible_rule_ids,
                "incompatible_rule_ids":x.incompatible_rule_ids,
                "comparison_fingerprint":x.comparison_fingerprint
            }for x in outcomes
        ],
        "rule_status":[
            {
                "rule_id":x.rule_id,
                "compatible_hypothesis_ids":x.compatible_hypothesis_ids,
                "incompatible_hypothesis_ids":x.incompatible_hypothesis_ids,
                "status":x.status,
                "operator_mean_outgoing_mass":x.operator_mean_outgoing_mass,
                "operator_active_edge_fraction":x.operator_active_edge_fraction,
            }for x in rule_status
        ],
        "robust":robust,
        "possible":possible,
        "contingent":contingent,
        "excluded":excluded,
        "max_steps":max_steps,
        "support_floor":support_floor,
        "support_tolerance":support_tolerance,
        "source_origins_verified":False,
        "scope":scope,
        "certificate":cert,
    }
    return FixedSourceHypothesisSensitivity(
        positive_occurrence_ids=positive,
        rule_operator_fingerprints=fingerprints,
        source_hypotheses=tuple(outcomes),
        rule_status=tuple(rule_status),
        source_robust_rule_ids=tuple(robust),
        source_possible_rule_ids=tuple(possible),
        source_dependent_rule_ids=tuple(contingent),
        source_impossible_under_declared_hypotheses_rule_ids=tuple(excluded),
        max_steps=max_steps,
        support_floor=support_floor,
        support_tolerance=support_tolerance,
        source_hypotheses_are_NOT_independently_verified_historical_origins=True,
        source_state_scope=scope,
        coverage_certificate=cert,
        fingerprint=_digest(payload)
    )
