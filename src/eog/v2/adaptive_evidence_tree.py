"""Exact adaptive evidence tree over finite set-valued action outcomes.

The solver minimizes worst-case actions to isolate one active hypothesis. Actions are
used at most once. After observing an outcome, hypotheses survive exactly when that
outcome belongs to their declared possible-outcome set.

If no remaining action can guarantee eventual singleton resolution, the state is
returned as unresolved rather than forcing a decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from typing import Hashable, Mapping, Sequence

from .robust_evidence_design import build_v28_fixture


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AdaptivePolicyValue:
    hypothesis_ids: tuple[str, ...]
    remaining_action_ids: tuple[str, ...]
    resolvable: bool
    worst_case_depth: int | None
    optimal_first_actions: tuple[str, ...]
    canonical_first_action: str | None
    fingerprint: str


def _normalize_fixture(
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    dict[str, dict[str, frozenset[Hashable]]],
]:
    hypotheses = tuple(sorted(str(value) for value in hypothesis_ids))
    if not hypotheses or len(set(hypotheses)) != len(hypotheses):
        raise ValueError("hypothesis_ids must contain unique values")
    actions = tuple(sorted(str(value) for value in possible_outcomes_by_action))
    if not actions:
        raise ValueError("at least one action is required")

    normalized: dict[str, dict[str, frozenset[Hashable]]] = {}
    hypothesis_set = set(hypotheses)
    for action_id in actions:
        rows = possible_outcomes_by_action[action_id]
        missing = hypothesis_set.difference(rows)
        if missing:
            raise ValueError(
                f"action {action_id!r} is missing outcomes for active hypotheses: "
                f"{sorted(missing)}"
            )
        normalized[action_id] = {}
        for hypothesis_id in hypotheses:
            outcomes = frozenset(rows[hypothesis_id])
            if not outcomes:
                raise ValueError("possible outcome sets must be non-empty")
            normalized[action_id][hypothesis_id] = outcomes
    return hypotheses, actions, normalized


def _possible_action_outcomes(
    active_hypotheses: Sequence[str],
    action_rows: Mapping[str, frozenset[Hashable]],
) -> tuple[Hashable, ...]:
    values: set[Hashable] = set()
    for hypothesis_id in active_hypotheses:
        values.update(action_rows[hypothesis_id])
    return tuple(sorted(values, key=str))


def _survivors_for_outcome(
    active_hypotheses: Sequence[str],
    action_rows: Mapping[str, frozenset[Hashable]],
    outcome: Hashable,
) -> tuple[str, ...]:
    return tuple(
        hypothesis_id
        for hypothesis_id in active_hypotheses
        if outcome in action_rows[hypothesis_id]
    )


def solve_adaptive_policy(
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
    *,
    available_action_ids: Sequence[str] | None = None,
) -> AdaptivePolicyValue:
    hypotheses, all_actions, normalized = _normalize_fixture(
        hypothesis_ids,
        possible_outcomes_by_action,
    )
    if available_action_ids is None:
        initial_actions = all_actions
    else:
        requested = tuple(sorted(str(value) for value in available_action_ids))
        missing = set(requested).difference(all_actions)
        if missing:
            raise ValueError(f"unknown action IDs: {sorted(missing)}")
        initial_actions = requested

    @lru_cache(maxsize=None)
    def recurse(
        active: tuple[str, ...],
        remaining: tuple[str, ...],
    ) -> tuple[bool, int | None, tuple[str, ...]]:
        if len(active) <= 1:
            return True, 0, ()
        if not remaining:
            return False, None, ()

        action_depths: dict[str, int] = {}
        for action_id in remaining:
            next_remaining = tuple(
                value for value in remaining if value != action_id
            )
            child_depths: list[int] = []
            action_resolvable = True
            for outcome in _possible_action_outcomes(
                active,
                normalized[action_id],
            ):
                child = _survivors_for_outcome(
                    active,
                    normalized[action_id],
                    outcome,
                )
                if not child:
                    continue
                child_resolvable, child_depth, _ = recurse(
                    child,
                    next_remaining,
                )
                if not child_resolvable or child_depth is None:
                    action_resolvable = False
                    break
                child_depths.append(child_depth)
            if action_resolvable and child_depths:
                action_depths[action_id] = 1 + max(child_depths)

        if not action_depths:
            return False, None, ()
        best_depth = min(action_depths.values())
        optimal = tuple(
            sorted(
                action_id
                for action_id, depth in action_depths.items()
                if depth == best_depth
            )
        )
        return True, best_depth, optimal

    resolvable, depth, optimal = recurse(hypotheses, initial_actions)
    canonical = optimal[0] if optimal else None
    payload = {
        "hypothesis_ids": list(hypotheses),
        "remaining_action_ids": list(initial_actions),
        "resolvable": resolvable,
        "worst_case_depth": depth,
        "optimal_first_actions": list(optimal),
        "canonical_first_action": canonical,
    }
    return AdaptivePolicyValue(
        hypothesis_ids=hypotheses,
        remaining_action_ids=initial_actions,
        resolvable=resolvable,
        worst_case_depth=depth,
        optimal_first_actions=optimal,
        canonical_first_action=canonical,
        fingerprint=_sha256(payload),
    )


def forced_first_action_depth(
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
    first_action_id: str,
) -> int | None:
    hypotheses, actions, normalized = _normalize_fixture(
        hypothesis_ids,
        possible_outcomes_by_action,
    )
    if first_action_id not in actions:
        raise ValueError("first_action_id is not in the action library")
    remaining = tuple(action for action in actions if action != first_action_id)

    child_depths: list[int] = []
    for outcome in _possible_action_outcomes(
        hypotheses,
        normalized[first_action_id],
    ):
        child = _survivors_for_outcome(
            hypotheses,
            normalized[first_action_id],
            outcome,
        )
        if not child:
            continue
        if len(child) == 1:
            child_depths.append(0)
            continue
        value = solve_adaptive_policy(
            child,
            possible_outcomes_by_action,
            available_action_ids=remaining,
        )
        if not value.resolvable or value.worst_case_depth is None:
            return None
        child_depths.append(value.worst_case_depth)
    if not child_depths:
        return None
    return 1 + max(child_depths)


def _bruteforce_depth(
    active: tuple[str, ...],
    remaining: tuple[str, ...],
    normalized: Mapping[str, Mapping[str, frozenset[Hashable]]],
) -> int | None:
    """Independent uncached exhaustive recursion used only for validation."""

    if len(active) <= 1:
        return 0
    if not remaining:
        return None
    values: list[int] = []
    for action_id in remaining:
        next_remaining = tuple(
            value for value in remaining if value != action_id
        )
        child_depths: list[int] = []
        valid = True
        for outcome in _possible_action_outcomes(active, normalized[action_id]):
            child = _survivors_for_outcome(
                active,
                normalized[action_id],
                outcome,
            )
            if not child:
                continue
            child_depth = _bruteforce_depth(
                child,
                next_remaining,
                normalized,
            )
            if child_depth is None:
                valid = False
                break
            child_depths.append(child_depth)
        if valid and child_depths:
            values.append(1 + max(child_depths))
    return None if not values else min(values)


def realized_canonical_path(
    truth_hypothesis_id: str,
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
    realized_outcome_by_action: Mapping[str, Hashable],
) -> tuple[dict[str, object], ...]:
    hypotheses, actions, normalized = _normalize_fixture(
        hypothesis_ids,
        possible_outcomes_by_action,
    )
    if truth_hypothesis_id not in hypotheses:
        raise ValueError("truth_hypothesis_id must be active initially")

    active = hypotheses
    remaining = actions
    path: list[dict[str, object]] = []
    while len(active) > 1:
        value = solve_adaptive_policy(
            active,
            possible_outcomes_by_action,
            available_action_ids=remaining,
        )
        if not value.resolvable or value.canonical_first_action is None:
            raise RuntimeError("canonical policy became unresolved on the realized path")
        action_id = value.canonical_first_action
        if action_id not in realized_outcome_by_action:
            raise ValueError(f"missing realized outcome for action {action_id!r}")
        outcome = realized_outcome_by_action[action_id]
        if outcome not in normalized[action_id][truth_hypothesis_id]:
            raise ValueError("realized outcome is impossible under the declared truth")
        before = active
        active = _survivors_for_outcome(
            active,
            normalized[action_id],
            outcome,
        )
        remaining = tuple(
            value for value in remaining if value != action_id
        )
        path.append(
            {
                "action_id": action_id,
                "outcome": outcome,
                "before_hypotheses": list(before),
                "after_hypotheses": list(active),
            }
        )
    return tuple(path)


def run_adaptive_evidence_v29() -> dict[str, object]:
    hypotheses, _, _, actions = build_v28_fixture()
    value = solve_adaptive_policy(hypotheses, actions)

    _, action_ids, normalized = _normalize_fixture(hypotheses, actions)
    brute_depth = _bruteforce_depth(
        tuple(sorted(hypotheses)),
        action_ids,
        normalized,
    )
    a1_supported = value.worst_case_depth == brute_depth

    forced = {
        action_id: forced_first_action_depth(
            hypotheses,
            actions,
            action_id,
        )
        for action_id in sorted(actions)
    }
    expected_optimal = (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )
    a2_supported = (
        value.resolvable
        and value.worst_case_depth == 2
        and value.optimal_first_actions == expected_optimal
        and value.canonical_first_action == "direct_detection_calibration"
    )
    a3_supported = (
        forced["repeat_one_survey"] == 3
        and forced["repeat_four_surveys"] == 3
    )

    realized = realized_canonical_path(
        "absent::p1",
        hypotheses,
        actions,
        {
            "direct_detection_calibration": 1.0,
            "direct_target_state_assay": "absent",
            "repeat_one_survey": 0,
            "repeat_four_surveys": 0,
        },
    )
    a4_supported = (
        len(realized) == 1
        and realized[0]["action_id"] == "direct_detection_calibration"
        and realized[0]["after_hypotheses"] == ["absent::p1"]
    )

    without_calibration = solve_adaptive_policy(
        hypotheses,
        actions,
        available_action_ids=(
            "direct_target_state_assay",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    without_state = solve_adaptive_policy(
        hypotheses,
        actions,
        available_action_ids=(
            "direct_detection_calibration",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    a5_supported = (
        not without_calibration.resolvable
        and not without_state.resolvable
    )

    verdicts = {
        "A1_exact_adaptive_recursion": (
            "SUPPORTED" if a1_supported else "REFUTED"
        ),
        "A2_optimal_worst_case_depth": (
            "SUPPORTED" if a2_supported else "REFUTED"
        ),
        "A3_repeat_first_is_worse": (
            "SUPPORTED" if a3_supported else "REFUTED"
        ),
        "A4_known_truth_realized_depth": (
            "SUPPORTED" if a4_supported else "REFUTED"
        ),
        "A5_direct_channels_are_jointly_necessary_for_worst_case_resolution": (
            "SUPPORTED" if a5_supported else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.adaptive_set_valued_evidence_tree.result.v2_9",
        "active_hypotheses": list(hypotheses),
        "minimum_worst_case_depth": value.worst_case_depth,
        "optimal_first_actions": list(value.optimal_first_actions),
        "canonical_first_action": value.canonical_first_action,
        "first_action_worst_case_depths": forced,
        "bruteforce_worst_case_depth": brute_depth,
        "known_truth": "absent::p1",
        "known_truth_realized_path": list(realized),
        "known_truth_realized_depth": len(realized),
        "ablation_without_calibration": {
            "resolvable": without_calibration.resolvable,
            "worst_case_depth": without_calibration.worst_case_depth,
        },
        "ablation_without_state_assay": {
            "resolvable": without_state.resolvable,
            "worst_case_depth": without_state.worst_case_depth,
        },
        "verdicts": verdicts,
        "policy_fingerprint": value.fingerprint,
    }
    result["fingerprint"] = _sha256(result)
    return result
