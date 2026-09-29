"""Cross-landscape known-truth BAM generality benchmark v3.

This module tests whether the local v2.3 identifiability pattern generalises across a
finite, preregistered roster of heterogeneous virtual landscapes.  Systems are
generated deterministically from frozen seeds.  A system that fails a structural
activation gate is retained as DESIGN_STOP and is never repaired or replaced.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
import time
from typing import Literal, Sequence

import numpy as np

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
from .known_truth_bam_direct_evidence import (
    _filter_direct_axis,
    _greedy_diagnostic_nodes,
    bam_state_key,
    group_worlds_by_bam_state,
)
from .known_truth_bam_direct_movement import (
    _filter_M_accessibility,
    _filter_M_arrival,
    _greedy_nodes,
)
from .known_truth_biogeography import VirtualLandscape


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


def _is_subset(left: int, right: int) -> bool:
    return left & ~right == 0


def _fraction(values: Sequence[bool]) -> float:
    return 0.0 if not values else sum(bool(v) for v in values) / len(values)


@dataclass(frozen=True)
class SystemSpec:
    system_id: str
    seed: int
    width: int
    height: int
    gap: bool


@dataclass(frozen=True)
class GeneralitySystem:
    spec: SystemSpec
    landscape: VirtualLandscape
    biotic_state: AuxiliaryBioticState
    worlds: tuple[BAMWorld, ...]
    fingerprint: str


@dataclass(frozen=True)
class SystemActivation:
    status: Literal["PASS", "DESIGN_STOP"]
    partner_fraction: float
    antagonist_fraction: float
    A_only_pairs: int
    B_only_pairs: int
    M_only_pairs: int
    exact_G_equivalence_pairs: int
    positive_superset_negative_pairs: int
    failed_gates: tuple[str, ...]
    fingerprint: str


SYSTEM_SPECS: tuple[SystemSpec, ...] = (
    SystemSpec("S00_7x3_closed", 0, 7, 3, False),
    SystemSpec("S01_7x3_gap", 1, 7, 3, True),
    SystemSpec("S02_7x3_closed", 2, 7, 3, False),
    SystemSpec("S03_7x3_gap", 3, 7, 3, True),
    SystemSpec("S04_7x3_closed", 4, 7, 3, False),
    SystemSpec("S05_7x3_gap", 5, 7, 3, True),
    SystemSpec("S06_9x5_closed", 6, 9, 5, False),
    SystemSpec("S07_9x5_gap", 7, 9, 5, True),
    SystemSpec("S08_9x5_closed", 8, 9, 5, False),
    SystemSpec("S09_9x5_gap", 9, 9, 5, True),
    SystemSpec("S10_9x5_closed", 10, 9, 5, False),
    SystemSpec("S11_9x5_gap", 11, 9, 5, True),
)


def _build_landscape(spec: SystemSpec) -> VirtualLandscape:
    rng = np.random.default_rng(spec.seed)
    node_ids: list[str] = []
    coordinates: list[tuple[float, float]] = []
    environment: list[tuple[float, float]] = []

    for row in range(spec.height):
        yn = row / max(spec.height - 1, 1)
        for col in range(spec.width):
            xn = col / max(spec.width - 1, 1)
            node_ids.append(f"r{row}c{col}")
            coordinates.append((float(col), float(row)))

            local_t = float(rng.normal(0.0, 0.035))
            local_m = float(rng.normal(0.0, 0.035))
            temp = (
                0.18
                + 0.56 * xn
                + 0.08 * math.sin(2.0 * math.pi * (xn + 0.07 * spec.seed))
                + 0.04 * (yn - 0.5)
                + local_t
            )
            moisture = (
                0.38
                + 0.28 * yn
                + 0.07 * math.cos(math.pi * xn)
                + 0.03 * math.sin(2.0 * math.pi * yn + spec.seed)
                + local_m
            )
            environment.append((float(temp), float(moisture)))

    barrier_col = spec.width // 2
    gaps = (spec.height // 2,) if spec.gap else ()
    return VirtualLandscape(
        width=spec.width,
        height=spec.height,
        node_ids=tuple(node_ids),
        coordinates=tuple(coordinates),
        environment=tuple(environment),
        barrier_col=barrier_col,
        barrier_gap_rows=gaps,
    )


def _source_ids(landscape: VirtualLandscape) -> tuple[str, str]:
    mid = landscape.height // 2
    return (f"r{mid}c0", f"r{mid}c{landscape.width - 1}")


def _local_environment(
    landscape: VirtualLandscape,
    node_id: str,
) -> tuple[float, float]:
    idx = landscape.node_ids.index(node_id)
    return landscape.environment[idx]


def _make_biotic_state(landscape: VirtualLandscape) -> AuxiliaryBioticState:
    left_source, right_source = _source_ids(landscape)
    p_center = _local_environment(landscape, left_source)
    a_center = _local_environment(landscape, right_source)

    partner_a = abiotic_mask(
        landscape,
        center=(p_center[0] + 0.16, p_center[1]),
        radius=(0.34, 0.26),
    )
    partner_m = movement_state(
        landscape,
        source_id=left_source,
        step_radius=1.01,
        barrier_permeable=True,
        horizon=landscape.width + landscape.height,
    ).accessible_mask

    antagonist_a = abiotic_mask(
        landscape,
        center=(a_center[0] - 0.10, a_center[1]),
        radius=(0.28, 0.24),
    )
    antagonist_m = movement_state(
        landscape,
        source_id=right_source,
        step_radius=1.01,
        barrier_permeable=True,
        horizon=landscape.width + landscape.height,
    ).accessible_mask

    partner = partner_a & partner_m
    antagonist = antagonist_a & antagonist_m
    return AuxiliaryBioticState(
        partner_mask=partner,
        antagonist_mask=antagonist,
        fingerprint=_sha256(
            {
                "partner_mask": partner,
                "antagonist_mask": antagonist,
                "landscape": landscape.fingerprint,
            }
        ),
    )


def _build_worlds(
    landscape: VirtualLandscape,
    biotic_state: AuxiliaryBioticState,
) -> tuple[BAMWorld, ...]:
    left_source, _ = _source_ids(landscape)
    source_env = _local_environment(landscape, left_source)
    a_specs = (
        (
            "A_narrow",
            (source_env[0] + 0.22, source_env[1]),
            (0.36, 0.28),
        ),
        (
            "A_broad",
            (source_env[0] + 0.22, source_env[1]),
            (0.62, 0.46),
        ),
    )
    b_modes: tuple[BMode, ...] = (
        "none",
        "obligate_partner",
        "antagonist_exclusion",
        "partner_and_antagonist",
    )
    short_horizon = max(3, landscape.width // 3)
    long_horizon = landscape.width + landscape.height
    worlds: list[BAMWorld] = []

    for a_label, center, radius in a_specs:
        for b_mode in b_modes:
            for step_radius in (1.01, 2.01):
                for barrier_permeable in (False, True):
                    for horizon in (short_horizon, long_horizon):
                        m_label = (
                            f"D{step_radius:.2f}_"
                            f"P{int(barrier_permeable)}_"
                            f"H{horizon}"
                        )
                        world_id = f"{a_label}|B_{b_mode}|M_{m_label}"
                        worlds.append(
                            build_bam_world(
                                landscape,
                                world_id=world_id,
                                abiotic_label=a_label,
                                niche_center=center,
                                niche_radius=radius,
                                biotic_state=biotic_state,
                                biotic_mode=b_mode,
                                movement_label=m_label,
                                source_id=left_source,
                                step_radius=step_radius,
                                barrier_permeable=barrier_permeable,
                                horizon=horizon,
                            )
                        )
    return tuple(sorted(worlds, key=lambda world: world.world_id))


def build_generality_system(spec: SystemSpec) -> GeneralitySystem:
    landscape = _build_landscape(spec)
    biotic = _make_biotic_state(landscape)
    worlds = _build_worlds(landscape, biotic)
    payload = {
        "spec": {
            "system_id": spec.system_id,
            "seed": spec.seed,
            "width": spec.width,
            "height": spec.height,
            "gap": spec.gap,
        },
        "landscape_fingerprint": landscape.fingerprint,
        "biotic_fingerprint": biotic.fingerprint,
        "world_fingerprints": [
            (world.world_id, world.fingerprint) for world in worlds
        ],
    }
    return GeneralitySystem(
        spec=spec,
        landscape=landscape,
        biotic_state=biotic,
        worlds=worlds,
        fingerprint=_sha256(payload),
    )


def audit_system_activation(system: GeneralitySystem) -> SystemActivation:
    worlds = system.worlds
    n_nodes = len(system.landscape.node_ids)
    partner_fraction = system.biotic_state.partner_mask.bit_count() / n_nodes
    antagonist_fraction = system.biotic_state.antagonist_mask.bit_count() / n_nodes

    A_only = 0
    B_only = 0
    M_only = 0
    exact_G_pairs = 0
    superset_negative = 0

    eligible = [
        world
        for world in worlds
        if len(world.occupied_ids) >= 2
        and _source_ids(system.landscape)[0] in world.occupied_ids
    ]

    for truth in eligible:
        for candidate in worlds:
            if candidate.world_id == truth.world_id:
                continue
            witness = axis_witnesses(truth, candidate)
            axes = tuple(axis for axis in ("A", "B", "M") if witness[axis])
            if axes == ("A",):
                A_only += 1
            elif axes == ("B",):
                B_only += 1
            elif axes == ("M",):
                M_only += 1

            if candidate.occupied_mask == truth.occupied_mask:
                exact_G_pairs += 1

            if _is_subset(truth.occupied_mask, candidate.occupied_mask):
                if candidate.occupied_mask & ~truth.occupied_mask:
                    superset_negative += 1

    failed: list[str] = []
    if not 0.15 < partner_fraction < 0.85:
        failed.append("partner_fraction")
    if not 0.15 < antagonist_fraction < 0.85:
        failed.append("antagonist_fraction")
    if A_only < 1:
        failed.append("A_only")
    if B_only < 1:
        failed.append("B_only")
    if M_only < 1:
        failed.append("M_only")
    if exact_G_pairs < 1:
        failed.append("exact_G_equivalence")
    if superset_negative < 1:
        failed.append("positive_superset_negative")

    payload = {
        "system_id": system.spec.system_id,
        "partner_fraction": partner_fraction,
        "antagonist_fraction": antagonist_fraction,
        "A_only_pairs": A_only,
        "B_only_pairs": B_only,
        "M_only_pairs": M_only,
        "exact_G_equivalence_pairs": exact_G_pairs,
        "positive_superset_negative_pairs": superset_negative,
        "failed_gates": failed,
    }
    return SystemActivation(
        status="PASS" if not failed else "DESIGN_STOP",
        partner_fraction=partner_fraction,
        antagonist_fraction=antagonist_fraction,
        A_only_pairs=A_only,
        B_only_pairs=B_only,
        M_only_pairs=M_only,
        exact_G_equivalence_pairs=exact_G_pairs,
        positive_superset_negative_pairs=superset_negative,
        failed_gates=tuple(failed),
        fingerprint=_sha256(payload),
    )


def _state_keys(
    worlds_by_id: dict[str, BAMWorld],
    ids: Sequence[str],
) -> set[tuple[object, ...]]:
    return {bam_state_key(worlds_by_id[world_id]) for world_id in ids}


def _score_system(system: GeneralitySystem) -> dict[str, object]:
    worlds = system.worlds
    worlds_by_id = {world.world_id: world for world in worlds}
    state_groups = group_worlds_by_bam_state(worlds)
    source_id = _source_ids(system.landscape)[0]

    eligible = 0
    state_unique = {f"E{i}": [] for i in range(7)}
    targeted_AB_counts: list[int] = []
    targeted_M_access_counts: list[int] = []
    targeted_M_arrival_counts: list[int] = []
    exact_G_sizes: list[int] = []
    axis_counts: Counter[str] = Counter()

    correctness = {
        "truth_retention_failures": 0,
        "monotonicity_violations": 0,
        "E6_state_recovery_failures": 0,
        "targeted_reproduction_failures": 0,
    }

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or source_id not in positives:
            continue
        eligible += 1
        truth_state = bam_state_key(truth)

        E0 = compatible_positive_only(worlds, positives).compatible_world_ids
        if truth.world_id not in E0:
            correctness["truth_retention_failures"] += 1

        negatives = tuple(
            node_id for node_id in truth.node_ids if node_id not in set(positives)
        )
        E1 = compatible_with_perfect_negatives(
            worlds,
            positives,
            negatives,
        ).compatible_world_ids

        node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
        observed_arrival = {
            node_id: int(truth.first_arrival_steps[node_index[node_id]])
            for node_id in positives
            if truth.first_arrival_steps[node_index[node_id]] is not None
        }
        E2 = compatible_with_temporal_arrivals(
            worlds,
            positives,
            negatives,
            observed_arrival,
        ).compatible_world_ids
        E3 = _filter_direct_axis(E2, worlds_by_id, truth, axis="A")
        E4 = _filter_direct_axis(E3, worlds_by_id, truth, axis="B")
        E5 = _filter_M_accessibility(E4, worlds_by_id, truth)
        E6 = _filter_M_arrival(E5, worlds_by_id, truth)

        levels = (E0, E1, E2, E3, E4, E5, E6)

        def unique_state(ids: Sequence[str]) -> bool:
            return _state_keys(worlds_by_id, ids) == {truth_state}

        unique_seq = [unique_state(ids) for ids in levels]
        for i, flag in enumerate(unique_seq):
            state_unique[f"E{i}"].append(flag)
        if any(
            earlier and not later
            for earlier, later in zip(unique_seq, unique_seq[1:])
        ):
            correctness["monotonicity_violations"] += 1

        if not unique_seq[-1]:
            correctness["E6_state_recovery_failures"] += 1

        exact_G_sizes.append(
            sum(1 for world in worlds if world.occupied_mask == truth.occupied_mask)
        )

        for candidate in worlds:
            if candidate.world_id == truth.world_id:
                continue
            axes = tuple(
                axis
                for axis in ("A", "B", "M")
                if axis_witnesses(truth, candidate)[axis]
            )
            axis_counts["".join(axes) if axes else "none"] += 1

        A_nodes = _greedy_diagnostic_nodes(
            E2,
            worlds_by_id,
            truth,
            axis="A",
            target_ids=E3,
        )
        B_nodes = _greedy_diagnostic_nodes(
            E3,
            worlds_by_id,
            truth,
            axis="B",
            target_ids=E4,
        )
        targeted_AB_counts.append(len(A_nodes) + len(B_nodes))

        targeted_E3 = _filter_direct_axis(
            E2,
            worlds_by_id,
            truth,
            axis="A",
            measured_node_ids=A_nodes,
        )
        targeted_E4 = _filter_direct_axis(
            E3,
            worlds_by_id,
            truth,
            axis="B",
            measured_node_ids=B_nodes,
        )
        if targeted_E3 != E3 or targeted_E4 != E4:
            correctness["targeted_reproduction_failures"] += 1

        M_access_nodes = _greedy_nodes(
            E4,
            E5,
            worlds_by_id,
            truth,
            _filter_M_accessibility,
        )
        targeted_M_access_counts.append(len(M_access_nodes))
        if _filter_M_accessibility(
            E4,
            worlds_by_id,
            truth,
            measured_node_ids=M_access_nodes,
        ) != E5:
            correctness["targeted_reproduction_failures"] += 1

        M_arrival_nodes = _greedy_nodes(
            E5,
            E6,
            worlds_by_id,
            truth,
            _filter_M_arrival,
        )
        targeted_M_arrival_counts.append(len(M_arrival_nodes))
        if _filter_M_arrival(
            E5,
            worlds_by_id,
            truth,
            measured_node_ids=M_arrival_nodes,
        ) != E6:
            correctness["targeted_reproduction_failures"] += 1

    fractions = {
        level: _fraction(values)
        for level, values in state_unique.items()
    }
    return {
        "system_id": system.spec.system_id,
        "system_fingerprint": system.fingerprint,
        "eligible_truths": eligible,
        "exact_bam_state_count": len(state_groups),
        "state_unique_fraction": fractions,
        "exact_G_equivalence_size_distribution": {
            str(k): int(v) for k, v in sorted(Counter(exact_G_sizes).items())
        },
        "targeted_AB_node_count_distribution": {
            str(k): int(v) for k, v in sorted(Counter(targeted_AB_counts).items())
        },
        "targeted_M_access_node_count_distribution": {
            str(k): int(v)
            for k, v in sorted(Counter(targeted_M_access_counts).items())
        },
        "targeted_M_arrival_node_count_distribution": {
            str(k): int(v)
            for k, v in sorted(Counter(targeted_M_arrival_counts).items())
        },
        "max_targeted_AB_nodes": max(targeted_AB_counts, default=0),
        "max_targeted_M_access_nodes": max(targeted_M_access_counts, default=0),
        "max_targeted_M_arrival_nodes": max(targeted_M_arrival_counts, default=0),
        "axis_witness_counts": dict(sorted(axis_counts.items())),
        "correctness": correctness,
    }


def run_bam_generality_v3() -> dict[str, object]:
    started = time.perf_counter()
    roster: list[dict[str, object]] = []
    scored: list[dict[str, object]] = []

    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        activation = audit_system_activation(system)
        row = {
            "system_id": spec.system_id,
            "seed": spec.seed,
            "width": spec.width,
            "height": spec.height,
            "gap": spec.gap,
            "system_fingerprint": system.fingerprint,
            "activation_status": activation.status,
            "partner_fraction": activation.partner_fraction,
            "antagonist_fraction": activation.antagonist_fraction,
            "A_only_pairs": activation.A_only_pairs,
            "B_only_pairs": activation.B_only_pairs,
            "M_only_pairs": activation.M_only_pairs,
            "exact_G_equivalence_pairs": activation.exact_G_equivalence_pairs,
            "positive_superset_negative_pairs": (
                activation.positive_superset_negative_pairs
            ),
            "failed_gates": list(activation.failed_gates),
            "activation_fingerprint": activation.fingerprint,
        }
        roster.append(row)
        if activation.status == "PASS":
            scored.append(_score_system(system))

    eligible_truths = sum(int(row["eligible_truths"]) for row in scored)

    pooled_unique_counts = {f"E{i}": 0 for i in range(7)}
    for row in scored:
        n = int(row["eligible_truths"])
        fractions = row["state_unique_fraction"]
        for level in pooled_unique_counts:
            pooled_unique_counts[level] += round(float(fractions[level]) * n)
    pooled_fractions = {
        level: (
            0.0 if eligible_truths == 0 else count / eligible_truths
        )
        for level, count in pooled_unique_counts.items()
    }

    all_correct = all(
        all(int(value) == 0 for value in row["correctness"].values())
        for row in scored
    )
    G1 = bool(scored) and all(
        float(row["state_unique_fraction"]["E0"]) == 0.0
        for row in scored
    )
    G2 = bool(scored) and all(
        float(row["state_unique_fraction"]["E4"]) < 1.0
        and float(row["state_unique_fraction"]["E5"]) == 1.0
        for row in scored
    )
    G3 = bool(scored) and all(
        int(row["max_targeted_AB_nodes"]) <= 3
        for row in scored
    )
    G4 = bool(scored) and all(
        int(row["max_targeted_M_access_nodes"]) <= 2
        for row in scored
    )
    G5 = bool(scored) and all(
        int(row["correctness"]["E6_state_recovery_failures"]) == 0
        for row in scored
    )
    G6 = bool(scored) and all(
        int(row["correctness"]["monotonicity_violations"]) == 0
        for row in scored
    )

    runtime_seconds = time.perf_counter() - started
    verdicts = {
        "G1_positive_zero_bound": "SUPPORTED" if G1 else "REFUTED",
        "G2_M_final_bottleneck": "SUPPORTED" if G2 else "REFUTED",
        "G3_AB_three_node_bound": "SUPPORTED" if G3 else "REFUTED",
        "G4_M_two_node_bound": "SUPPORTED" if G4 else "REFUTED",
        "G5_complete_state_recovery": "SUPPORTED" if G5 else "REFUTED",
        "G6_monotone_evidence_ladder": "SUPPORTED" if G6 else "REFUTED",
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_generality.result.v3",
        "system_roster_size": len(SYSTEM_SPECS),
        "scored_system_count": len(scored),
        "design_stop_count": len(SYSTEM_SPECS) - len(scored),
        "eligible_truth_count": eligible_truths,
        "all_scored_correctness_checks_zero": all_correct,
        "pooled_bam_state_unique_fraction": pooled_fractions,
        "roster": roster,
        "scored_systems": scored,
        "verdicts": verdicts,
        "runtime_seconds": runtime_seconds,
    }
    fingerprint_payload = dict(result)
    fingerprint_payload["runtime_seconds"] = None
    result["fingerprint"] = _sha256(fingerprint_payload)
    return result
