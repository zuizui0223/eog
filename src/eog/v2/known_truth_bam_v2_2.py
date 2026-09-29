"""Source-compatible, interaction-complete BAM known-truth simulation v2.2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .known_truth_bam import (
    AuxiliaryBioticState,
    BAMWorld,
    abiotic_mask,
    axis_witnesses,
    build_bam_world,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
    movement_state,
)
from .known_truth_bam_v2_1 import make_bam_v21_landscape


@dataclass(frozen=True)
class BAMActivationAuditV22:
    passed: bool
    partner_fraction: float
    antagonist_fraction: float
    focal_source_in_partner: bool
    biotic_masks_pairwise_distinct: bool
    eligible_truth_counts_by_B: tuple[tuple[str, int], ...]
    eligible_truth_counts_by_A: tuple[tuple[str, int], ...]
    eligible_truth_counts_by_M: tuple[tuple[str, int], ...]
    witness_counts: tuple[tuple[str, int], ...]
    same_g_different_arrival_pairs: int
    positive_superset_negative_witness_pairs: int
    failed_gates: tuple[str, ...]


def _auxiliary_mask(
    landscape,
    *,
    source_id: str,
    niche_center: tuple[float, float],
    niche_radius: tuple[float, float],
) -> int:
    a = abiotic_mask(landscape, center=niche_center, radius=niche_radius)
    m = movement_state(
        landscape,
        source_id=source_id,
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    ).accessible_mask
    return a & m


def generate_biotic_state_v22(landscape) -> AuxiliaryBioticState:
    partner = _auxiliary_mask(
        landscape,
        source_id="r1c0",
        niche_center=(0.24, 0.575),
        niche_radius=(0.20, 0.10),
    )
    antagonist = _auxiliary_mask(
        landscape,
        source_id="r1c5",
        niche_center=(0.50, 0.48),
        niche_radius=(0.25, 0.15),
    )
    return AuxiliaryBioticState(
        partner_mask=partner,
        antagonist_mask=antagonist,
        fingerprint=f"v22:{partner}:{antagonist}",
    )


def build_world_grid_v22() -> tuple[BAMWorld, ...]:
    landscape = make_bam_v21_landscape()
    state = generate_biotic_state_v22(landscape)
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
                        biotic_state=state,
                        biotic_mode=b_mode,
                        movement_label=m_label,
                        source_id="r1c0",
                        step_radius=step_radius,
                        barrier_permeable=barrier_permeable,
                        horizon=horizon,
                    )
                )
    return tuple(sorted(worlds, key=lambda world: world.world_id))


def _world(worlds: Sequence[BAMWorld], a: str, b: str, m: str) -> BAMWorld:
    wanted = f"{a}|B_{b}|{m}"
    for world in worlds:
        if world.world_id == wanted:
            return world
    raise KeyError(wanted)


def _only_axis_witness_count(truth: BAMWorld, false_world: BAMWorld, axis: str) -> int:
    witnesses = axis_witnesses(truth, false_world)
    if not witnesses[axis]:
        return 0
    if any(witnesses[other] for other in ("A", "B", "M") if other != axis):
        return 0
    return len(witnesses[axis])


def activation_audit_v22(worlds: Sequence[BAMWorld]) -> BAMActivationAuditV22:
    landscape = make_bam_v21_landscape()
    state = generate_biotic_state_v22(landscape)
    n = len(landscape.node_ids)
    partner_fraction = state.partner_mask.bit_count() / n
    antagonist_fraction = state.antagonist_mask.bit_count() / n
    source_index = landscape.node_ids.index("r1c0")
    source_bit = 1 << source_index
    source_in_partner = bool(state.partner_mask & source_bit)

    representative = [
        _world(worlds, "A_broad", b, "M_long_open_h8")
        for b in (
            "none",
            "obligate_partner",
            "antagonist_exclusion",
            "partner_and_antagonist",
        )
    ]
    biotic_masks_pairwise_distinct = len({w.biotic_mask for w in representative}) == 4

    eligible = [
        world
        for world in worlds
        if len(world.occupied_ids) >= 2 and "r1c0" in world.occupied_ids
    ]
    counts_b = {
        mode: sum(world.biotic_mode == mode for world in eligible)
        for mode in (
            "none",
            "obligate_partner",
            "antagonist_exclusion",
            "partner_and_antagonist",
        )
    }
    counts_a = {
        label: sum(world.abiotic_label == label for world in eligible)
        for label in ("A_narrow", "A_broad")
    }
    counts_m = {
        label: sum(world.movement_label == label for world in eligible)
        for label in (
            "M_short_closed_h2",
            "M_long_closed_h2",
            "M_long_open_h2",
            "M_short_open_h8",
            "M_long_open_h8",
        )
    }

    witness_counts = {
        "A_only": _only_axis_witness_count(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_narrow", "none", "M_long_open_h8"),
            "A",
        ),
        "B_partner_only": _only_axis_witness_count(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_broad", "obligate_partner", "M_long_open_h8"),
            "B",
        ),
        "B_antagonist_only": _only_axis_witness_count(
            _world(worlds, "A_broad", "none", "M_long_open_h8"),
            _world(worlds, "A_broad", "antagonist_exclusion", "M_long_open_h8"),
            "B",
        ),
        "M_distance_only": _only_axis_witness_count(
            _world(worlds, "A_broad", "none", "M_long_closed_h2"),
            _world(worlds, "A_broad", "none", "M_short_closed_h2"),
            "M",
        ),
        "M_barrier_only": _only_axis_witness_count(
            _world(worlds, "A_broad", "none", "M_long_open_h2"),
            _world(worlds, "A_broad", "none", "M_long_closed_h2"),
            "M",
        ),
    }

    same_g_different_arrival_pairs = 0
    positive_superset_negative_witness_pairs = 0
    for i, left in enumerate(worlds):
        for right in worlds[i + 1 :]:
            if left.occupied_mask == right.occupied_mask:
                occupied_indices = [
                    idx for idx in range(len(left.node_ids))
                    if left.occupied_mask & (1 << idx)
                ]
                if any(
                    left.first_arrival_steps[idx] != right.first_arrival_steps[idx]
                    for idx in occupied_indices
                ):
                    same_g_different_arrival_pairs += 1
            if left.occupied_mask & ~right.occupied_mask == 0 and (
                right.occupied_mask & ~left.occupied_mask
            ):
                positive_superset_negative_witness_pairs += 1
            if right.occupied_mask & ~left.occupied_mask == 0 and (
                left.occupied_mask & ~right.occupied_mask
            ):
                positive_superset_negative_witness_pairs += 1

    failed: list[str] = []
    if not (0.2 <= partner_fraction <= 0.8):
        failed.append("partner_fraction")
    if not (0.2 <= antagonist_fraction <= 0.8):
        failed.append("antagonist_fraction")
    if not source_in_partner:
        failed.append("focal_source_in_partner")
    if not biotic_masks_pairwise_distinct:
        failed.append("biotic_masks_pairwise_distinct")
    for mode, count in counts_b.items():
        if count < 1:
            failed.append(f"eligible_B_{mode}")
    for label, count in counts_a.items():
        if count < 1:
            failed.append(f"eligible_{label}")
    for label, count in counts_m.items():
        if count < 1:
            failed.append(f"eligible_{label}")
    for key, count in witness_counts.items():
        if count < 1:
            failed.append(key)
    if same_g_different_arrival_pairs < 1:
        failed.append("same_G_different_arrival")
    if positive_superset_negative_witness_pairs < 1:
        failed.append("positive_superset_negative_witness")

    return BAMActivationAuditV22(
        passed=not failed,
        partner_fraction=partner_fraction,
        antagonist_fraction=antagonist_fraction,
        focal_source_in_partner=source_in_partner,
        biotic_masks_pairwise_distinct=biotic_masks_pairwise_distinct,
        eligible_truth_counts_by_B=tuple(sorted(counts_b.items())),
        eligible_truth_counts_by_A=tuple(sorted(counts_a.items())),
        eligible_truth_counts_by_M=tuple(sorted(counts_m.items())),
        witness_counts=tuple(sorted(witness_counts.items())),
        same_g_different_arrival_pairs=same_g_different_arrival_pairs,
        positive_superset_negative_witness_pairs=positive_superset_negative_witness_pairs,
        failed_gates=tuple(failed),
    )


def run_bam_v22() -> dict[str, object]:
    worlds = build_world_grid_v22()
    audit = activation_audit_v22(worlds)
    audit_payload = {
        "partner_fraction": audit.partner_fraction,
        "antagonist_fraction": audit.antagonist_fraction,
        "focal_source_in_partner": audit.focal_source_in_partner,
        "biotic_masks_pairwise_distinct": audit.biotic_masks_pairwise_distinct,
        "eligible_truth_counts_by_B": dict(audit.eligible_truth_counts_by_B),
        "eligible_truth_counts_by_A": dict(audit.eligible_truth_counts_by_A),
        "eligible_truth_counts_by_M": dict(audit.eligible_truth_counts_by_M),
        "witness_counts": dict(audit.witness_counts),
        "same_g_different_arrival_pairs": audit.same_g_different_arrival_pairs,
        "positive_superset_negative_witness_pairs": audit.positive_superset_negative_witness_pairs,
        "failed_gates": list(audit.failed_gates),
    }
    if not audit.passed:
        return {
            "schema": "eog.known_truth_bam.source_compatible_result.v2_2",
            "status": "ACTIVATION_STOP",
            "activation_audit": audit_payload,
        }

    landscape = make_bam_v21_landscape()
    eligible = [
        world for world in worlds
        if len(world.occupied_ids) >= 2 and "r1c0" in world.occupied_ids
    ]
    truth_retention_failures = 0
    axis_mismatches = 0
    equivalence_violations = 0
    superset_violations = 0
    negative_failures = 0
    temporal_failures = 0
    positive_unique = 0
    negative_unique = 0
    temporal_unique = 0
    negative_rescuable = 0
    negative_rescued = 0
    temporal_rescuable = 0
    temporal_rescued = 0
    h7_cases = 0
    h7_no_b_survived = 0
    h8_cases = 0
    h8_no_b_eliminated = 0
    antagonist_dependency_cases = 0
    antagonist_no_b_survived = 0
    antagonist_negative_rescued = 0
    cases: list[dict[str, object]] = []

    for truth in eligible:
        positives = truth.occupied_ids
        positive_result = compatible_positive_only(worlds, positives)
        if truth.world_id not in positive_result.compatible_world_ids:
            truth_retention_failures += 1
        if positive_result.compatible_world_ids == (truth.world_id,):
            positive_unique += 1

        exact_g = tuple(
            world.world_id for world in worlds
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
                axis_mismatches += 1
            if truth.occupied_mask & ~false_world.occupied_mask == 0 and eliminated:
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
                    negative_failures += 1

        temporal_obs = {
            node_id: int(truth.first_arrival_steps[idx])
            for idx, node_id in enumerate(truth.node_ids)
            if node_id in set(positives) and truth.first_arrival_steps[idx] is not None
        }
        temporal_result = compatible_with_temporal_arrivals(
            worlds, positives, negatives, temporal_obs
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
                    temporal_failures += 1

        if truth.biotic_mode == "obligate_partner":
            no_b = _world(worlds, truth.abiotic_label, "none", truth.movement_label)
            extra = no_b.occupied_mask & ~truth.occupied_mask
            if extra:
                h7_cases += 1
                if no_b.world_id in positive_result.compatible_world_ids:
                    h7_no_b_survived += 1
                h8_cases += 1
                if no_b.world_id not in negative_result.compatible_world_ids:
                    h8_no_b_eliminated += 1

        if truth.biotic_mode == "antagonist_exclusion":
            no_b = _world(worlds, truth.abiotic_label, "none", truth.movement_label)
            extra = no_b.occupied_mask & ~truth.occupied_mask
            if extra:
                antagonist_dependency_cases += 1
                if no_b.world_id in positive_result.compatible_world_ids:
                    antagonist_no_b_survived += 1
                if no_b.world_id not in negative_result.compatible_world_ids:
                    antagonist_negative_rescued += 1

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
        "BAM_H2_axis_witness_attribution": "SUPPORTED" if axis_mismatches == 0 else "REFUTED",
        "BAM_H3_intersection_nonidentifiability": "SUPPORTED" if equivalence_violations == 0 else "REFUTED",
        "BAM_H4_positive_superset_ceiling": "SUPPORTED" if superset_violations == 0 else "REFUTED",
        "BAM_H5_perfect_negative_rescue": (
            "SUPPORTED" if negative_rescuable > 0 and negative_failures == 0 else "REFUTED"
        ),
        "BAM_H6_temporal_M_rescue": (
            "SUPPORTED" if temporal_rescuable > 0 and temporal_failures == 0 else "REFUTED"
        ),
        "BAM_H7_positive_partner_dependence_nonidentifiability": (
            "SUPPORTED" if h7_cases > 0 and h7_no_b_survived == h7_cases else "REFUTED"
        ),
        "BAM_H8_perfect_negative_partner_rescue": (
            "SUPPORTED" if h8_cases > 0 and h8_no_b_eliminated == h8_cases else "REFUTED"
        ),
    }

    return {
        "schema": "eog.known_truth_bam.source_compatible_result.v2_2",
        "status": "SCORED",
        "activation_audit": audit_payload,
        "candidate_world_count": len(worlds),
        "eligible_truth_worlds": len(eligible),
        "truth_retention_failures": truth_retention_failures,
        "axis_witness_mismatches": axis_mismatches,
        "equivalence_violations": equivalence_violations,
        "positive_superset_violations": superset_violations,
        "negative_rescue_failures": negative_failures,
        "temporal_rescue_failures": temporal_failures,
        "fraction_truth_unique_positive_only": positive_unique / len(eligible),
        "fraction_truth_unique_with_negatives": negative_unique / len(eligible),
        "fraction_truth_unique_with_temporal_evidence": temporal_unique / len(eligible),
        "negative_rescue_fraction": negative_rescued / negative_rescuable,
        "temporal_M_rescue_fraction": temporal_rescued / temporal_rescuable,
        "partner_dependency_diagnostic_cases": h7_cases,
        "partner_no_B_survives_positive": h7_no_b_survived,
        "partner_no_B_eliminated_by_negatives": h8_no_b_eliminated,
        "antagonist_dependency_diagnostic_cases": antagonist_dependency_cases,
        "antagonist_no_B_survives_positive": antagonist_no_b_survived,
        "antagonist_no_B_eliminated_by_negatives": antagonist_negative_rescued,
        "verdicts": verdicts,
        "cases": cases,
    }
