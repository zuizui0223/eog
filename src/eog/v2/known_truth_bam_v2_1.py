"""Orthogonally activated known-truth BAM simulation v2.1.

This successor does not alter the frozen BAM v2 result.  It implements the v2.1
protocol whose first requirement is an outcome-free structural activation audit.
No H1-H6 scoring is permitted unless every A/B/M activation gate passes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

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
from .known_truth_biogeography import VirtualLandscape, make_gradient_landscape


BMode = Literal[
    "none",
    "obligate_partner",
    "antagonist_exclusion",
    "partner_and_antagonist",
]


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bit_count(value: int) -> int:
    return int(value.bit_count())


def _is_subset(left: int, right: int) -> bool:
    return left & ~right == 0


@dataclass(frozen=True)
class V21Axes:
    world_id: str
    abiotic_label: str
    biotic_mode: BMode
    step_radius: float
    barrier_permeable: bool
    horizon: int


@dataclass(frozen=True)
class V21System:
    landscape: VirtualLandscape
    biotic_state: AuxiliaryBioticState
    worlds: tuple[BAMWorld, ...]
    axes: tuple[V21Axes, ...]
    fingerprint: str

    @property
    def axes_by_world(self) -> dict[str, V21Axes]:
        return {row.world_id: row for row in self.axes}


@dataclass(frozen=True)
class ActivationGateReceipt:
    status: Literal["PASS", "DESIGN_STOP"]
    partner_fraction: float
    antagonist_fraction: float
    A_only_pairs: int
    partner_B_only_pairs: int
    antagonist_B_only_pairs: int
    M_distance_only_pairs: int
    M_barrier_only_pairs: int
    same_G_different_arrival_pairs: int
    positive_superset_negative_witness_pairs: int
    failed_gates: tuple[str, ...]
    fingerprint: str


def make_v21_landscape() -> VirtualLandscape:
    return make_gradient_landscape(
        width=7,
        height=3,
        spike_col=3,
        spike_amount=0.45,
        barrier_col=4,
        barrier_gap_rows=(),
    )


def make_v21_biotic_state(landscape: VirtualLandscape) -> AuxiliaryBioticState:
    # Partner: expected partial occupancy over columns 0,1,2,4,5.
    partner_a = abiotic_mask(
        landscape,
        center=(0.42, 0.55),
        radius=(0.35, 0.20),
    )
    partner_m = movement_state(
        landscape,
        source_id="r1c0",
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    ).accessible_mask
    partner = partner_a & partner_m

    # Antagonist: expected partial occupancy over right-hand columns 4,5,6.
    antagonist_a = abiotic_mask(
        landscape,
        center=(0.62, 0.45),
        radius=(0.20, 0.15),
    )
    antagonist_m = movement_state(
        landscape,
        source_id="r1c6",
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    ).accessible_mask
    antagonist = antagonist_a & antagonist_m

    return AuxiliaryBioticState(
        partner_mask=partner,
        antagonist_mask=antagonist,
        fingerprint=_sha256(
            {
                "partner_mask": partner,
                "antagonist_mask": antagonist,
                "protocol": "known_truth_bam_v2_1",
            }
        ),
    )


def build_v21_system() -> V21System:
    landscape = make_v21_landscape()
    biotic = make_v21_biotic_state(landscape)

    a_specs = (
        ("A_narrow", (0.45, 0.52), (0.35, 0.20)),
        ("A_broad", (0.45, 0.52), (0.50, 0.30)),
    )
    b_modes: tuple[BMode, ...] = (
        "none",
        "obligate_partner",
        "antagonist_exclusion",
        "partner_and_antagonist",
    )

    worlds: list[BAMWorld] = []
    axes: list[V21Axes] = []
    for a_label, center, radius in a_specs:
        for b_mode in b_modes:
            for step_radius in (1.01, 2.01):
                for barrier_permeable in (False, True):
                    for horizon in (3, 8):
                        m_label = (
                            f"D{step_radius:.2f}_"
                            f"P{int(barrier_permeable)}_"
                            f"H{horizon}"
                        )
                        world_id = f"{a_label}|B_{b_mode}|M_{m_label}"
                        world = build_bam_world(
                            landscape,
                            world_id=world_id,
                            abiotic_label=a_label,
                            niche_center=center,
                            niche_radius=radius,
                            biotic_state=biotic,
                            biotic_mode=b_mode,
                            movement_label=m_label,
                            source_id="r1c0",
                            step_radius=step_radius,
                            barrier_permeable=barrier_permeable,
                            horizon=horizon,
                        )
                        worlds.append(world)
                        axes.append(
                            V21Axes(
                                world_id=world_id,
                                abiotic_label=a_label,
                                biotic_mode=b_mode,
                                step_radius=step_radius,
                                barrier_permeable=barrier_permeable,
                                horizon=horizon,
                            )
                        )

    ordered_worlds = tuple(sorted(worlds, key=lambda row: row.world_id))
    ordered_axes = tuple(sorted(axes, key=lambda row: row.world_id))
    payload = {
        "landscape_fingerprint": landscape.fingerprint,
        "biotic_fingerprint": biotic.fingerprint,
        "world_fingerprints": [
            (world.world_id, world.fingerprint) for world in ordered_worlds
        ],
        "axes": [
            {
                "world_id": row.world_id,
                "A": row.abiotic_label,
                "B": row.biotic_mode,
                "D": row.step_radius,
                "P": row.barrier_permeable,
                "H": row.horizon,
            }
            for row in ordered_axes
        ],
    }
    return V21System(
        landscape=landscape,
        biotic_state=biotic,
        worlds=ordered_worlds,
        axes=ordered_axes,
        fingerprint=_sha256(payload),
    )


def _same_except_A(left: V21Axes, right: V21Axes) -> bool:
    return (
        left.biotic_mode == right.biotic_mode
        and left.step_radius == right.step_radius
        and left.barrier_permeable == right.barrier_permeable
        and left.horizon == right.horizon
        and left.abiotic_label != right.abiotic_label
    )


def _same_except_B(left: V21Axes, right: V21Axes) -> bool:
    return (
        left.abiotic_label == right.abiotic_label
        and left.step_radius == right.step_radius
        and left.barrier_permeable == right.barrier_permeable
        and left.horizon == right.horizon
        and left.biotic_mode != right.biotic_mode
    )


def _same_except_distance(left: V21Axes, right: V21Axes) -> bool:
    return (
        left.abiotic_label == right.abiotic_label
        and left.biotic_mode == right.biotic_mode
        and left.barrier_permeable == right.barrier_permeable
        and left.horizon == right.horizon
        and left.step_radius != right.step_radius
    )


def _same_except_barrier(left: V21Axes, right: V21Axes) -> bool:
    return (
        left.abiotic_label == right.abiotic_label
        and left.biotic_mode == right.biotic_mode
        and left.step_radius == right.step_radius
        and left.horizon == right.horizon
        and left.barrier_permeable != right.barrier_permeable
    )


def audit_v21_activation(system: V21System) -> ActivationGateReceipt:
    worlds = system.worlds
    axes_by_world = system.axes_by_world
    n_nodes = len(system.landscape.node_ids)

    partner_fraction = _bit_count(system.biotic_state.partner_mask) / n_nodes
    antagonist_fraction = _bit_count(system.biotic_state.antagonist_mask) / n_nodes

    A_only_pairs = 0
    partner_B_only_pairs = 0
    antagonist_B_only_pairs = 0
    M_distance_only_pairs = 0
    M_barrier_only_pairs = 0
    same_G_different_arrival_pairs = 0
    positive_superset_negative_witness_pairs = 0

    for truth in worlds:
        truth_axes = axes_by_world[truth.world_id]
        if len(truth.occupied_ids) < 2 or "r1c0" not in truth.occupied_ids:
            continue

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            false_axes = axes_by_world[false_world.world_id]
            witness = axis_witnesses(truth, false_world)
            has_A = bool(witness["A"])
            has_B = bool(witness["B"])
            has_M = bool(witness["M"])

            if _same_except_A(truth_axes, false_axes) and has_A and not has_B and not has_M:
                A_only_pairs += 1

            if _same_except_B(truth_axes, false_axes) and has_B and not has_A and not has_M:
                modes = {truth_axes.biotic_mode, false_axes.biotic_mode}
                if modes == {"none", "obligate_partner"}:
                    partner_B_only_pairs += 1
                if modes == {"none", "antagonist_exclusion"}:
                    antagonist_B_only_pairs += 1

            if (
                _same_except_distance(truth_axes, false_axes)
                and has_M and not has_A and not has_B
            ):
                M_distance_only_pairs += 1

            if (
                _same_except_barrier(truth_axes, false_axes)
                and has_M and not has_A and not has_B
            ):
                M_barrier_only_pairs += 1

            if truth.occupied_mask == false_world.occupied_mask:
                differs = any(
                    left != right
                    for left, right, node_id in zip(
                        truth.first_arrival_steps,
                        false_world.first_arrival_steps,
                        truth.node_ids,
                        strict=True,
                    )
                    if node_id in set(truth.occupied_ids)
                )
                if differs:
                    same_G_different_arrival_pairs += 1

            if _is_subset(truth.occupied_mask, false_world.occupied_mask):
                extra = false_world.occupied_mask & ~truth.occupied_mask
                if extra:
                    positive_superset_negative_witness_pairs += 1

    failed: list[str] = []
    if not 0.20 < partner_fraction < 0.80:
        failed.append("partner_fraction")
    if not 0.20 < antagonist_fraction < 0.80:
        failed.append("antagonist_fraction")
    if A_only_pairs < 1:
        failed.append("A_only")
    if partner_B_only_pairs < 1:
        failed.append("partner_B_only")
    if antagonist_B_only_pairs < 1:
        failed.append("antagonist_B_only")
    if M_distance_only_pairs < 1:
        failed.append("M_distance_only")
    if M_barrier_only_pairs < 1:
        failed.append("M_barrier_only")
    if same_G_different_arrival_pairs < 1:
        failed.append("same_G_different_arrival")
    if positive_superset_negative_witness_pairs < 1:
        failed.append("positive_superset_negative_witness")

    payload = {
        "partner_fraction": partner_fraction,
        "antagonist_fraction": antagonist_fraction,
        "A_only_pairs": A_only_pairs,
        "partner_B_only_pairs": partner_B_only_pairs,
        "antagonist_B_only_pairs": antagonist_B_only_pairs,
        "M_distance_only_pairs": M_distance_only_pairs,
        "M_barrier_only_pairs": M_barrier_only_pairs,
        "same_G_different_arrival_pairs": same_G_different_arrival_pairs,
        "positive_superset_negative_witness_pairs": positive_superset_negative_witness_pairs,
        "failed_gates": failed,
    }
    return ActivationGateReceipt(
        status="PASS" if not failed else "DESIGN_STOP",
        partner_fraction=partner_fraction,
        antagonist_fraction=antagonist_fraction,
        A_only_pairs=A_only_pairs,
        partner_B_only_pairs=partner_B_only_pairs,
        antagonist_B_only_pairs=antagonist_B_only_pairs,
        M_distance_only_pairs=M_distance_only_pairs,
        M_barrier_only_pairs=M_barrier_only_pairs,
        same_G_different_arrival_pairs=same_G_different_arrival_pairs,
        positive_superset_negative_witness_pairs=positive_superset_negative_witness_pairs,
        failed_gates=tuple(failed),
        fingerprint=_sha256(payload),
    )


def run_bam_v21() -> dict[str, object]:
    system = build_v21_system()
    activation = audit_v21_activation(system)
    activation_payload = {
        "status": activation.status,
        "partner_fraction": activation.partner_fraction,
        "antagonist_fraction": activation.antagonist_fraction,
        "A_only_pairs": activation.A_only_pairs,
        "partner_B_only_pairs": activation.partner_B_only_pairs,
        "antagonist_B_only_pairs": activation.antagonist_B_only_pairs,
        "M_distance_only_pairs": activation.M_distance_only_pairs,
        "M_barrier_only_pairs": activation.M_barrier_only_pairs,
        "same_G_different_arrival_pairs": activation.same_G_different_arrival_pairs,
        "positive_superset_negative_witness_pairs": (
            activation.positive_superset_negative_witness_pairs
        ),
        "failed_gates": list(activation.failed_gates),
        "fingerprint": activation.fingerprint,
    }
    if activation.status != "PASS":
        result = {
            "schema": "eog.known_truth_bam_orthogonal.result.v2_1",
            "status": "DESIGN_STOP",
            "system_fingerprint": system.fingerprint,
            "activation": activation_payload,
            "scoring_performed": False,
        }
        result["fingerprint"] = _sha256(result)
        return result

    worlds = system.worlds
    axes_by_world = system.axes_by_world
    eligible = 0
    truth_retention_failures = 0
    h2_axis_mismatches = 0
    h3_equivalence_violations = 0
    h4_superset_violations = 0
    h5_negative_rescue_failures = 0
    h6_temporal_rescue_failures = 0
    positive_unique = 0
    negative_unique = 0
    temporal_unique = 0
    negative_rescuable = 0
    negative_rescued = 0
    temporal_rescuable = 0
    temporal_rescued = 0
    axis_counts = {
        "A_only": 0,
        "B_only": 0,
        "M_only": 0,
        "AB": 0,
        "AM": 0,
        "BM": 0,
        "ABM": 0,
        "none": 0,
    }
    g_equivalence_sizes: list[int] = []
    rows: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible += 1
        positives_set = set(positives)

        positive = compatible_positive_only(worlds, positives)
        if truth.world_id not in positive.compatible_world_ids:
            truth_retention_failures += 1
        if positive.compatible_world_ids == (truth.world_id,):
            positive_unique += 1

        equivalent = tuple(
            world for world in worlds
            if world.occupied_mask == truth.occupied_mask
        )
        g_equivalence_sizes.append(len(equivalent))
        if not {world.world_id for world in equivalent}.issubset(
            positive.compatible_world_ids
        ):
            h3_equivalence_violations += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            witness = axis_witnesses(truth, false_world)
            axes = tuple(axis for axis in ("A", "B", "M") if witness[axis])
            label = "".join(axes) if axes else "none"
            key = {
                "A": "A_only",
                "B": "B_only",
                "M": "M_only",
                "AB": "AB",
                "AM": "AM",
                "BM": "BM",
                "ABM": "ABM",
                "": "none",
            }[label]
            axis_counts[key] += 1
            eliminated = false_world.world_id not in positive.compatible_world_ids
            if eliminated != bool(axes):
                h2_axis_mismatches += 1
            if _is_subset(truth.occupied_mask, false_world.occupied_mask) and eliminated:
                h4_superset_violations += 1

        negatives = tuple(
            node_id
            for node_id in system.landscape.node_ids
            if node_id not in positives_set
        )
        with_neg = compatible_with_perfect_negatives(worlds, positives, negatives)
        if with_neg.compatible_world_ids == (truth.world_id,):
            negative_unique += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            if not _is_subset(truth.occupied_mask, false_world.occupied_mask):
                continue
            extra = false_world.occupied_mask & ~truth.occupied_mask
            if extra:
                negative_rescuable += 1
                if false_world.world_id not in with_neg.compatible_world_ids:
                    negative_rescued += 1
                else:
                    h5_negative_rescue_failures += 1

        node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
        observed_arrival = {
            node_id: int(truth.first_arrival_steps[node_index[node_id]])
            for node_id in positives
            if truth.first_arrival_steps[node_index[node_id]] is not None
        }
        with_time = compatible_with_temporal_arrivals(
            worlds,
            positives,
            negatives,
            observed_arrival,
        )
        if with_time.compatible_world_ids == (truth.world_id,):
            temporal_unique += 1

        for false_world in equivalent:
            if false_world.world_id == truth.world_id:
                continue
            differs = any(
                false_world.first_arrival_steps[node_index[node_id]]
                != truth.first_arrival_steps[node_index[node_id]]
                for node_id in positives
            )
            if differs:
                temporal_rescuable += 1
                if false_world.world_id not in with_time.compatible_world_ids:
                    temporal_rescued += 1
                else:
                    h6_temporal_rescue_failures += 1

        truth_axes = axes_by_world[truth.world_id]
        rows.append(
            {
                "truth_world_id": truth.world_id,
                "A": truth_axes.abiotic_label,
                "B": truth_axes.biotic_mode,
                "D": truth_axes.step_radius,
                "P": truth_axes.barrier_permeable,
                "H": truth_axes.horizon,
                "G_count": len(positives),
                "G_equivalence_size": len(equivalent),
                "compatible_positive": len(positive.compatible_world_ids),
                "compatible_negative": len(with_neg.compatible_world_ids),
                "compatible_temporal": len(with_time.compatible_world_ids),
            }
        )

    verdicts = {
        "BAM_H1_truth_retention": (
            "SUPPORTED" if truth_retention_failures == 0 else "REFUTED"
        ),
        "BAM_H2_axis_witness_attribution": (
            "SUPPORTED" if h2_axis_mismatches == 0 else "REFUTED"
        ),
        "BAM_H3_intersection_nonidentifiability": (
            "SUPPORTED" if h3_equivalence_violations == 0 else "REFUTED"
        ),
        "BAM_H4_positive_superset_ceiling": (
            "SUPPORTED" if h4_superset_violations == 0 else "REFUTED"
        ),
        "BAM_H5_perfect_negative_rescue": (
            "SUPPORTED"
            if negative_rescuable > 0 and h5_negative_rescue_failures == 0
            else "NOT_TESTED" if negative_rescuable == 0 else "REFUTED"
        ),
        "BAM_H6_temporal_M_rescue": (
            "SUPPORTED"
            if temporal_rescuable > 0 and h6_temporal_rescue_failures == 0
            else "NOT_TESTED" if temporal_rescuable == 0 else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_orthogonal.result.v2_1",
        "status": "SCORED",
        "system_fingerprint": system.fingerprint,
        "activation": activation_payload,
        "scoring_performed": True,
        "candidate_world_count": len(worlds),
        "eligible_truth_worlds": eligible,
        "truth_retention_failures": truth_retention_failures,
        "axis_witness_mismatches": h2_axis_mismatches,
        "equivalence_violations": h3_equivalence_violations,
        "positive_superset_violations": h4_superset_violations,
        "negative_rescue_failures": h5_negative_rescue_failures,
        "temporal_rescue_failures": h6_temporal_rescue_failures,
        "fraction_truth_unique_positive_only": (
            0.0 if eligible == 0 else positive_unique / eligible
        ),
        "fraction_truth_unique_with_negatives": (
            0.0 if eligible == 0 else negative_unique / eligible
        ),
        "fraction_truth_unique_with_temporal_evidence": (
            0.0 if eligible == 0 else temporal_unique / eligible
        ),
        "negative_rescue_opportunities": negative_rescuable,
        "negative_rescue_fraction": (
            0.0 if negative_rescuable == 0 else negative_rescued / negative_rescuable
        ),
        "temporal_rescue_opportunities": temporal_rescuable,
        "temporal_M_rescue_fraction": (
            0.0 if temporal_rescuable == 0 else temporal_rescued / temporal_rescuable
        ),
        "axis_witness_counts": axis_counts,
        "G_equivalence_class_sizes": g_equivalence_sizes,
        "verdicts": verdicts,
        "cases": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result
