"""Robust and adaptive evidence planning for EOG v3 joint-world evaluations.

This module exposes the frozen v2.8/v2.9 finite set-valued planners through the
v3 joint-world surface.  Candidate action mappings may be declared on a larger
parent joint universe; only currently surviving joint worlds are passed to the
exact planners.
"""
from __future__ import annotations

from typing import Hashable, Mapping, Sequence

from eog.v2.adaptive_evidence_tree import (
    AdaptivePolicyValue,
    forced_first_action_depth,
    solve_adaptive_policy,
)
from eog.v2.robust_evidence_design import (
    RobustEvidencePlan,
    plan_robust_set_valued_evidence,
)

from .joint_world_engine import JointWorldEvaluation


ActionSupports = Mapping[
    str,
    Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
]


def _active_joint_ids(evaluation: JointWorldEvaluation) -> tuple[str, ...]:
    return tuple(sorted(evaluation.surviving_joint_world_ids))


def _subset_action_supports(
    evaluation: JointWorldEvaluation,
    action_supports: ActionSupports,
) -> dict[str, dict[str, frozenset[Hashable]]]:
    active = _active_joint_ids(evaluation)
    if not active:
        raise ValueError("cannot plan evidence after the joint universe is falsified")
    active_set = set(active)
    if not action_supports:
        raise ValueError("action_supports must be non-empty")

    normalized: dict[str, dict[str, frozenset[Hashable]]] = {}
    for action_id in sorted(str(value) for value in action_supports):
        mapping = action_supports[action_id]
        missing = active_set.difference(mapping)
        if missing:
            raise ValueError(
                f"action {action_id!r} is missing outcomes for active joint worlds: "
                f"{sorted(missing)}"
            )
        normalized[action_id] = {}
        for joint_id in active:
            outcomes = frozenset(mapping[joint_id])
            if not outcomes:
                raise ValueError(
                    f"action {action_id!r} has empty outcome support for {joint_id!r}"
                )
            normalized[action_id][joint_id] = outcomes
    return normalized


def plan_robust_evidence_set(
    evaluation: JointWorldEvaluation,
    action_supports: ActionSupports,
) -> RobustEvidencePlan:
    """Return the exact minimum nonadaptive robust evidence set, or unresolved."""

    active = _active_joint_ids(evaluation)
    normalized = _subset_action_supports(evaluation, action_supports)
    return plan_robust_set_valued_evidence(active, normalized)


def solve_adaptive_evidence_policy(
    evaluation: JointWorldEvaluation,
    action_supports: ActionSupports,
    *,
    available_action_ids: Sequence[str] | None = None,
) -> AdaptivePolicyValue:
    """Minimize worst-case additional actions needed to isolate one joint world."""

    active = _active_joint_ids(evaluation)
    normalized = _subset_action_supports(evaluation, action_supports)
    return solve_adaptive_policy(
        active,
        normalized,
        available_action_ids=available_action_ids,
    )


def adaptive_forced_first_depth(
    evaluation: JointWorldEvaluation,
    action_supports: ActionSupports,
    first_action_id: str,
) -> int | None:
    """Return worst-case depth when one action is forced to be first."""

    active = _active_joint_ids(evaluation)
    normalized = _subset_action_supports(evaluation, action_supports)
    return forced_first_action_depth(
        active,
        normalized,
        first_action_id,
    )


__all__ = [
    "ActionSupports",
    "adaptive_forced_first_depth",
    "plan_robust_evidence_set",
    "solve_adaptive_evidence_policy",
]
