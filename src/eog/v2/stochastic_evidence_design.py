"""Robust stochastic evidence design over surviving joint ecology-observation worlds.

Actions may have multiple possible outcomes in a given joint world.  The planner uses
support sets only:

- a pair is guaranteed to be separated when their outcome supports are disjoint;
- worst-case joint survivors are the largest support-compatible joint set over action
  outcomes;
- worst-case ecological survivors project those joint survivors onto ecological IDs.

No priors or expected-utility weights are assumed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import combinations
from typing import Hashable, Mapping

from .joint_ecology_observation import _select_target_node
from .known_truth_detection import ObservationWorld, observation_history_probability


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
class ActiveJointWorld:
    joint_id: str
    ecological_world_id: str
    observation_world_id: str
    target_present: bool
    detection_probability: float
    false_positive_probability: float


@dataclass(frozen=True)
class StochasticActionSummary:
    action_id: str
    guaranteed_joint_pair_splits: int
    worst_case_joint_survivors: int
    worst_case_ecological_survivors: int
    possible_outcomes: tuple[Hashable, ...]


def build_active_joint_worlds_v28() -> tuple[
    tuple[ActiveJointWorld, ...],
    str,
]:
    """Reconstruct the frozen broad v2.7 joint survivor state after 4 nondetections."""

    system, target_node, _, _ = _select_target_node()
    observation_worlds = (
        ObservationWorld("perfect", 1.0, 0.0),
        ObservationWorld("imperfect", 0.75, 0.0),
    )

    active: list[ActiveJointWorld] = []
    for ecological_world in system.worlds:
        target_present = target_node in ecological_world.occupied_ids
        state = "present" if target_present else "absent"
        for obs in observation_worlds:
            probability = observation_history_probability(
                state,
                detections=0,
                surveys=4,
                observation_world=obs,
            )
            if probability <= 0.0:
                continue
            active.append(
                ActiveJointWorld(
                    joint_id=f"{ecological_world.world_id}::{obs.world_id}",
                    ecological_world_id=ecological_world.world_id,
                    observation_world_id=obs.world_id,
                    target_present=target_present,
                    detection_probability=obs.detection_probability,
                    false_positive_probability=obs.false_positive_probability,
                )
            )
    return tuple(sorted(active, key=lambda row: row.joint_id)), target_node


def _repeat_four_support(world: ActiveJointWorld) -> frozenset[int]:
    obs = ObservationWorld(
        world.observation_world_id,
        world.detection_probability,
        world.false_positive_probability,
    )
    state = "present" if world.target_present else "absent"
    return frozenset(
        detections
        for detections in range(5)
        if observation_history_probability(
            state,
            detections=detections,
            surveys=4,
            observation_world=obs,
        )
        > 0.0
    )


def action_supports_v28(
    active_worlds: tuple[ActiveJointWorld, ...],
) -> dict[str, dict[str, frozenset[Hashable]]]:
    return {
        "repeat_4_same_protocol": {
            world.joint_id: _repeat_four_support(world)
            for world in active_worlds
        },
        "calibrate_detection_world": {
            world.joint_id: frozenset((world.observation_world_id,))
            for world in active_worlds
        },
        "gold_standard_target_state": {
            world.joint_id: frozenset(
                ("present" if world.target_present else "absent",)
            )
            for world in active_worlds
        },
    }


def supports_disjoint(
    left: frozenset[Hashable],
    right: frozenset[Hashable],
) -> bool:
    return left.isdisjoint(right)


def guaranteed_pair_split_count(
    active_worlds: tuple[ActiveJointWorld, ...],
    support_by_joint_world: Mapping[str, frozenset[Hashable]],
) -> int:
    return sum(
        1
        for left, right in combinations(active_worlds, 2)
        if supports_disjoint(
            support_by_joint_world[left.joint_id],
            support_by_joint_world[right.joint_id],
        )
    )


def worst_case_survivors(
    active_worlds: tuple[ActiveJointWorld, ...],
    support_by_joint_world: Mapping[str, frozenset[Hashable]],
) -> tuple[int, int, tuple[Hashable, ...]]:
    possible_outcomes = tuple(
        sorted(
            set().union(*support_by_joint_world.values()),
            key=lambda value: str(value),
        )
    )
    worst_joint = 0
    worst_ecological = 0
    for outcome in possible_outcomes:
        survivors = [
            world
            for world in active_worlds
            if outcome in support_by_joint_world[world.joint_id]
        ]
        worst_joint = max(worst_joint, len(survivors))
        worst_ecological = max(
            worst_ecological,
            len({world.ecological_world_id for world in survivors}),
        )
    return worst_joint, worst_ecological, possible_outcomes


def summarize_action(
    action_id: str,
    active_worlds: tuple[ActiveJointWorld, ...],
    support_by_joint_world: Mapping[str, frozenset[Hashable]],
) -> StochasticActionSummary:
    worst_joint, worst_ecological, outcomes = worst_case_survivors(
        active_worlds,
        support_by_joint_world,
    )
    return StochasticActionSummary(
        action_id=action_id,
        guaranteed_joint_pair_splits=guaranteed_pair_split_count(
            active_worlds,
            support_by_joint_world,
        ),
        worst_case_joint_survivors=worst_joint,
        worst_case_ecological_survivors=worst_ecological,
        possible_outcomes=outcomes,
    )


def run_stochastic_evidence_design_v28() -> dict[str, object]:
    active_worlds, target_node = build_active_joint_worlds_v28()
    supports = action_supports_v28(active_worlds)

    summaries = tuple(
        summarize_action(action_id, active_worlds, supports[action_id])
        for action_id in sorted(supports)
    )
    by_id = {row.action_id: row for row in summaries}

    # S1 is an exhaustive self-consistency audit of the support-disjoint definition.
    s1_mismatches = 0
    for action_id, action_support in supports.items():
        for left, right in combinations(active_worlds, 2):
            expected = len(
                action_support[left.joint_id].intersection(
                    action_support[right.joint_id]
                )
            ) == 0
            observed = supports_disjoint(
                action_support[left.joint_id],
                action_support[right.joint_id],
            )
            if expected != observed:
                s1_mismatches += 1

    repeat = by_id["repeat_4_same_protocol"]
    calibration = by_id["calibrate_detection_world"]
    gold = by_id["gold_standard_target_state"]

    s2_supported = (
        len(active_worlds) == 112
        and repeat.guaranteed_joint_pair_splits == 0
        and repeat.worst_case_joint_survivors == 112
        and repeat.worst_case_ecological_survivors == 64
        and calibration.guaranteed_joint_pair_splits == 3072
        and calibration.worst_case_joint_survivors == 64
        and calibration.worst_case_ecological_survivors == 64
        and gold.guaranteed_joint_pair_splits == 1536
        and gold.worst_case_joint_survivors == 96
        and gold.worst_case_ecological_survivors == 48
    )

    best_joint_value = min(row.worst_case_joint_survivors for row in summaries)
    best_joint = tuple(
        row.action_id
        for row in summaries
        if row.worst_case_joint_survivors == best_joint_value
    )
    best_ecological_value = min(
        row.worst_case_ecological_survivors for row in summaries
    )
    best_ecological = tuple(
        row.action_id
        for row in summaries
        if row.worst_case_ecological_survivors == best_ecological_value
    )
    s3_supported = (
        best_joint == ("calibrate_detection_world",)
        and best_ecological == ("gold_standard_target_state",)
    )

    def dominates(left: StochasticActionSummary, right: StochasticActionSummary) -> bool:
        no_worse = (
            left.guaranteed_joint_pair_splits >= right.guaranteed_joint_pair_splits
            and left.worst_case_joint_survivors
            <= right.worst_case_joint_survivors
            and left.worst_case_ecological_survivors
            <= right.worst_case_ecological_survivors
        )
        strictly_better = (
            left.guaranteed_joint_pair_splits > right.guaranteed_joint_pair_splits
            or left.worst_case_joint_survivors
            < right.worst_case_joint_survivors
            or left.worst_case_ecological_survivors
            < right.worst_case_ecological_survivors
        )
        return no_worse and strictly_better

    s4_supported = dominates(calibration, repeat) and dominates(gold, repeat)

    verdicts = {
        "S1_support_disjointness": (
            "SUPPORTED" if s1_mismatches == 0 else "REFUTED"
        ),
        "S2_frozen_action_values": "SUPPORTED" if s2_supported else "REFUTED",
        "S3_objective_dependent_choice": (
            "SUPPORTED" if s3_supported else "REFUTED"
        ),
        "S4_more_same_type_data_is_robustly_dominated": (
            "SUPPORTED" if s4_supported else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.stochastic_evidence_design.result.v2_8",
        "parent_v2_7_result_fingerprint": (
            "085587287263d5ebb4016455ac74406b14979e7de25e57e12b8a607becd5cd1d"
        ),
        "selected_target_node": target_node,
        "active_joint_world_count": len(active_worlds),
        "active_ecological_world_count": len(
            {world.ecological_world_id for world in active_worlds}
        ),
        "action_summaries": [
            {
                "action_id": row.action_id,
                "guaranteed_joint_pair_splits": row.guaranteed_joint_pair_splits,
                "worst_case_joint_survivors": row.worst_case_joint_survivors,
                "worst_case_ecological_survivors": row.worst_case_ecological_survivors,
                "possible_outcomes": list(row.possible_outcomes),
            }
            for row in summaries
        ],
        "best_action_joint_objective": list(best_joint),
        "best_action_ecological_objective": list(best_ecological),
        "S1_mismatches": s1_mismatches,
        "verdicts": verdicts,
    }
    result["fingerprint"] = _sha256(result)
    return result
