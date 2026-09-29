"""Exact finite intervention planner for falsification-driven evidence design.

The planner assumes a finite declared world universe and already-known passive
signatures.  It asks which predeclared interventions split currently unresolved
world pairs and finds an exact minimum separating intervention set.

No probabilities, utilities, or post-outcome intervention invention are used.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import hashlib
import json
from typing import Hashable, Mapping, Sequence

from .known_truth_bam_v2_1 import build_v21_system
from .known_truth_bam_v2_3 import (
    _h_corridor_challenge,
    _p_barrier_challenge,
    _passive_state_key,
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


@dataclass(frozen=True)
class InterventionRanking:
    intervention_id: str
    split_unresolved_pairs: int
    unresolved_pairs_remaining: int
    augmented_class_size_distribution: tuple[tuple[int, int], ...]
    largest_residual_class: int


@dataclass(frozen=True)
class InterventionPlan:
    passive_unresolved_pairs: tuple[tuple[str, str], ...]
    rankings: tuple[InterventionRanking, ...]
    minimum_separating_set: tuple[str, ...] | None
    minimum_set_size: int | None
    all_worlds_separated: bool
    fingerprint: str


def _unordered_pairs(values: Sequence[str]) -> tuple[tuple[str, str], ...]:
    ordered = tuple(sorted(values))
    return tuple(
        (ordered[i], ordered[j])
        for i in range(len(ordered))
        for j in range(i + 1, len(ordered))
    )


def passive_unresolved_pairs(
    passive_signature_by_world: Mapping[str, Hashable],
) -> tuple[tuple[str, str], ...]:
    groups: dict[Hashable, list[str]] = defaultdict(list)
    for world_id, signature in passive_signature_by_world.items():
        groups[signature].append(world_id)
    pairs: list[tuple[str, str]] = []
    for ids in groups.values():
        pairs.extend(_unordered_pairs(ids))
    return tuple(sorted(pairs))


def _augmented_signature(
    world_id: str,
    passive_signature_by_world: Mapping[str, Hashable],
    intervention_outcomes: Mapping[str, Mapping[str, Hashable]],
    selected: Sequence[str],
) -> tuple[Hashable, ...]:
    return (
        passive_signature_by_world[world_id],
        *(
            intervention_outcomes[intervention_id][world_id]
            for intervention_id in selected
        ),
    )


def augmented_equivalence_classes(
    passive_signature_by_world: Mapping[str, Hashable],
    intervention_outcomes: Mapping[str, Mapping[str, Hashable]],
    selected: Sequence[str],
) -> tuple[tuple[str, ...], ...]:
    groups: dict[tuple[Hashable, ...], list[str]] = defaultdict(list)
    for world_id in sorted(passive_signature_by_world):
        groups[
            _augmented_signature(
                world_id,
                passive_signature_by_world,
                intervention_outcomes,
                selected,
            )
        ].append(world_id)
    return tuple(
        sorted((tuple(sorted(ids)) for ids in groups.values()), key=lambda ids: (len(ids), ids))
    )


def split_pair_count(
    unresolved_pairs: Sequence[tuple[str, str]],
    outcome_by_world: Mapping[str, Hashable],
) -> int:
    return sum(
        1
        for left, right in unresolved_pairs
        if outcome_by_world[left] != outcome_by_world[right]
    )


def pair_coverage_holds(
    unresolved_pairs: Sequence[tuple[str, str]],
    intervention_outcomes: Mapping[str, Mapping[str, Hashable]],
    selected: Sequence[str],
) -> bool:
    for left, right in unresolved_pairs:
        if not any(
            intervention_outcomes[intervention_id][left]
            != intervention_outcomes[intervention_id][right]
            for intervention_id in selected
        ):
            return False
    return True


def exact_minimum_separating_set(
    passive_signature_by_world: Mapping[str, Hashable],
    intervention_outcomes: Mapping[str, Mapping[str, Hashable]],
) -> tuple[str, ...] | None:
    interventions = tuple(sorted(intervention_outcomes))
    unresolved = passive_unresolved_pairs(passive_signature_by_world)
    if not unresolved:
        return ()
    for size in range(1, len(interventions) + 1):
        valid: list[tuple[str, ...]] = []
        for subset in combinations(interventions, size):
            if pair_coverage_holds(unresolved, intervention_outcomes, subset):
                valid.append(tuple(subset))
        if valid:
            return min(valid)
    return None


def build_v23_intervention_library() -> tuple[
    dict[str, Hashable],
    dict[str, dict[str, Hashable]],
]:
    system = build_v21_system()
    axes_by = system.axes_by_world

    passive = {
        world.world_id: _passive_state_key(world)
        for world in system.worlds
    }
    p_outcomes = {
        world.world_id: _p_barrier_challenge(
            axes_by[world.world_id].step_radius,
            axes_by[world.world_id].barrier_permeable,
        )
        for world in system.worlds
    }
    h_outcomes = {
        world.world_id: _h_corridor_challenge(
            axes_by[world.world_id].step_radius,
            axes_by[world.world_id].horizon,
        )
        for world in system.worlds
    }

    # This is intentionally redundant: re-observing the already-known passive
    # signature cannot split any pair that is passive-equivalent.
    repeat_passive = {
        world_id: passive_signature
        for world_id, passive_signature in passive.items()
    }

    return passive, {
        "P_barrier_challenge": p_outcomes,
        "H_long_corridor_challenge": h_outcomes,
        "repeat_passive_state": repeat_passive,
    }


def plan_v24() -> dict[str, object]:
    passive, interventions = build_v23_intervention_library()
    unresolved = passive_unresolved_pairs(passive)

    rankings: list[InterventionRanking] = []
    for intervention_id in sorted(interventions):
        classes = augmented_equivalence_classes(
            passive,
            interventions,
            (intervention_id,),
        )
        size_dist = Counter(len(ids) for ids in classes)
        split = split_pair_count(unresolved, interventions[intervention_id])
        remaining = len(unresolved) - split
        rankings.append(
            InterventionRanking(
                intervention_id=intervention_id,
                split_unresolved_pairs=split,
                unresolved_pairs_remaining=remaining,
                augmented_class_size_distribution=tuple(sorted(size_dist.items())),
                largest_residual_class=max(len(ids) for ids in classes),
            )
        )

    rankings.sort(
        key=lambda row: (
            -row.split_unresolved_pairs,
            row.largest_residual_class,
            row.intervention_id,
        )
    )

    minimum = exact_minimum_separating_set(passive, interventions)
    if minimum is None:
        final_classes = augmented_equivalence_classes(passive, interventions, ())
        all_separated = False
    else:
        final_classes = augmented_equivalence_classes(passive, interventions, minimum)
        all_separated = all(len(ids) == 1 for ids in final_classes)

    # E1 checks every intervention subset, not only the optimum.
    pair_cover_mismatches = 0
    ids = tuple(sorted(interventions))
    for size in range(0, len(ids) + 1):
        for subset in combinations(ids, size):
            cover = pair_coverage_holds(unresolved, interventions, subset)
            classes = augmented_equivalence_classes(passive, interventions, subset)
            injective = all(len(group) == 1 for group in classes)
            if cover != injective:
                pair_cover_mismatches += 1

    by_id = {row.intervention_id: row for row in rankings}
    e2_supported = (
        len(unresolved) == 16
        and by_id["P_barrier_challenge"].split_unresolved_pairs == 8
        and by_id["H_long_corridor_challenge"].split_unresolved_pairs == 8
        and by_id["repeat_passive_state"].split_unresolved_pairs == 0
    )
    e3_supported = (
        minimum == ("H_long_corridor_challenge", "P_barrier_challenge")
        and all_separated
    )
    verdicts = {
        "E1_pair_cover_equivalence": (
            "SUPPORTED" if pair_cover_mismatches == 0 else "REFUTED"
        ),
        "E2_current_library_structure": (
            "SUPPORTED" if e2_supported else "REFUTED"
        ),
        "E3_minimum_design": (
            "SUPPORTED" if e3_supported else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.falsification_driven_experiment_design.result.v2_4",
        "parent_v2_3_result_fingerprint": "654ec11ce21455989b399c7668f06595cd499b5acb347b78bdc17582f92960f2",
        "world_count": len(passive),
        "passive_unresolved_pair_count": len(unresolved),
        "passive_unresolved_pairs": list(unresolved),
        "ranked_interventions": [
            {
                "intervention_id": row.intervention_id,
                "split_unresolved_pairs": row.split_unresolved_pairs,
                "unresolved_pairs_remaining": row.unresolved_pairs_remaining,
                "augmented_class_size_distribution": {
                    str(size): count
                    for size, count in row.augmented_class_size_distribution
                },
                "largest_residual_class": row.largest_residual_class,
            }
            for row in rankings
        ],
        "minimum_separating_set": (
            None if minimum is None else list(minimum)
        ),
        "minimum_set_size": (
            None if minimum is None else len(minimum)
        ),
        "all_worlds_separated": all_separated,
        "pair_cover_mismatches": pair_cover_mismatches,
        "final_class_size_distribution": dict(
            sorted(Counter(len(ids) for ids in final_classes).items())
        ),
        "verdicts": verdicts,
    }
    result["fingerprint"] = _sha256(result)
    return result
