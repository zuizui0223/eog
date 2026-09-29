"""Observation-robust exact evidence design over a finite world universe.

A candidate evidence channel may predict a latent biological outcome for each world,
but the observation process maps that latent outcome to a set of possible observed
outcomes.  Two worlds are robustly separated only if those observable support sets are
disjoint.

This module intentionally does not use likelihood thresholds or expected information.
It is an exact/falsification planner.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import hashlib
import json
from typing import Hashable, Mapping, Sequence

from .falsification_driven_design import build_v23_intervention_library
from .generic_evidence_design import (
    equivalence_classes,
    unresolved_pairs_from_classes,
)
from .known_truth_detection import (
    ObservationWorld,
    observation_history_probability,
)


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def observed_count_support(
    true_binary_state: bool,
    *,
    surveys: int,
    observation_worlds: Sequence[ObservationWorld],
) -> frozenset[int]:
    """Union of all detection counts having positive probability in any observation world."""

    worlds = tuple(observation_worlds)
    if not worlds:
        raise ValueError("at least one observation world is required")
    if isinstance(surveys, bool) or not isinstance(surveys, int) or surveys < 1:
        raise ValueError("surveys must be a positive integer")

    state = "present" if true_binary_state else "absent"
    possible: set[int] = set()
    for detections in range(surveys + 1):
        if any(
            observation_history_probability(
                state,
                detections=detections,
                surveys=surveys,
                observation_world=world,
            )
            > 0.0
            for world in worlds
        ):
            possible.add(detections)
    return frozenset(possible)


def robustly_splits(
    left_support: frozenset[Hashable],
    right_support: frozenset[Hashable],
) -> bool:
    return left_support.isdisjoint(right_support)


def robust_split_count(
    unresolved_pairs: Sequence[tuple[str, str]],
    support_by_world: Mapping[str, frozenset[Hashable]],
) -> int:
    return sum(
        1
        for left, right in unresolved_pairs
        if robustly_splits(support_by_world[left], support_by_world[right])
    )


def robust_pair_coverage_holds(
    unresolved_pairs: Sequence[tuple[str, str]],
    evidence_supports: Mapping[str, Mapping[str, frozenset[Hashable]]],
    selected_evidence_ids: Sequence[str],
) -> bool:
    selected = tuple(selected_evidence_ids)
    for left, right in unresolved_pairs:
        if not any(
            robustly_splits(
                evidence_supports[evidence_id][left],
                evidence_supports[evidence_id][right],
            )
            for evidence_id in selected
        ):
            return False
    return True


def exact_minimum_robust_separating_set(
    current_signature_by_world: Mapping[str, Hashable],
    evidence_supports: Mapping[str, Mapping[str, frozenset[Hashable]]],
) -> tuple[str, ...] | None:
    if not current_signature_by_world:
        raise ValueError("current_signature_by_world must be non-empty")
    world_ids = tuple(sorted(current_signature_by_world))
    world_set = set(world_ids)
    evidence_ids = tuple(sorted(evidence_supports))
    if not evidence_ids:
        raise ValueError("evidence_supports must be non-empty")
    for evidence_id in evidence_ids:
        if set(evidence_supports[evidence_id]) != world_set:
            raise ValueError("every evidence channel must define support for every world")

    placeholder = {
        "placeholder": {world_id: 0 for world_id in world_ids},
    }
    current_classes = equivalence_classes(
        current_signature_by_world,
        placeholder,
    )
    unresolved = unresolved_pairs_from_classes(current_classes)
    if not unresolved:
        return ()

    for size in range(1, len(evidence_ids) + 1):
        valid = []
        for subset in combinations(evidence_ids, size):
            if robust_pair_coverage_holds(unresolved, evidence_supports, subset):
                valid.append(tuple(subset))
        if valid:
            return min(valid)
    return None


@dataclass(frozen=True)
class RobustEvidencePlan:
    unresolved_pairs: tuple[tuple[str, str], ...]
    split_counts: tuple[tuple[str, int], ...]
    minimum_separating_set: tuple[str, ...] | None
    minimum_set_size: int | None
    insufficient_library: bool
    fingerprint: str


def plan_robust_evidence(
    current_signature_by_world: Mapping[str, Hashable],
    evidence_supports: Mapping[str, Mapping[str, frozenset[Hashable]]],
) -> RobustEvidencePlan:
    world_ids = tuple(sorted(current_signature_by_world))
    placeholder = {
        "placeholder": {world_id: 0 for world_id in world_ids},
    }
    current_classes = equivalence_classes(
        current_signature_by_world,
        placeholder,
    )
    unresolved = unresolved_pairs_from_classes(current_classes)

    split_counts = tuple(
        sorted(
            (
                evidence_id,
                robust_split_count(unresolved, support_by_world),
            )
            for evidence_id, support_by_world in evidence_supports.items()
        )
    )
    minimum = exact_minimum_robust_separating_set(
        current_signature_by_world,
        evidence_supports,
    )
    insufficient = bool(unresolved) and minimum is None

    payload = {
        "unresolved_pairs": list(unresolved),
        "split_counts": list(split_counts),
        "minimum_separating_set": None if minimum is None else list(minimum),
        "insufficient_library": insufficient,
    }
    return RobustEvidencePlan(
        unresolved_pairs=unresolved,
        split_counts=split_counts,
        minimum_separating_set=minimum,
        minimum_set_size=None if minimum is None else len(minimum),
        insufficient_library=insufficient,
        fingerprint=_sha256(payload),
    )


def _supports_from_binary_interventions(
    *,
    surveys: int,
    observation_worlds: Sequence[ObservationWorld],
) -> tuple[
    dict[str, Hashable],
    dict[str, dict[str, frozenset[Hashable]]],
]:
    passive, deterministic = build_v23_intervention_library()
    supports: dict[str, dict[str, frozenset[Hashable]]] = {}

    for evidence_id in ("P_barrier_challenge", "H_long_corridor_challenge"):
        supports[evidence_id] = {
            world_id: frozenset(
                observed_count_support(
                    bool(true_outcome),
                    surveys=surveys,
                    observation_worlds=observation_worlds,
                )
            )
            for world_id, true_outcome in deterministic[evidence_id].items()
        }

    # Negative control: the already-known passive signature is observed exactly.
    supports["repeat_passive_state"] = {
        world_id: frozenset((passive_signature,))
        for world_id, passive_signature in passive.items()
    }
    return passive, supports


def run_robust_evidence_design_v27() -> dict[str, object]:
    regimes = {
        "perfect_n1": {
            "surveys": 1,
            "worlds": (ObservationWorld("perfect", 1.0, 0.0),),
        },
        "imperfect_detection_n1": {
            "surveys": 1,
            "worlds": (
                ObservationWorld("perfect", 1.0, 0.0),
                ObservationWorld("imperfect", 0.75, 0.0),
            ),
        },
        "imperfect_detection_n8": {
            "surveys": 8,
            "worlds": (
                ObservationWorld("perfect", 1.0, 0.0),
                ObservationWorld("imperfect", 0.75, 0.0),
            ),
        },
        "false_positive_n1": {
            "surveys": 1,
            "worlds": (
                ObservationWorld("perfect", 1.0, 0.0),
                ObservationWorld("false_positive", 1.0, 0.01),
            ),
        },
        "false_positive_n8": {
            "surveys": 8,
            "worlds": (
                ObservationWorld("perfect", 1.0, 0.0),
                ObservationWorld("false_positive", 1.0, 0.01),
            ),
        },
    }

    rows: dict[str, object] = {}
    plans: dict[str, RobustEvidencePlan] = {}
    support_examples: dict[str, object] = {}

    for regime_id, config in regimes.items():
        surveys = int(config["surveys"])
        observation_worlds = tuple(config["worlds"])
        passive, supports = _supports_from_binary_interventions(
            surveys=surveys,
            observation_worlds=observation_worlds,
        )
        plan = plan_robust_evidence(passive, supports)
        plans[regime_id] = plan

        split_counts = dict(plan.split_counts)
        rows[regime_id] = {
            "surveys": surveys,
            "observation_world_ids": [world.world_id for world in observation_worlds],
            "unresolved_pair_count": len(plan.unresolved_pairs),
            "split_counts": split_counts,
            "minimum_separating_set": (
                None if plan.minimum_separating_set is None
                else list(plan.minimum_separating_set)
            ),
            "minimum_set_size": plan.minimum_set_size,
            "insufficient_library": plan.insufficient_library,
            "plan_fingerprint": plan.fingerprint,
        }
        support_examples[regime_id] = {
            "true_positive_support": sorted(
                observed_count_support(
                    True,
                    surveys=surveys,
                    observation_worlds=observation_worlds,
                )
            ),
            "true_negative_support": sorted(
                observed_count_support(
                    False,
                    surveys=surveys,
                    observation_worlds=observation_worlds,
                )
            ),
        }

    perfect = plans["perfect_n1"]
    perfect_counts = dict(perfect.split_counts)
    r1 = (
        perfect_counts["P_barrier_challenge"] == 8
        and perfect_counts["H_long_corridor_challenge"] == 8
        and perfect_counts["repeat_passive_state"] == 0
        and perfect.minimum_separating_set
        == ("H_long_corridor_challenge", "P_barrier_challenge")
    )

    imperfect_ids = ("imperfect_detection_n1", "imperfect_detection_n8")
    r2 = all(
        dict(plans[key].split_counts)["P_barrier_challenge"] == 0
        and dict(plans[key].split_counts)["H_long_corridor_challenge"] == 0
        for key in imperfect_ids
    )

    false_positive_ids = ("false_positive_n1", "false_positive_n8")
    r3 = all(
        dict(plans[key].split_counts)["P_barrier_challenge"] == 0
        and dict(plans[key].split_counts)["H_long_corridor_challenge"] == 0
        for key in false_positive_ids
    )

    # Broader observation worlds must not improve exact discrimination.
    r4_violations = 0
    perfect_split = dict(perfect.split_counts)
    for key, plan in plans.items():
        if key == "perfect_n1":
            continue
        counts = dict(plan.split_counts)
        for evidence_id in perfect_split:
            if counts[evidence_id] > perfect_split[evidence_id]:
                r4_violations += 1
        if plan.minimum_set_size is not None and perfect.minimum_set_size is not None:
            if plan.minimum_set_size < perfect.minimum_set_size:
                r4_violations += 1

    uncertain_ids = (*imperfect_ids, *false_positive_ids)
    r5 = all(
        plans[key].minimum_separating_set is None
        and plans[key].insufficient_library
        for key in uncertain_ids
    )

    verdicts = {
        "R1_perfect_reduces_to_deterministic": "SUPPORTED" if r1 else "REFUTED",
        "R2_imperfect_detection_blocks_exact_split": "SUPPORTED" if r2 else "REFUTED",
        "R3_false_positive_blocks_exact_split": "SUPPORTED" if r3 else "REFUTED",
        "R4_observation_uncertainty_cannot_improve_exact_design": (
            "SUPPORTED" if r4_violations == 0 else "REFUTED"
        ),
        "R5_fail_closed_under_unobservable_intervention": (
            "SUPPORTED" if r5 else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.robust_finite_evidence_design.result.v2_7",
        "parent_generic_design_fingerprint": (
            "a2365bcd014ebbe2722f8c04a3df0f149a4eb6af2fcf97b27cf11435721d8abd"
        ),
        "parent_observation_boundary_fingerprint": (
            "3e5187088b74a443471c79743d78fc86c02a5d87565f3f51fb0f081669c46091"
        ),
        "regimes": rows,
        "observed_support_examples": support_examples,
        "observation_uncertainty_monotonicity_violations": r4_violations,
        "verdicts": verdicts,
    }
    result["fingerprint"] = _sha256(result)
    return result
