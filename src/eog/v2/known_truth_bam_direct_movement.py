"""Direct movement evidence for the frozen BAM v2.1 universe.

v2.2 showed that complete G, perfect negatives, occupied-node movement timing, and
direct A/B observations still left many BAM states unresolved.  This module adds
independent source-conditioned M observations:

E5: complete M accessibility set.
E6: complete M first-arrival state.

The primary endpoint remains exact finite-landscape BAM-state identity, not exact
parameter-label identity.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Sequence

from .known_truth_bam import (
    BAMWorld,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
)
from .known_truth_bam_direct_evidence import (
    _filter_direct_axis,
    bam_state_key,
    group_worlds_by_bam_state,
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


def _world_by_id(worlds: Sequence[BAMWorld]) -> dict[str, BAMWorld]:
    return {world.world_id: world for world in worlds}


def _state_keys(
    worlds_by_id: dict[str, BAMWorld],
    ids: Sequence[str],
) -> set[tuple[object, ...]]:
    return {bam_state_key(worlds_by_id[world_id]) for world_id in ids}


def _filter_M_accessibility(
    candidate_ids: Sequence[str],
    worlds_by_id: dict[str, BAMWorld],
    truth: BAMWorld,
    measured_node_ids: Sequence[str] | None = None,
) -> tuple[str, ...]:
    node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
    nodes = tuple(truth.node_ids if measured_node_ids is None else measured_node_ids)
    compatible: list[str] = []
    for world_id in candidate_ids:
        world = worlds_by_id[world_id]
        ok = True
        for node_id in nodes:
            idx = node_index[node_id]
            bit = 1 << idx
            if bool(truth.movement_mask & bit) != bool(world.movement_mask & bit):
                ok = False
                break
        if ok:
            compatible.append(world_id)
    return tuple(compatible)


def _filter_M_arrival(
    candidate_ids: Sequence[str],
    worlds_by_id: dict[str, BAMWorld],
    truth: BAMWorld,
    measured_node_ids: Sequence[str] | None = None,
) -> tuple[str, ...]:
    node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
    nodes = tuple(truth.node_ids if measured_node_ids is None else measured_node_ids)
    compatible: list[str] = []
    for world_id in candidate_ids:
        world = worlds_by_id[world_id]
        if all(
            world.first_arrival_steps[node_index[node_id]]
            == truth.first_arrival_steps[node_index[node_id]]
            for node_id in nodes
        ):
            compatible.append(world_id)
    return tuple(compatible)


def _greedy_nodes(
    candidate_ids: Sequence[str],
    target_ids: Sequence[str],
    worlds_by_id: dict[str, BAMWorld],
    truth: BAMWorld,
    filter_fn,
) -> tuple[str, ...]:
    current = tuple(candidate_ids)
    target = tuple(target_ids)
    target_set = set(target)
    if set(current) == target_set:
        return ()

    chosen: list[str] = []
    while set(current) != target_set:
        best_node = None
        best_remaining = None
        best_eliminated = -1
        for node_id in truth.node_ids:
            if node_id in chosen:
                continue
            remaining = filter_fn(
                current,
                worlds_by_id,
                truth,
                measured_node_ids=(node_id,),
            )
            if not target_set.issubset(remaining):
                raise RuntimeError("targeted M observation contradicted full-M target")
            eliminated = len(current) - len(remaining)
            if (
                eliminated > best_eliminated
                or (
                    eliminated == best_eliminated
                    and best_node is not None
                    and node_id < best_node
                )
            ):
                best_node = node_id
                best_remaining = remaining
                best_eliminated = eliminated
        if best_node is None or best_remaining is None or best_eliminated <= 0:
            raise RuntimeError("no M diagnostic node can reproduce full-M contraction")
        chosen.append(best_node)
        current = best_remaining
    return tuple(chosen)


def _fraction(values: Sequence[bool]) -> float:
    return 0.0 if not values else sum(bool(v) for v in values) / len(values)


def run_direct_movement_v23() -> dict[str, object]:
    system = build_v21_system()
    worlds = system.worlds
    worlds_by_id = _world_by_id(worlds)
    state_groups = group_worlds_by_bam_state(worlds)

    eligible = 0
    h1_access_failures = 0
    h2_arrival_failures = 0
    h3_state_recovery_failures = 0
    h4_alias_split_violations = 0
    h5_target_failures = 0

    unique_E4: list[bool] = []
    unique_E5: list[bool] = []
    unique_E6: list[bool] = []
    parameter_unique_E6: list[bool] = []

    access_counts: list[int] = []
    arrival_counts: list[int] = []
    total_counts: list[int] = []
    access_node_frequency: Counter[str] = Counter()
    arrival_node_frequency: Counter[str] = Counter()
    residual_after_E6 = 0
    rows: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible += 1
        truth_state = bam_state_key(truth)
        truth_alias_ids = set(state_groups[truth_state])

        E0 = compatible_positive_only(worlds, positives).compatible_world_ids
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
        expected_E5 = tuple(
            world_id
            for world_id in E4
            if worlds_by_id[world_id].movement_mask == truth.movement_mask
        )
        if E5 != expected_E5:
            h1_access_failures += 1

        E6 = _filter_M_arrival(E5, worlds_by_id, truth)
        expected_E6 = tuple(
            world_id
            for world_id in E5
            if worlds_by_id[world_id].first_arrival_steps == truth.first_arrival_steps
        )
        if E6 != expected_E6:
            h2_arrival_failures += 1

        final_states = _state_keys(worlds_by_id, E6)
        if final_states != {truth_state}:
            h3_state_recovery_failures += 1
            residual_after_E6 += 1

        present_aliases = truth_alias_ids.intersection(E6)
        if present_aliases != truth_alias_ids:
            h4_alias_split_violations += 1

        access_nodes = _greedy_nodes(
            E4,
            E5,
            worlds_by_id,
            truth,
            _filter_M_accessibility,
        )
        targeted_E5 = _filter_M_accessibility(
            E4,
            worlds_by_id,
            truth,
            measured_node_ids=access_nodes,
        )
        if targeted_E5 != E5:
            h5_target_failures += 1

        arrival_nodes = _greedy_nodes(
            E5,
            E6,
            worlds_by_id,
            truth,
            _filter_M_arrival,
        )
        targeted_E6 = _filter_M_arrival(
            E5,
            worlds_by_id,
            truth,
            measured_node_ids=arrival_nodes,
        )
        if targeted_E6 != E6:
            h5_target_failures += 1

        for node_id in access_nodes:
            access_node_frequency[node_id] += 1
        for node_id in arrival_nodes:
            arrival_node_frequency[node_id] += 1

        def state_unique(ids: Sequence[str]) -> bool:
            return _state_keys(worlds_by_id, ids) == {truth_state}

        unique_E4.append(state_unique(E4))
        unique_E5.append(state_unique(E5))
        unique_E6.append(state_unique(E6))
        parameter_unique_E6.append(E6 == (truth.world_id,))
        access_counts.append(len(access_nodes))
        arrival_counts.append(len(arrival_nodes))
        total_counts.append(len(access_nodes) + len(arrival_nodes))

        rows.append(
            {
                "truth_world_id": truth.world_id,
                "truth_bam_state_alias_count": len(truth_alias_ids),
                "compatible_E4": len(E4),
                "compatible_E5": len(E5),
                "compatible_E6": len(E6),
                "bam_state_unique_E4": unique_E4[-1],
                "bam_state_unique_E5": unique_E5[-1],
                "bam_state_unique_E6": unique_E6[-1],
                "parameter_unique_E6": parameter_unique_E6[-1],
                "targeted_M_accessibility_nodes": list(access_nodes),
                "targeted_M_arrival_nodes": list(arrival_nodes),
            }
        )

    verdicts = {
        "DM_H1_M_accessibility_contraction": (
            "SUPPORTED" if h1_access_failures == 0 else "REFUTED"
        ),
        "DM_H2_M_arrival_contraction": (
            "SUPPORTED" if h2_arrival_failures == 0 else "REFUTED"
        ),
        "DM_H3_complete_BAM_state_recovery": (
            "SUPPORTED" if h3_state_recovery_failures == 0 else "REFUTED"
        ),
        "DM_H4_parameter_alias_honesty": (
            "SUPPORTED" if h4_alias_split_violations == 0 else "REFUTED"
        ),
        "DM_H5_targeted_M_efficiency": (
            "SUPPORTED" if h5_target_failures == 0 else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_direct_movement.result.v2_3",
        "candidate_world_count": len(worlds),
        "eligible_truth_worlds": eligible,
        "exact_bam_state_count": len(state_groups),
        "M_accessibility_failures": h1_access_failures,
        "M_arrival_failures": h2_arrival_failures,
        "complete_BAM_state_recovery_failures": h3_state_recovery_failures,
        "parameter_alias_split_violations": h4_alias_split_violations,
        "targeted_M_reproduction_failures": h5_target_failures,
        "bam_state_unique_fraction_E4": _fraction(unique_E4),
        "bam_state_unique_fraction_E5": _fraction(unique_E5),
        "bam_state_unique_fraction_E6": _fraction(unique_E6),
        "parameter_unique_fraction_E6": _fraction(parameter_unique_E6),
        "residual_nonidentifiable_cases_after_E6": residual_after_E6,
        "minimal_direct_M_accessibility_measurements_distribution": {
            str(k): int(v) for k, v in sorted(Counter(access_counts).items())
        },
        "minimal_direct_M_arrival_measurements_distribution": {
            str(k): int(v) for k, v in sorted(Counter(arrival_counts).items())
        },
        "minimal_total_M_measurements_distribution": {
            str(k): int(v) for k, v in sorted(Counter(total_counts).items())
        },
        "diagnostic_M_accessibility_node_frequency": dict(
            sorted(access_node_frequency.items())
        ),
        "diagnostic_M_arrival_node_frequency": dict(
            sorted(arrival_node_frequency.items())
        ),
        "verdicts": verdicts,
        "cases": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result
