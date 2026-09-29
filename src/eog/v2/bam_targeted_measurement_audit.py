"""Audit greedy BAM targeted measurements against exact finite hitting sets."""

from __future__ import annotations

from collections import Counter
import hashlib
import json

from .bam_identifiability_theory import (
    FiniteBAMState,
    exact_minimum_diagnostic_measurements,
    measurements_from_arrival_state,
    measurements_from_binary_state,
)
from .known_truth_bam import (
    BAMWorld,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
)
from .known_truth_bam_direct_evidence import (
    _filter_direct_axis,
    _greedy_diagnostic_nodes,
)
from .known_truth_bam_direct_movement import (
    _filter_M_accessibility,
    _filter_M_arrival,
    _greedy_nodes,
)
from .known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite(world: BAMWorld) -> FiniteBAMState:
    return FiniteBAMState(
        world_id=world.world_id,
        node_ids=world.node_ids,
        A=frozenset(world.abiotic_ids),
        B=frozenset(world.biotic_ids),
        M=frozenset(world.movement_ids),
        tau=tuple(world.first_arrival_steps),
        parameter_label=world.world_id,
    )


def _dist(values: list[int]) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted(Counter(values).items())}


def run_targeted_measurement_exact_audit() -> dict[str, object]:
    truth_cases = 0
    systems_scored = 0
    greedy_equal = {"A": 0, "B": 0, "M": 0, "tau": 0}
    greedy_suboptimal = {"A": 0, "B": 0, "M": 0, "tau": 0}
    exact_counts = {"A": [], "B": [], "AB_joint": [], "M": [], "tau": [], "M_tau_joint": []}
    greedy_counts = {"A": [], "B": [], "AB_total": [], "M": [], "tau": [], "M_tau_total": []}
    failures: list[dict[str, object]] = []

    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        activation = audit_system_activation(system)
        if activation.status != "PASS":
            continue
        systems_scored += 1
        worlds = system.worlds
        worlds_by_id = {world.world_id: world for world in worlds}
        finite_worlds = tuple(_finite(world) for world in worlds)
        finite_by_id = {world.world_id: world for world in finite_worlds}
        source_id = f"r{system.landscape.height // 2}c0"

        for truth in worlds:
            positives = truth.occupied_ids
            if len(positives) < 2 or source_id not in positives:
                continue
            truth_cases += 1
            ftruth = finite_by_id[truth.world_id]

            E0 = compatible_positive_only(worlds, positives).compatible_world_ids
            negatives = tuple(
                node_id for node_id in truth.node_ids if node_id not in set(positives)
            )
            E1 = compatible_with_perfect_negatives(
                worlds, positives, negatives
            ).compatible_world_ids
            node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
            observed_arrival = {
                node_id: int(truth.first_arrival_steps[node_index[node_id]])
                for node_id in positives
                if truth.first_arrival_steps[node_index[node_id]] is not None
            }
            E2 = compatible_with_temporal_arrivals(
                worlds, positives, negatives, observed_arrival
            ).compatible_world_ids
            E3 = _filter_direct_axis(E2, worlds_by_id, truth, axis="A")
            E4 = _filter_direct_axis(E3, worlds_by_id, truth, axis="B")
            E5 = _filter_M_accessibility(E4, worlds_by_id, truth)
            E6 = _filter_M_arrival(E5, worlds_by_id, truth)

            greedy_A = _greedy_diagnostic_nodes(
                E2, worlds_by_id, truth, axis="A", target_ids=E3
            )
            greedy_B = _greedy_diagnostic_nodes(
                E3, worlds_by_id, truth, axis="B", target_ids=E4
            )
            greedy_M = _greedy_nodes(
                E4, E5, worlds_by_id, truth, _filter_M_accessibility
            )
            greedy_tau = _greedy_nodes(
                E5, E6, worlds_by_id, truth, _filter_M_arrival
            )

            exact_A = exact_minimum_diagnostic_measurements(
                E2,
                E3,
                measurements_from_binary_state(
                    finite_worlds, ftruth, E2, component="A"
                ),
            )
            exact_B = exact_minimum_diagnostic_measurements(
                E3,
                E4,
                measurements_from_binary_state(
                    finite_worlds, ftruth, E3, component="B"
                ),
            )
            exact_M = exact_minimum_diagnostic_measurements(
                E4,
                E5,
                measurements_from_binary_state(
                    finite_worlds, ftruth, E4, component="M"
                ),
            )
            exact_tau = exact_minimum_diagnostic_measurements(
                E5,
                E6,
                measurements_from_arrival_state(
                    finite_worlds, ftruth, E5
                ),
            )

            AB_measurements = (
                *measurements_from_binary_state(
                    finite_worlds, ftruth, E2, component="A"
                ),
                *measurements_from_binary_state(
                    finite_worlds, ftruth, E2, component="B"
                ),
            )
            exact_AB_joint = exact_minimum_diagnostic_measurements(
                E2, E4, AB_measurements
            )

            M_tau_measurements = (
                *measurements_from_binary_state(
                    finite_worlds, ftruth, E4, component="M"
                ),
                *measurements_from_arrival_state(
                    finite_worlds, ftruth, E4
                ),
            )
            exact_M_tau_joint = exact_minimum_diagnostic_measurements(
                E4, E6, M_tau_measurements
            )

            exact_rows = {
                "A": exact_A,
                "B": exact_B,
                "M": exact_M,
                "tau": exact_tau,
            }
            greedy_rows = {
                "A": greedy_A,
                "B": greedy_B,
                "M": greedy_M,
                "tau": greedy_tau,
            }
            for key in ("A", "B", "M", "tau"):
                if exact_rows[key] is None:
                    failures.append(
                        {
                            "system_id": spec.system_id,
                            "truth_world_id": truth.world_id,
                            "stage": key,
                            "error": "exact_solver_returned_none",
                        }
                    )
                    continue
                e = len(exact_rows[key])
                g = len(greedy_rows[key])
                exact_counts[key].append(e)
                greedy_counts[key].append(g)
                if e == g:
                    greedy_equal[key] += 1
                elif g > e:
                    greedy_suboptimal[key] += 1
                else:
                    failures.append(
                        {
                            "system_id": spec.system_id,
                            "truth_world_id": truth.world_id,
                            "stage": key,
                            "error": "greedy_better_than_exact",
                            "greedy": g,
                            "exact": e,
                        }
                    )

            if exact_AB_joint is None or exact_M_tau_joint is None:
                failures.append(
                    {
                        "system_id": spec.system_id,
                        "truth_world_id": truth.world_id,
                        "stage": "joint",
                        "error": "joint_exact_solver_returned_none",
                    }
                )
            else:
                exact_counts["AB_joint"].append(len(exact_AB_joint))
                exact_counts["M_tau_joint"].append(len(exact_M_tau_joint))
                greedy_counts["AB_total"].append(len(greedy_A) + len(greedy_B))
                greedy_counts["M_tau_total"].append(len(greedy_M) + len(greedy_tau))

    result: dict[str, object] = {
        "schema": "eog.bam_targeted_measurement_exact_audit.v1",
        "systems_scored": systems_scored,
        "truth_cases": truth_cases,
        "failures": failures,
        "greedy_equal_to_exact_count": greedy_equal,
        "greedy_suboptimal_count": greedy_suboptimal,
        "exact_measurement_count_distribution": {
            key: _dist(values) for key, values in exact_counts.items()
        },
        "greedy_measurement_count_distribution": {
            key: _dist(values) for key, values in greedy_counts.items()
        },
        "max_exact_A": max(exact_counts["A"], default=0),
        "max_exact_B": max(exact_counts["B"], default=0),
        "max_exact_AB_joint": max(exact_counts["AB_joint"], default=0),
        "max_exact_M": max(exact_counts["M"], default=0),
        "max_exact_tau": max(exact_counts["tau"], default=0),
        "max_exact_M_tau_joint": max(exact_counts["M_tau_joint"], default=0),
        "all_greedy_counts_valid_upper_bounds": not failures,
    }
    result["fingerprint"] = _sha256(result)
    return result
