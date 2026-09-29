"""Direct axis-specific evidence for the frozen orthogonal BAM v2.1 universe.

The v2.1 candidate universe is unchanged.  This module adds two idealised evidence
channels:

A evidence: direct abiotic viability state at selected nodes.
B evidence: direct biotic permissibility state at selected nodes.

The primary endpoint is BAM-state identification, not exact parameter-label recovery.
Worlds with identical A, B, M and movement-arrival state are treated as one exact
mechanistic equivalence class.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Callable, Sequence

from .known_truth_bam import (
    BAMWorld,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
)
from .known_truth_bam_v2_1 import build_v21_system


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bam_state_key(world: BAMWorld) -> tuple[object, ...]:
    """Exact finite-landscape BAM state, excluding parameter labels."""

    return (
        int(world.abiotic_mask),
        int(world.biotic_mask),
        int(world.movement_mask),
        tuple(world.first_arrival_steps),
    )


def group_worlds_by_bam_state(worlds: Sequence[BAMWorld]) -> dict[tuple[object, ...], tuple[str, ...]]:
    groups: dict[tuple[object, ...], list[str]] = {}
    for world in worlds:
        groups.setdefault(bam_state_key(world), []).append(world.world_id)
    return {
        key: tuple(sorted(ids))
        for key, ids in groups.items()
    }


def _world_by_id(worlds: Sequence[BAMWorld]) -> dict[str, BAMWorld]:
    return {world.world_id: world for world in worlds}


def _state_keys_for_ids(
    worlds_by_id: dict[str, BAMWorld],
    ids: Sequence[str],
) -> set[tuple[object, ...]]:
    return {bam_state_key(worlds_by_id[world_id]) for world_id in ids}


def _filter_direct_axis(
    candidate_ids: Sequence[str],
    worlds_by_id: dict[str, BAMWorld],
    truth: BAMWorld,
    *,
    axis: str,
    measured_node_ids: Sequence[str] | None = None,
) -> tuple[str, ...]:
    if axis not in {"A", "B"}:
        raise ValueError("axis must be A or B")
    node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
    nodes = tuple(truth.node_ids if measured_node_ids is None else measured_node_ids)
    missing = set(nodes).difference(node_index)
    if missing:
        raise ValueError(f"unknown measured nodes: {sorted(missing)}")

    truth_mask = truth.abiotic_mask if axis == "A" else truth.biotic_mask
    compatible: list[str] = []
    for world_id in candidate_ids:
        world = worlds_by_id[world_id]
        candidate_mask = world.abiotic_mask if axis == "A" else world.biotic_mask
        agrees = True
        for node_id in nodes:
            bit = 1 << node_index[node_id]
            if bool(truth_mask & bit) != bool(candidate_mask & bit):
                agrees = False
                break
        if agrees:
            compatible.append(world_id)
    return tuple(compatible)


def _greedy_diagnostic_nodes(
    candidate_ids: Sequence[str],
    worlds_by_id: dict[str, BAMWorld],
    truth: BAMWorld,
    *,
    axis: str,
    target_ids: Sequence[str],
) -> tuple[str, ...]:
    """Choose a deterministic small node set that reproduces the full-axis target set."""

    current = tuple(candidate_ids)
    target = tuple(target_ids)
    target_set = set(target)
    chosen: list[str] = []
    available = list(truth.node_ids)

    if set(current) == target_set:
        return ()

    while set(current) != target_set:
        best_node: str | None = None
        best_remaining: tuple[str, ...] | None = None
        best_eliminated = -1

        for node_id in available:
            if node_id in chosen:
                continue
            remaining = _filter_direct_axis(
                current,
                worlds_by_id,
                truth,
                axis=axis,
                measured_node_ids=(node_id,),
            )
            # A valid diagnostic node must never eliminate a full-axis-compatible world.
            if not target_set.issubset(remaining):
                raise RuntimeError("single-node evidence contradicted full-axis target")
            eliminated = len(current) - len(remaining)
            if eliminated > best_eliminated or (
                eliminated == best_eliminated
                and best_node is not None
                and node_id < best_node
            ):
                best_node = node_id
                best_remaining = remaining
                best_eliminated = eliminated

        if best_node is None or best_remaining is None or best_eliminated <= 0:
            raise RuntimeError("no direct-axis diagnostic node can reproduce full-axis contraction")
        chosen.append(best_node)
        current = best_remaining

    return tuple(chosen)


def _fraction(values: Sequence[bool]) -> float:
    return 0.0 if not values else sum(bool(v) for v in values) / len(values)


def run_direct_evidence_v22() -> dict[str, object]:
    system = build_v21_system()
    worlds = system.worlds
    worlds_by_id = _world_by_id(worlds)
    state_groups = group_worlds_by_bam_state(worlds)

    eligible_truths = 0
    h1_state_split_violations = 0
    h2_A_failures = 0
    h3_B_failures = 0
    h4_state_recovery_failures = 0
    h5_target_reproduction_failures = 0

    state_unique_E0: list[bool] = []
    state_unique_E1: list[bool] = []
    state_unique_E2: list[bool] = []
    state_unique_E3: list[bool] = []
    state_unique_E4: list[bool] = []
    parameter_unique_E4: list[bool] = []
    direct_A_counts: list[int] = []
    direct_B_counts: list[int] = []
    total_direct_counts: list[int] = []
    residual_nonidentifiable = 0
    case_rows: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible_truths += 1
        truth_state = bam_state_key(truth)
        truth_alias_ids = state_groups[truth_state]

        E0 = compatible_positive_only(worlds, positives).compatible_world_ids
        negatives = tuple(
            node_id for node_id in truth.node_ids if node_id not in set(positives)
        )
        E1 = compatible_with_perfect_negatives(worlds, positives, negatives).compatible_world_ids

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

        # H1: exact state aliases must remain together under E0-E2.
        for ids in (E0, E1, E2):
            present_aliases = set(truth_alias_ids).intersection(ids)
            if present_aliases and present_aliases != set(truth_alias_ids):
                h1_state_split_violations += 1

        E3 = _filter_direct_axis(E2, worlds_by_id, truth, axis="A")
        expected_E3 = tuple(
            world_id
            for world_id in E2
            if worlds_by_id[world_id].abiotic_mask == truth.abiotic_mask
        )
        if E3 != expected_E3:
            h2_A_failures += 1

        E4 = _filter_direct_axis(E3, worlds_by_id, truth, axis="B")
        expected_E4 = tuple(
            world_id
            for world_id in E3
            if worlds_by_id[world_id].biotic_mask == truth.biotic_mask
        )
        if E4 != expected_E4:
            h3_B_failures += 1

        final_states = _state_keys_for_ids(worlds_by_id, E4)
        if final_states != {truth_state}:
            h4_state_recovery_failures += 1
            residual_nonidentifiable += 1

        A_nodes = _greedy_diagnostic_nodes(
            E2,
            worlds_by_id,
            truth,
            axis="A",
            target_ids=E3,
        )
        targeted_E3 = _filter_direct_axis(
            E2,
            worlds_by_id,
            truth,
            axis="A",
            measured_node_ids=A_nodes,
        )
        if targeted_E3 != E3:
            h5_target_reproduction_failures += 1

        B_nodes = _greedy_diagnostic_nodes(
            E3,
            worlds_by_id,
            truth,
            axis="B",
            target_ids=E4,
        )
        targeted_E4 = _filter_direct_axis(
            E3,
            worlds_by_id,
            truth,
            axis="B",
            measured_node_ids=B_nodes,
        )
        if targeted_E4 != E4:
            h5_target_reproduction_failures += 1

        def state_unique(ids: Sequence[str]) -> bool:
            return _state_keys_for_ids(worlds_by_id, ids) == {truth_state}

        state_unique_E0.append(state_unique(E0))
        state_unique_E1.append(state_unique(E1))
        state_unique_E2.append(state_unique(E2))
        state_unique_E3.append(state_unique(E3))
        state_unique_E4.append(state_unique(E4))
        parameter_unique_E4.append(E4 == (truth.world_id,))
        direct_A_counts.append(len(A_nodes))
        direct_B_counts.append(len(B_nodes))
        total_direct_counts.append(len(A_nodes) + len(B_nodes))

        case_rows.append(
            {
                "truth_world_id": truth.world_id,
                "truth_bam_state_alias_count": len(truth_alias_ids),
                "compatible_E0": len(E0),
                "compatible_E1": len(E1),
                "compatible_E2": len(E2),
                "compatible_E3": len(E3),
                "compatible_E4": len(E4),
                "bam_state_unique_E0": state_unique_E0[-1],
                "bam_state_unique_E1": state_unique_E1[-1],
                "bam_state_unique_E2": state_unique_E2[-1],
                "bam_state_unique_E3": state_unique_E3[-1],
                "bam_state_unique_E4": state_unique_E4[-1],
                "parameter_unique_E4": parameter_unique_E4[-1],
                "targeted_A_nodes": list(A_nodes),
                "targeted_B_nodes": list(B_nodes),
                "targeted_A_count": len(A_nodes),
                "targeted_B_count": len(B_nodes),
            }
        )

    alias_distribution = Counter(len(ids) for ids in state_groups.values())
    A_count_dist = Counter(direct_A_counts)
    B_count_dist = Counter(direct_B_counts)
    total_count_dist = Counter(total_direct_counts)

    verdicts = {
        "DE_H1_state_equivalence_honesty": (
            "SUPPORTED" if h1_state_split_violations == 0 else "REFUTED"
        ),
        "DE_H2_direct_A_contraction": (
            "SUPPORTED" if h2_A_failures == 0 else "REFUTED"
        ),
        "DE_H3_direct_B_contraction": (
            "SUPPORTED" if h3_B_failures == 0 else "REFUTED"
        ),
        "DE_H4_complete_axis_state_recovery": (
            "SUPPORTED" if h4_state_recovery_failures == 0 else "REFUTED"
        ),
        "DE_H5_targeted_measurement_efficiency": (
            "SUPPORTED" if h5_target_reproduction_failures == 0 else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_direct_evidence.result.v2_2",
        "candidate_world_count": len(worlds),
        "eligible_truth_worlds": eligible_truths,
        "exact_bam_state_count": len(state_groups),
        "exact_parameter_alias_count": len(worlds) - len(state_groups),
        "bam_state_alias_class_size_distribution": {
            str(k): int(v) for k, v in sorted(alias_distribution.items())
        },
        "state_equivalence_split_violations": h1_state_split_violations,
        "direct_A_failures": h2_A_failures,
        "direct_B_failures": h3_B_failures,
        "complete_axis_state_recovery_failures": h4_state_recovery_failures,
        "targeted_measurement_reproduction_failures": h5_target_reproduction_failures,
        "bam_state_unique_fraction_E0": _fraction(state_unique_E0),
        "bam_state_unique_fraction_E1": _fraction(state_unique_E1),
        "bam_state_unique_fraction_E2": _fraction(state_unique_E2),
        "bam_state_unique_fraction_E3": _fraction(state_unique_E3),
        "bam_state_unique_fraction_E4": _fraction(state_unique_E4),
        "parameter_unique_fraction_E4": _fraction(parameter_unique_E4),
        "minimal_direct_A_measurements_distribution": {
            str(k): int(v) for k, v in sorted(A_count_dist.items())
        },
        "minimal_direct_B_measurements_distribution": {
            str(k): int(v) for k, v in sorted(B_count_dist.items())
        },
        "minimal_total_A_B_measurements_distribution": {
            str(k): int(v) for k, v in sorted(total_count_dist.items())
        },
        "residual_nonidentifiable_cases_after_E4": residual_nonidentifiable,
        "verdicts": verdicts,
        "cases": case_rows,
    }
    result["fingerprint"] = _sha256(result)
    return result
