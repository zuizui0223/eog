"""Orthogonally activated known-truth BAM simulation v2.1.

This successor exists because BAM v2 did not independently activate all A/B/M axes.
It therefore performs a structural activation audit before any hypothesis scoring.
Failure of an activation gate is a terminal STOP for this protocol version.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .known_truth_biogeography import make_gradient_landscape
from .known_truth_bam import (
    AuxiliaryBioticState,
    BAMWorld,
    abiotic_mask,
    axis_witnesses,
    biotic_mask,
    build_bam_world,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
    movement_state,
)


@dataclass(frozen=True)
class BAMActivationAuditV21:
    passed: bool
    partner_fraction: float
    antagonist_fraction: float
    witness_counts: tuple[tuple[str, int], ...]
    same_g_different_arrival_pairs: int
    positive_superset_negative_witness_pairs: int
    failed_gates: tuple[str, ...]


def make_bam_v21_landscape():
    return make_gradient_landscape(
        width=7,
        height=3,
        spike_col=3,
        spike_amount=0.45,
        barrier_col=4,
        barrier_gap_rows=(),
    )


def _auxiliary_mask(
    landscape,
    *,
    source_id: str,
    niche_center: tuple[float, float],
    niche_radius: tuple[float, float],
    step_radius: float,
    barrier_permeable: bool,
    horizon: int,
) -> int:
    a = abiotic_mask(landscape, center=niche_center, radius=niche_radius)
    m = movement_state(
        landscape,
        source_id=source_id,
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
        horizon=horizon,
    ).accessible_mask
    return a & m


def generate_biotic_state_v21(landscape) -> AuxiliaryBioticState:
    partner = _auxiliary_mask(
        landscape,
        source_id="r1c2",
        niche_center=(0.35, 0.54),
        niche_radius=(0.18, 0.15),
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    )
    antagonist = _auxiliary_mask(
        landscape,
        source_id="r1c5",
        niche_center=(0.61, 0.43),
        niche_radius=(0.14, 0.12),
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    )
    # Reuse the parent dataclass; the fingerprint is not used as a scientific
    # comparison quantity in v2.1.
    return AuxiliaryBioticState(
        partner_mask=partner,
        antagonist_mask=antagonist,
        fingerprint=f"v21:{partner}:{antagonist}",
    )


def build_world_grid_v21() -> tuple[BAMWorld, ...]:
    landscape = make_bam_v21_landscape()
    b_state = generate_biotic_state_v21(landscape)
    a_specs = (
        ("A_narrow", (0.45, 0.50), (0.35, 0.20)),
        ("A_broad", (0.45, 0.50), (0.80, 0.50)),
    )
    b_modes = (
        "none",
        "obligate_partner",
        "antagonist_exclusion",
        "partner_and_antagonist",
    )
    m_specs = (
        ("M_short_closed_h2", 1.01, False, 2),
        ("M_long_closed_h2", 2.01, False, 2),
        ("M_long_open_h2", 2.01, True, 2),
        ("M_short_open_h8", 1.01, True, 8),
        ("M_long_open_h8", 2.01, True, 8),
    )
    worlds: list[BAMWorld] = []
    for a_label, center, radius in a_specs:
        for b_mode in b_modes:
            for m_label, step_radius, barrier_permeable, horizon in m_specs:
                worlds.append(
                    build_bam_world(
                        landscape,
                        world_id=f"{a_label}|B_{b_mode}|{m_label}",
                        abiotic_label=a_label,
                        niche_center=center,
                        niche_radius=radius,
                        biotic_state=b_state,
                        biotic_mode=b_mode,
                        movement_label=m_label,
                        source_id="r1c0",
                        step_radius=step_radius,
                        barrier_permeable=barrier_permeable,
                        horizon=horizon,
                    )
                )
    return tuple(sorted(worlds, key=lambda world: world.world_id))


def _world(
    worlds: Sequence[BAMWorld],
    a: str,
    b: str,
    m: str,
) -> BAMWorld:
    target = f"{a}|B_{b}|{m}"
    for world in worlds:
        if world.world_id == target:
            return world
    raise KeyError(target)


def _nonempty_only(
    truth: BAMWorld,
    false_world: BAMWorld,
    axis: str,
) -> int:
    witnesses = axis_witnesses(truth, false_world)
    if not witnesses[axis]:
        return 0
    if any(witnesses[other] for other in ("A", "B", "M") if other != axis):
        return 0
    return len(witnesses[axis])


def activation_audit_v21(worlds: Sequence[BAMWorld]) -> BAMActivationAuditV21:
    landscape = make_bam_v21_landscape()
    b_state = generate_biotic_state_v21(landscape)
    n = len(landscape.node_ids)
    partner_fraction = b_state.partner_mask.bit_count() / n
    antagonist_fraction = b_state.antagonist_mask.bit_count() / n

    witness_counts = {
        "A_only": _nonempty_only(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_narrow", "none", "M_long_open_h8"),
            "A",
        ),
        "B_partner_only": _nonempty_only(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_broad", "obligate_partner", "M_long_open_h8"),
            "B",
        ),
        "B_antagonist_only": _nonempty_only(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_broad", "antagonist_exclusion", "M_long_open_h8"),
            "B",
        ),
        "M_distance_only": _nonempty_only(
            _world(worlds, "A_broad", "none", "M_long_closed_h2"),
            _world(worlds, "A_broad", "none", "M_short_closed_h2"),
            "M",
        ),
        "M_barrier_only": _nonempty_only(
            _world(worlds, "A_broad", "none", "M_long_open_h2"),
            _world(worlds, "A_broad", "none", "M_long_closed_h2"),
            "M",
        ),
    }

    same_g_different_arrival_pairs = 0
    for i, left in enumerate(worlds):
        for right in worlds[i + 1 :]:
            if left.occupied_mask != right.occupied_mask:
                continue
            occupied_indices = [
                idx
                for idx in range(len(left.node_ids))
                if left.occupied_mask & (1 << idx)
            ]
            if any(
                left.first_arrival_steps[idx] != right.first_arrival_steps[idx]
                for idx in occupied_indices
            ):
                same_g_different_arrival_pairs += 1

    positive_superset_negative_witness_pairs = 0
    for truth in worlds:
        for false_world in worlds:
            if truth.world_id == false_world.world_id:
                continue
            if truth.occupied_mask & ~false_world.occupied_mask:
                continue
            if false_world.occupied_mask & ~truth.occupied_mask:
                positive_superset_negative_witness_pairs += 1

    failed: list[str] = []
    if not (0.2 <= partner_fraction <= 0.8):
        failed.append("partner_occupancy_fraction")
    if not (0.2 <= antagonist_fraction <= 0.8):
        failed.append("antagonist_occupancy_fraction")
    for key, value in witness_counts.items():
        if value < 1:
            failed.append(key)
    if same_g_different_arrival_pairs < 1:
        failed.append("same_G_different_arrival_pair")
    if positive_superset_negative_witness_pairs < 1:
        failed.append("positive_superset_negative_witness_pair")

    return BAMActivationAuditV21(
        passed=not failed,
        partner_fraction=partner_fraction,
        antagonist_fraction=antagonist_fraction,
        witness_counts=tuple(sorted(witness_counts.items())),
        same_g_different_arrival_pairs=same_g_different_arrival_pairs,
        positive_superset_negative_witness_pairs=positive_superset_negative_witness_pairs,
        failed_gates=tuple(failed),
    )


def run_bam_v21() -> dict[str, object]:
    worlds = build_world_grid_v21()
    audit = activation_audit_v21(worlds)
    if not audit.passed:
        return {
            "schema": "eog.known_truth_bam.orthogonal_result.v2_1",
            "status": "ACTIVATION_STOP",
            "activation_audit": {
                "partner_fraction": audit.partner_fraction,
                "antagonist_fraction": audit.antagonist_fraction,
                "witness_counts": dict(audit.witness_counts),
                "same_g_different_arrival_pairs": audit.same_g_different_arrival_pairs,
                "positive_superset_negative_witness_pairs": audit.positive_superset_negative_witness_pairs,
                "failed_gates": list(audit.failed_gates),
            },
        }

    landscape = make_bam_v21_landscape()
    eligible = 0
    truth_retention_failures = 0
    axis_witness_mismatches = 0
    equivalence_violations = 0
    superset_violations = 0
    negative_rescue_failures = 0
    temporal_rescue_failures = 0
    positive_unique = 0
    negative_unique = 0
    temporal_unique = 0
    negative_rescuable = 0
    negative_rescued = 0
    temporal_rescuable = 0
    temporal_rescued = 0
    partner_dependency_positive_unidentifiable = 0
    partner_dependency_negative_rescued = 0
    antagonist_dependency_positive_unidentifiable = 0
    antagonist_dependency_negative_rescued = 0
    cases: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible += 1
        positive_result = compatible_positive_only(worlds, positives)
        if truth.world_id not in positive_result.compatible_world_ids:
            truth_retention_failures += 1
        if positive_result.compatible_world_ids == (truth.world_id,):
            positive_unique += 1

        exact_g = tuple(
            world.world_id
            for world in worlds
            if world.occupied_mask == truth.occupied_mask
        )
        if not set(exact_g).issubset(positive_result.compatible_world_ids):
            equivalence_violations += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            witnesses = axis_witnesses(truth, false_world)
            union = set(witnesses["A"]) | set(witnesses["B"]) | set(witnesses["M"])
            eliminated = false_world.world_id not in positive_result.compatible_world_ids
            if eliminated != bool(union):
                axis_witness_mismatches += 1
            if truth.occupied_mask & ~false_world.occupied_mask == 0:
                if eliminated:
                    superset_violations += 1

        negatives = tuple(
            node_id for node_id in landscape.node_ids if node_id not in set(positives)
        )
        negative_result = compatible_with_perfect_negatives(worlds, positives, negatives)
        if negative_result.compatible_world_ids == (truth.world_id,):
            negative_unique += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            if truth.occupied_mask & ~false_world.occupied_mask:
                continue
            extra = false_world.occupied_mask & ~truth.occupied_mask
            if extra:
                negative_rescuable += 1
                if false_world.world_id not in negative_result.compatible_world_ids:
                    negative_rescued += 1
                else:
                    negative_rescue_failures += 1

        temporal_obs = {
            node_id: int(truth.first_arrival_steps[idx])
            for idx, node_id in enumerate(truth.node_ids)
            if node_id in set(positives)
            and truth.first_arrival_steps[idx] is not None
        }
        temporal_result = compatible_with_temporal_arrivals(
            worlds,
            positives,
            negatives,
            temporal_obs,
        )
        if temporal_result.compatible_world_ids == (truth.world_id,):
            temporal_unique += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            if false_world.occupied_mask != truth.occupied_mask:
                continue
            differs = any(
                false_world.first_arrival_steps[idx] != truth.first_arrival_steps[idx]
                for idx, node_id in enumerate(truth.node_ids)
                if node_id in set(positives)
            )
            if differs:
                temporal_rescuable += 1
                if false_world.world_id not in temporal_result.compatible_world_ids:
                    temporal_rescued += 1
                else:
                    temporal_rescue_failures += 1

        # Directional interaction-identifiability audit.
        if truth.biotic_mode == "obligate_partner":
            no_b = _world(worlds, truth.abiotic_label, "none", truth.movement_label)
            if no_b.world_id in positive_result.compatible_world_ids:
                partner_dependency_positive_unidentifiable += 1
                if (
                    no_b.occupied_mask & ~truth.occupied_mask
                    and no_b.world_id not in negative_result.compatible_world_ids
                ):
                    partner_dependency_negative_rescued += 1
        if truth.biotic_mode == "antagonist_exclusion":
            no_b = _world(worlds, truth.abiotic_label, "none", truth.movement_label)
            if no_b.world_id in positive_result.compatible_world_ids:
                antagonist_dependency_positive_unidentifiable += 1
                if (
                    no_b.occupied_mask & ~truth.occupied_mask
                    and no_b.world_id not in negative_result.compatible_world_ids
                ):
                    antagonist_dependency_negative_rescued += 1

        cases.append(
            {
                "truth_world_id": truth.world_id,
                "positive_compatible_count": len(positive_result.compatible_world_ids),
                "negative_compatible_count": len(negative_result.compatible_world_ids),
                "temporal_compatible_count": len(temporal_result.compatible_world_ids),
                "exact_G_equivalence_size": len(exact_g),
            }
        )

    verdicts = {
        "BAM_H1_truth_retention": "SUPPORTED" if truth_retention_failures == 0 else "REFUTED",
        "BAM_H2_axis_witness_attribution": "SUPPORTED" if axis_witness_mismatches == 0 else "REFUTED",
        "BAM_H3_intersection_nonidentifiability": "SUPPORTED" if equivalence_violations == 0 else "REFUTED",
        "BAM_H4_positive_superset_ceiling": "SUPPORTED" if superset_violations == 0 else "REFUTED",
        "BAM_H5_perfect_negative_rescue": (
            "SUPPORTED" if negative_rescuable > 0 and negative_rescue_failures == 0 else "REFUTED"
        ),
        "BAM_H6_temporal_M_rescue": (
            "SUPPORTED" if temporal_rescuable > 0 and temporal_rescue_failures == 0 else "REFUTED"
        ),
    }
    return {
        "schema": "eog.known_truth_bam.orthogonal_result.v2_1",
        "status": "SCORED",
        "activation_audit": {
            "partner_fraction": audit.partner_fraction,
            "antagonist_fraction": audit.antagonist_fraction,
            "witness_counts": dict(audit.witness_counts),
            "same_g_different_arrival_pairs": audit.same_g_different_arrival_pairs,
            "positive_superset_negative_witness_pairs": audit.positive_superset_negative_witness_pairs,
            "failed_gates": [],
        },
        "candidate_world_count": len(worlds),
        "eligible_truth_worlds": eligible,
        "truth_retention_failures": truth_retention_failures,
        "axis_witness_mismatches": axis_witness_mismatches,
        "equivalence_violations": equivalence_violations,
        "positive_superset_violations": superset_violations,
        "negative_rescue_failures": negative_rescue_failures,
        "temporal_rescue_failures": temporal_rescue_failures,
        "fraction_truth_unique_positive_only": 0.0 if eligible == 0 else positive_unique / eligible,
        "fraction_truth_unique_with_negatives": 0.0 if eligible == 0 else negative_unique / eligible,
        "fraction_truth_unique_with_temporal_evidence": 0.0 if eligible == 0 else temporal_unique / eligible,
        "negative_rescue_fraction": 0.0 if negative_rescuable == 0 else negative_rescued / negative_rescuable,
        "temporal_M_rescue_fraction": 0.0 if temporal_rescuable == 0 else temporal_rescued / temporal_rescuable,
        "partner_dependency_positive_unidentifiable": partner_dependency_positive_unidentifiable,
        "partner_dependency_negative_rescued": partner_dependency_negative_rescued,
        "antagonist_dependency_positive_unidentifiable": antagonist_dependency_positive_unidentifiable,
        "antagonist_dependency_negative_rescued": antagonist_dependency_negative_rescued,
        "verdicts": verdicts,
        "cases": cases,
    }
