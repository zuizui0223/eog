"""Robust finite evidence design with set-valued stochastic outcomes.

Each action maps every active hypothesis to the finite set of outcomes that have
positive probability under that hypothesis.  An action robustly separates two
hypotheses only when those possible-outcome sets are disjoint.

This is a guarantee-style planner.  It deliberately does not treat low probability
or expected information gain as hard separation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import hashlib
import json
import math
from typing import Hashable, Mapping, Sequence


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_outcome_set(values: Sequence[Hashable] | set[Hashable] | frozenset[Hashable]) -> frozenset[Hashable]:
    result = frozenset(values)
    if not result:
        raise ValueError("possible outcome sets must be non-empty")
    return result


def robustly_separates(
    left_outcomes: Sequence[Hashable] | set[Hashable] | frozenset[Hashable],
    right_outcomes: Sequence[Hashable] | set[Hashable] | frozenset[Hashable],
) -> bool:
    return _normalize_outcome_set(left_outcomes).isdisjoint(
        _normalize_outcome_set(right_outcomes)
    )


def unresolved_pairs(hypothesis_ids: Sequence[str]) -> tuple[tuple[str, str], ...]:
    ids = tuple(sorted(str(value) for value in hypothesis_ids))
    if not ids or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("hypothesis_ids must contain unique non-empty IDs")
    return tuple(
        (ids[i], ids[j])
        for i in range(len(ids))
        for j in range(i + 1, len(ids))
    )


def robust_split_pairs(
    pairs: Sequence[tuple[str, str]],
    possible_outcomes_by_hypothesis: Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        pair
        for pair in pairs
        if robustly_separates(
            possible_outcomes_by_hypothesis[pair[0]],
            possible_outcomes_by_hypothesis[pair[1]],
        )
    )


def action_set_covers_pairs(
    pairs: Sequence[tuple[str, str]],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
    selected_action_ids: Sequence[str],
) -> bool:
    selected = tuple(selected_action_ids)
    for left, right in pairs:
        if not any(
            robustly_separates(
                possible_outcomes_by_action[action_id][left],
                possible_outcomes_by_action[action_id][right],
            )
            for action_id in selected
        ):
            return False
    return True


def exact_minimum_robust_separating_set(
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
) -> tuple[str, ...] | None:
    ids = tuple(sorted(str(value) for value in hypothesis_ids))
    pairs = unresolved_pairs(ids)
    action_ids = tuple(sorted(possible_outcomes_by_action))
    if not action_ids:
        return None if pairs else ()

    for action_id in action_ids:
        worlds = set(possible_outcomes_by_action[action_id])
        if worlds != set(ids):
            raise ValueError(
                f"action {action_id!r} must define outcomes for exactly every hypothesis"
            )
        for values in possible_outcomes_by_action[action_id].values():
            _normalize_outcome_set(values)

    for size in range(1, len(action_ids) + 1):
        valid: list[tuple[str, ...]] = []
        for subset in combinations(action_ids, size):
            if action_set_covers_pairs(pairs, possible_outcomes_by_action, subset):
                valid.append(tuple(subset))
        if valid:
            return min(valid)
    return None


@dataclass(frozen=True)
class RobustActionRanking:
    action_id: str
    robust_split_pair_count: int
    robust_unresolved_pair_count: int


@dataclass(frozen=True)
class RobustEvidencePlan:
    hypothesis_ids: tuple[str, ...]
    unresolved_pairs: tuple[tuple[str, str], ...]
    rankings: tuple[RobustActionRanking, ...]
    minimum_robust_separating_set: tuple[str, ...] | None
    minimum_robust_set_size: int | None
    all_pairs_robustly_separated: bool
    insufficient_action_library: bool
    fingerprint: str


def plan_robust_set_valued_evidence(
    hypothesis_ids: Sequence[str],
    possible_outcomes_by_action: Mapping[
        str,
        Mapping[str, Sequence[Hashable] | set[Hashable] | frozenset[Hashable]],
    ],
) -> RobustEvidencePlan:
    ids = tuple(sorted(str(value) for value in hypothesis_ids))
    pairs = unresolved_pairs(ids)

    rankings: list[RobustActionRanking] = []
    for action_id in sorted(possible_outcomes_by_action):
        split = robust_split_pairs(
            pairs,
            possible_outcomes_by_action[action_id],
        )
        rankings.append(
            RobustActionRanking(
                action_id=action_id,
                robust_split_pair_count=len(split),
                robust_unresolved_pair_count=len(pairs) - len(split),
            )
        )
    rankings.sort(
        key=lambda row: (-row.robust_split_pair_count, row.action_id)
    )

    minimum = exact_minimum_robust_separating_set(
        ids,
        possible_outcomes_by_action,
    )
    all_separated = (
        minimum is not None
        and action_set_covers_pairs(
            pairs,
            possible_outcomes_by_action,
            minimum,
        )
    )
    insufficient = bool(pairs) and minimum is None
    payload = {
        "hypothesis_ids": list(ids),
        "unresolved_pairs": [list(pair) for pair in pairs],
        "rankings": [
            {
                "action_id": row.action_id,
                "robust_split_pair_count": row.robust_split_pair_count,
                "robust_unresolved_pair_count": row.robust_unresolved_pair_count,
            }
            for row in rankings
        ],
        "minimum_robust_separating_set": None if minimum is None else list(minimum),
        "all_pairs_robustly_separated": all_separated,
        "insufficient_action_library": insufficient,
    }
    return RobustEvidencePlan(
        hypothesis_ids=ids,
        unresolved_pairs=pairs,
        rankings=tuple(rankings),
        minimum_robust_separating_set=minimum,
        minimum_robust_set_size=None if minimum is None else len(minimum),
        all_pairs_robustly_separated=all_separated,
        insufficient_action_library=insufficient,
        fingerprint=_sha256(payload),
    )


def binomial_positive_support(
    *,
    surveys: int,
    probability: float,
) -> frozenset[int]:
    if surveys < 1:
        raise ValueError("surveys must be positive")
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0,1]")
    possible = []
    for detections in range(surveys + 1):
        mass = (
            math.comb(surveys, detections)
            * probability**detections
            * (1.0 - probability) ** (surveys - detections)
        )
        if mass > 0.0:
            possible.append(detections)
    return frozenset(possible)


def build_v28_fixture():
    hypotheses = (
        "absent::p1",
        "absent::p075",
        "present::p075",
    )
    state_by = {
        "absent::p1": "absent",
        "absent::p075": "absent",
        "present::p075": "present",
    }
    p_by = {
        "absent::p1": 1.0,
        "absent::p075": 0.75,
        "present::p075": 0.75,
    }

    def focal_support(hypothesis_id: str, surveys: int) -> frozenset[int]:
        probability = p_by[hypothesis_id] if state_by[hypothesis_id] == "present" else 0.0
        return binomial_positive_support(
            surveys=surveys,
            probability=probability,
        )

    actions = {
        "repeat_one_survey": {
            hypothesis_id: focal_support(hypothesis_id, 1)
            for hypothesis_id in hypotheses
        },
        "repeat_four_surveys": {
            hypothesis_id: focal_support(hypothesis_id, 4)
            for hypothesis_id in hypotheses
        },
        "direct_detection_calibration": {
            hypothesis_id: frozenset({p_by[hypothesis_id]})
            for hypothesis_id in hypotheses
        },
        "direct_target_state_assay": {
            hypothesis_id: frozenset({state_by[hypothesis_id]})
            for hypothesis_id in hypotheses
        },
    }
    return hypotheses, state_by, p_by, actions


def run_robust_set_valued_v28() -> dict[str, object]:
    hypotheses, state_by, p_by, actions = build_v28_fixture()
    plan = plan_robust_set_valued_evidence(hypotheses, actions)
    pairs = plan.unresolved_pairs

    split_counts = {
        row.action_id: row.robust_split_pair_count
        for row in plan.rankings
    }

    # R1: exhaustive subset pair-cover audit.
    r1_mismatches = 0
    action_ids = tuple(sorted(actions))
    for size in range(len(action_ids) + 1):
        for subset in combinations(action_ids, size):
            covered = action_set_covers_pairs(pairs, actions, subset)
            directly_all_separated = all(
                any(
                    robustly_separates(
                        actions[action_id][left],
                        actions[action_id][right],
                    )
                    for action_id in subset
                )
                for left, right in pairs
            )
            if covered != directly_all_separated:
                r1_mismatches += 1

    r2_supported = (
        split_counts["repeat_one_survey"] == 0
        and split_counts["repeat_four_surveys"] == 0
    )
    r3_supported = (
        split_counts["direct_detection_calibration"] == 2
        and split_counts["direct_target_state_assay"] == 2
    )
    expected_minimum = (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )
    r4_supported = (
        plan.minimum_robust_separating_set == expected_minimum
        and plan.minimum_robust_set_size == 2
        and plan.all_pairs_robustly_separated
    )

    # Frozen known truth = absent::p1.  The observed calibration outcome is p=1.
    truth_id = "absent::p1"
    calibration_outcome = p_by[truth_id]
    after_calibration = tuple(
        hypothesis_id
        for hypothesis_id in hypotheses
        if calibration_outcome
        in actions["direct_detection_calibration"][hypothesis_id]
    )
    r5_supported = (
        after_calibration == (truth_id,)
        and plan.minimum_robust_set_size == 2
    )

    verdicts = {
        "R1_disjoint_support_criterion": (
            "SUPPORTED" if r1_mismatches == 0 else "REFUTED"
        ),
        "R2_more_surveys_have_no_guaranteed_split": (
            "SUPPORTED" if r2_supported else "REFUTED"
        ),
        "R3_direct_channels_each_split_two_pairs": (
            "SUPPORTED" if r3_supported else "REFUTED"
        ),
        "R4_minimum_robust_design": (
            "SUPPORTED" if r4_supported else "REFUTED"
        ),
        "R5_truth_conditional_adaptive_shortcut": (
            "SUPPORTED" if r5_supported else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.robust_set_valued_evidence_design.result.v2_8",
        "active_joint_hypotheses": list(hypotheses),
        "known_truth_hypothesis": truth_id,
        "unresolved_pair_count": len(pairs),
        "possible_outcomes_by_action_and_hypothesis": {
            action_id: {
                hypothesis_id: sorted(values, key=str)
                for hypothesis_id, values in rows.items()
            }
            for action_id, rows in actions.items()
        },
        "robust_split_pair_count_by_action": split_counts,
        "minimum_robust_separating_set": (
            None
            if plan.minimum_robust_separating_set is None
            else list(plan.minimum_robust_separating_set)
        ),
        "minimum_robust_set_size": plan.minimum_robust_set_size,
        "known_truth_calibration_outcome": calibration_outcome,
        "known_truth_after_calibration": list(after_calibration),
        "R1_mismatches": r1_mismatches,
        "verdicts": verdicts,
        "plan_fingerprint": plan.fingerprint,
    }
    result["fingerprint"] = _sha256(result)
    return result
