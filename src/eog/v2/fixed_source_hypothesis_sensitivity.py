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


@dataclass(frozen=True)
class FixedSourceHypothesisIdentifiability:
    """Source-hypothesis projection of compatible frozen rule×source pairs.

    Uniqueness conditional on one graph does NOT imply globally identifiable
    historical origin when the frozen graph/rule itself remains uncertain.
    This is a finite declared-rule/source hypothesis combinatorial audit only.
    """

    candidate_rule_count: int
    declared_source_hypothesis_ids: tuple[str, ...]
    source_support_cardinality_counts: tuple[tuple[int, int], ...]
    uniquely_source_supported_rule_ids: tuple[str, ...]
    source_hypotheses_unique_given_rule_counts: tuple[tuple[str, int], ...]
    compatible_rule_source_assignments: tuple[tuple[str, str], ...]
    compatible_rule_source_assignment_count: int
    possible_source_hypotheses_after_marginalizing_rule: tuple[str, ...]
    source_hypothesis_identifiability_status: str
    historical_origin_identified: bool
    graph_truth_or_source_prior_estimated: bool
    source_state_scope: str
    parent_audit_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def summarize_fixed_source_hypothesis_identifiability(
    audit: FixedSourceHypothesisSensitivity,
) -> FixedSourceHypothesisIdentifiability:
    """Separate graph-CONDITIONAL source uniqueness from rule-MARGINAL uniqueness.

    Pure post-processing of an existing complete, named EOG compatibility
    ledger. No extra source candidates, model fits, ecological assumptions,
    posterior weights or data sources are introduced.

    The test asks whether source hypotheses remain distinguishable AFTER
    projecting all compatible (candidate rule, source hypothesis) pairs to
    source labels, rather than assuming one rule is true without evidence.
    """
    if not isinstance(audit, FixedSourceHypothesisSensitivity):
        raise TypeError("audit must be FixedSourceHypothesisSensitivity")
    hypothesis_ids = tuple(h.hypothesis_id for h in audit.source_hypotheses)
    rule_ids = tuple(r.rule_id for r in audit.rule_status)
    if not hypothesis_ids or len(set(hypothesis_ids)) != len(hypothesis_ids):
        raise ValueError("audited source hypothesis IDs must be unique and nonempty")
    if not rule_ids or len(set(rule_ids)) != len(rule_ids):
        raise ValueError("audited rule IDs must be unique and nonempty")
    if tuple(rule_id for rule_id, _ in audit.rule_operator_fingerprints) != rule_ids:
        raise ValueError("audited candidate rule/fingerprint identities are inconsistent")

    hyp_compatible: dict[str, set[str]] = {}
    for hypothesis in audit.source_hypotheses:
        positive = set(hypothesis.compatible_rule_ids)
        negative = set(hypothesis.incompatible_rule_ids)
        if (positive & negative or positive | negative != set(rule_ids)
                or len(positive) != len(hypothesis.compatible_rule_ids)
                or len(negative) != len(hypothesis.incompatible_rule_ids)):
            raise ValueError("audited source hypothesis rule compatibility partition inconsistent")
        hyp_compatible[hypothesis.hypothesis_id] = positive

    cardinality_counts = [0] * (len(hypothesis_ids) + 1)
    unique_by_hypothesis = {h: 0 for h in hypothesis_ids}
    unique_rule_ids = []
    compatible_pairs = []
    robust, partial, excluded, possible = [], [], [], []
    for row in audit.rule_status:
        supported = tuple(
            h for h in hypothesis_ids if row.rule_id in hyp_compatible[h]
        )
        unsupported = tuple(h for h in hypothesis_ids if h not in supported)
        if (row.compatible_hypothesis_ids != supported
                or row.incompatible_hypothesis_ids != unsupported):
            raise ValueError("audited rule source-hypothesis support identities inconsistent")
        n = len(supported)
        cardinality_counts[n] += 1
        for hypothesis_id in supported:
            compatible_pairs.append((row.rule_id, hypothesis_id))
        if n == 1:
            unique_rule_ids.append(row.rule_id)
            unique_by_hypothesis[supported[0]] += 1
        if n == len(hypothesis_ids):
            expected = "source_robust"
            robust.append(row.rule_id)
            possible.append(row.rule_id)
        elif n:
            expected = "source_dependent"
            partial.append(row.rule_id)
            possible.append(row.rule_id)
        else:
            expected = "unsupported_under_all_declared_sources"
            excluded.append(row.rule_id)
        if row.status != expected:
            raise ValueError("audited candidate rule source-status label inconsistent")

    if (
        tuple(robust) != audit.source_robust_rule_ids
        or tuple(partial) != audit.source_dependent_rule_ids
        or tuple(possible) != audit.source_possible_rule_ids
        or tuple(excluded)
        != audit.source_impossible_under_declared_hypotheses_rule_ids
    ):
        raise ValueError("audited aggregate rule-source hypothesis identities inconsistent")

    projected = tuple(
        h for h in hypothesis_ids
        if any(h == hypothesis for _, hypothesis in compatible_pairs)
    )
    if not projected:
        status = "declared_rule_source_universe_falsified"
    elif len(hypothesis_ids) == 1:
        status = "single_candidate_declared_not_an_identification_test"
    elif len(projected) == 1:
        status = "one_source_supported_within_declared_rule_and_source_universe"
    else:
        status = "multiple_sources_possible_after_rule_marginalization"

    certificate = "exhaustive_projection_of_declared_frozen_rule_source_hypothesis_pairs"
    payload = {
        "candidate_rule_count": len(rule_ids),
        "declared_source_hypothesis_ids": hypothesis_ids,
        "source_support_cardinality_counts": tuple(enumerate(cardinality_counts)),
        "uniquely_source_supported_rule_ids": unique_rule_ids,
        "source_hypotheses_unique_given_rule_counts": tuple(
            (h, unique_by_hypothesis[h]) for h in hypothesis_ids
        ),
        "compatible_rule_source_assignments": compatible_pairs,
        "compatible_rule_source_assignment_count": len(compatible_pairs),
        "possible_source_hypotheses_after_marginalizing_rule": projected,
        "source_hypothesis_identifiability_status": status,
        "historical_origin_identified": False,
        "graph_truth_or_source_prior_estimated": False,
        "source_state_scope": "static_declared_graph_conditional_vs_graph_marginal_source",
        "parent_audit_fingerprint": audit.fingerprint,
        "coverage_certificate": certificate,
    }
    return FixedSourceHypothesisIdentifiability(
        candidate_rule_count=len(rule_ids),
        declared_source_hypothesis_ids=hypothesis_ids,
        source_support_cardinality_counts=tuple(enumerate(cardinality_counts)),
        uniquely_source_supported_rule_ids=tuple(unique_rule_ids),
        source_hypotheses_unique_given_rule_counts=tuple(
            (h, unique_by_hypothesis[h]) for h in hypothesis_ids
        ),
        compatible_rule_source_assignments=tuple(compatible_pairs),
        compatible_rule_source_assignment_count=len(compatible_pairs),
        possible_source_hypotheses_after_marginalizing_rule=projected,
        source_hypothesis_identifiability_status=status,
        historical_origin_identified=False,
        graph_truth_or_source_prior_estimated=False,
        source_state_scope="static_declared_graph_conditional_vs_graph_marginal_source",
        parent_audit_fingerprint=audit.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_digest(payload),
    )
