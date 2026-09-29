"""Intervention identifiability for dormant BAM movement parameters (v2.3).

This experiment starts from the frozen v2.2 result: complete passive A/B/M state
evidence leaves parameter aliases that differ only in barrier permeability P or
movement horizon H.  It tests whether finite, axis-specific interventions activate
those dormant parameters without changing the passive BAM result.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json

from .known_truth_bam import movement_state
from .known_truth_bam_v2_1 import build_v21_system, make_v21_landscape
from .known_truth_biogeography import make_gradient_landscape


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _passive_state_key(world) -> tuple[object, ...]:
    return (
        world.abiotic_mask,
        world.biotic_mask,
        world.movement_mask,
        world.first_arrival_steps,
    )


def _p_barrier_challenge(step_radius: float, barrier_permeable: bool) -> bool:
    """Standardized one-step crossing challenge for P."""

    landscape = make_v21_landscape()
    state = movement_state(
        landscape,
        source_id="r1c3",
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
        horizon=1,
    )
    target_index = landscape.node_ids.index("r1c4")
    return bool(state.accessible_mask & (1 << target_index))


def _h_corridor_challenge(step_radius: float, horizon: int) -> bool:
    """Barrier-free long-corridor challenge for H."""

    landscape = make_gradient_landscape(
        width=9,
        height=3,
        spike_col=None,
        barrier_col=None,
    )
    state = movement_state(
        landscape,
        source_id="r1c0",
        step_radius=step_radius,
        barrier_permeable=True,
        horizon=horizon,
    )
    target_index = landscape.node_ids.index("r1c8")
    return bool(state.accessible_mask & (1 << target_index))


def run_bam_intervention_v23() -> dict[str, object]:
    system = build_v21_system()
    worlds = system.worlds
    axes_by = system.axes_by_world

    passive_classes: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for world in worlds:
        passive_classes[_passive_state_key(world)].append(world.world_id)

    alias_rows: list[dict[str, object]] = []
    p_only_classes = 0
    h_only_classes = 0
    p_split = 0
    h_split = 0
    i1_failures = 0
    i2_failures = 0

    for world_ids in passive_classes.values():
        rows = [axes_by[world_id] for world_id in world_ids]
        varying: list[str] = []
        if len({row.abiotic_label for row in rows}) > 1:
            varying.append("A")
        if len({row.biotic_mode for row in rows}) > 1:
            varying.append("B")
        if len({row.step_radius for row in rows}) > 1:
            varying.append("D")
        if len({row.barrier_permeable for row in rows}) > 1:
            varying.append("P")
        if len({row.horizon for row in rows}) > 1:
            varying.append("H")

        p_outcomes = {
            world_id: _p_barrier_challenge(
                axes_by[world_id].step_radius,
                axes_by[world_id].barrier_permeable,
            )
            for world_id in world_ids
        }
        h_outcomes = {
            world_id: _h_corridor_challenge(
                axes_by[world_id].step_radius,
                axes_by[world_id].horizon,
            )
            for world_id in world_ids
        }

        if len(world_ids) > 1 and varying == ["P"]:
            p_only_classes += 1
            split = len(set(p_outcomes.values())) == len(world_ids)
            if split:
                p_split += 1
            else:
                i1_failures += 1
        if len(world_ids) > 1 and varying == ["H"]:
            h_only_classes += 1
            split = len(set(h_outcomes.values())) == len(world_ids)
            if split:
                h_split += 1
            else:
                i2_failures += 1

        alias_rows.append(
            {
                "world_ids": sorted(world_ids),
                "class_size": len(world_ids),
                "varying_axes": varying,
                "P_challenge_outcomes": dict(sorted(p_outcomes.items())),
                "H_challenge_outcomes": dict(sorted(h_outcomes.items())),
            }
        )

    # I3: challenge response must be independent of the non-target alias parameter.
    specificity_violations = 0
    axes_rows = list(system.axes)
    for left in axes_rows:
        for right in axes_rows:
            if left.world_id >= right.world_id:
                continue

            # P challenge: match everything except H. P challenge forces horizon=1.
            same_for_p = (
                left.abiotic_label == right.abiotic_label
                and left.biotic_mode == right.biotic_mode
                and left.step_radius == right.step_radius
                and left.barrier_permeable == right.barrier_permeable
                and left.horizon != right.horizon
            )
            if same_for_p:
                if _p_barrier_challenge(
                    left.step_radius, left.barrier_permeable
                ) != _p_barrier_challenge(
                    right.step_radius, right.barrier_permeable
                ):
                    specificity_violations += 1

            # H challenge: no barrier, so match everything except P.
            same_for_h = (
                left.abiotic_label == right.abiotic_label
                and left.biotic_mode == right.biotic_mode
                and left.step_radius == right.step_radius
                and left.horizon == right.horizon
                and left.barrier_permeable != right.barrier_permeable
            )
            if same_for_h:
                if _h_corridor_challenge(
                    left.step_radius, left.horizon
                ) != _h_corridor_challenge(
                    right.step_radius, right.horizon
                ):
                    specificity_violations += 1

    augmented_classes: dict[tuple[object, ...], list[str]] = defaultdict(list)
    intervention_rows: list[dict[str, object]] = []
    for world in worlds:
        axes = axes_by[world.world_id]
        p_outcome = _p_barrier_challenge(
            axes.step_radius,
            axes.barrier_permeable,
        )
        h_outcome = _h_corridor_challenge(
            axes.step_radius,
            axes.horizon,
        )
        key = (*_passive_state_key(world), p_outcome, h_outcome)
        augmented_classes[key].append(world.world_id)
        intervention_rows.append(
            {
                "world_id": world.world_id,
                "P_challenge_crossed": p_outcome,
                "H_challenge_target_reached": h_outcome,
            }
        )

    passive_size_distribution = Counter(len(ids) for ids in passive_classes.values())
    augmented_size_distribution = Counter(len(ids) for ids in augmented_classes.values())
    unique_worlds_after = sum(
        len(ids) for ids in augmented_classes.values() if len(ids) == 1
    )

    verdicts = {
        "I1_P_alias_activation": "SUPPORTED" if i1_failures == 0 and p_only_classes > 0 else "REFUTED",
        "I2_H_alias_activation": "SUPPORTED" if i2_failures == 0 and h_only_classes > 0 else "REFUTED",
        "I3_axis_specificity": "SUPPORTED" if specificity_violations == 0 else "REFUTED",
        "I4_full_parameter_recovery": (
            "SUPPORTED"
            if len(augmented_classes) == len(worlds)
            and all(len(ids) == 1 for ids in augmented_classes.values())
            else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_intervention.result.v2_3",
        "parent_v2_2_result_fingerprint": "5912231d6b8d04fd1cbb3540bf137562c394aca9fc40069486d6350ee7fff9f0",
        "candidate_world_count": len(worlds),
        "number_of_passive_equivalence_classes": len(passive_classes),
        "passive_class_size_distribution": {
            str(key): value for key, value in sorted(passive_size_distribution.items())
        },
        "P_only_alias_classes": p_only_classes,
        "H_only_alias_classes": h_only_classes,
        "P_alias_classes_split": p_split,
        "H_alias_classes_split": h_split,
        "I1_failures": i1_failures,
        "I2_failures": i2_failures,
        "axis_specificity_violations": specificity_violations,
        "number_of_intervention_augmented_classes": len(augmented_classes),
        "intervention_augmented_class_size_distribution": {
            str(key): value for key, value in sorted(augmented_size_distribution.items())
        },
        "world_fraction_uniquely_identified_after_intervention": (
            0.0 if not worlds else unique_worlds_after / len(worlds)
        ),
        "verdicts": verdicts,
        "alias_classes": sorted(
            alias_rows,
            key=lambda row: (row["class_size"], row["world_ids"]),
        ),
        "intervention_outcomes": sorted(
            intervention_rows,
            key=lambda row: row["world_id"],
        ),
    }
    result["fingerprint"] = _sha256(result)
    return result
