#!/usr/bin/env python3
"""Finite history-matching / NROY negative boundary for EOG world reconstruction.

History matching rules out model parameter settings that are implausible given
observations and uncertainty, retaining the Not-Ruled-Out-Yet (NROY) region for later
waves.  This benchmark asks whether EOG's *finite exact* compatible-world filtering is,
in the zero-emulator / zero-discrepancy special case, the same logical operation.

The baseline below is deliberately independent of EOG reconstruction.  Each declared
world is treated as a deterministic simulator whose output is the set of nodes reachable
from source A within two directed steps.  A history-matching wave retains a world only
when all positive observed nodes are in that output set.

Known truth:

- world_B: A -> B -> C;
- world_D: A -> D -> C;
- world_fail: A -> B only.

Wave 1 observations A,C retain world_B and world_D and rule out world_fail.
Wave 2 adds B, retaining only world_B.

Exact agreement with EOG is the expected result.  Therefore EOG must not claim novelty
for generic finite model-world elimination, retention of a compatible/NROY set, or
sequential set contraction after additional observations.  The remaining ecological
question lies in how the worlds and constraints are constructed and interpreted:
occurrence-anchored reachability, ecological versus analyst-choice alternatives,
axis-preserving relaxation/rescue sets, and explicit finite-universe certificates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    compare_reconstructions,
    reconstruct_compatible_worlds,
)


NODE_IDS = ("A", "B", "C", "D")
INDEX = {node_id: i for i, node_id in enumerate(NODE_IDS)}
WORLD_SPECS = {
    "world_B": (("A", "B"), ("B", "C")),
    "world_D": (("A", "D"), ("D", "C")),
    "world_fail": (("A", "B"),),
}
MAX_STEPS = 2


def _independent_reachable(edges, source="A", max_steps=MAX_STEPS):
    adjacency = {node_id: [] for node_id in NODE_IDS}
    for left, right in edges:
        adjacency[left].append(right)

    reached = {source}
    frontier = {source}
    for _step in range(max_steps):
        next_frontier = set()
        for node in frontier:
            next_frontier.update(adjacency[node])
        next_frontier.difference_update(reached)
        reached.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    return tuple(node_id for node_id in NODE_IDS if node_id in reached)


def _history_match(observations):
    observed = set(observations)
    nroy = []
    ruled_out = []
    simulator_outputs = {}
    for world_id in sorted(WORLD_SPECS):
        reachable = _independent_reachable(WORLD_SPECS[world_id])
        simulator_outputs[world_id] = list(reachable)
        if observed.issubset(reachable):
            nroy.append(world_id)
        else:
            ruled_out.append(world_id)
    return {
        "observations": list(observations),
        "nroy_world_ids": nroy,
        "ruled_out_world_ids": ruled_out,
        "simulator_outputs": simulator_outputs,
    }


def _operator(edges):
    declared = [
        DynamicReachabilityEdge(
            source=INDEX[source],
            target=INDEX[target],
            geographic_support=1.0,
        )
        for source, target in edges
    ]
    return build_dynamic_transition_operator(NODE_IDS, declared, loss_support=1.0)


def _worlds():
    return tuple(
        FiniteWorld(world_id, _operator(WORLD_SPECS[world_id]), ("A",))
        for world_id in sorted(WORLD_SPECS)
    )


def run_history_matching_nroy_boundary():
    wave1_observations = ("A", "C")
    wave2_observations = ("A", "B", "C")

    history_wave1 = _history_match(wave1_observations)
    history_wave2 = _history_match(wave2_observations)

    worlds = _worlds()
    eog_wave1 = reconstruct_compatible_worlds(
        worlds,
        wave1_observations,
        max_steps=MAX_STEPS,
    )
    eog_wave2 = reconstruct_compatible_worlds(
        worlds,
        wave2_observations,
        max_steps=MAX_STEPS,
    )
    eog_update = compare_reconstructions(eog_wave1, eog_wave2)

    history_eliminated = sorted(
        set(history_wave1["nroy_world_ids"]).difference(history_wave2["nroy_world_ids"])
    )
    history_contraction = (
        len(history_eliminated) / len(history_wave1["nroy_world_ids"])
        if history_wave1["nroy_world_ids"]
        else 0.0
    )

    wave1_equal = (
        tuple(history_wave1["nroy_world_ids"]) == eog_wave1.compatible_world_ids
        and tuple(history_wave1["ruled_out_world_ids"]) == eog_wave1.incompatible_world_ids
    )
    wave2_equal = (
        tuple(history_wave2["nroy_world_ids"]) == eog_wave2.compatible_world_ids
        and tuple(history_wave2["ruled_out_world_ids"]) == eog_wave2.incompatible_world_ids
    )

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "history matching / Not-Ruled-Out-Yet (NROY) model-space reduction",
            "primary_climate_reference": (
                "Williamson et al. 2013, Climate Dynamics 41:1703-1729"
            ),
            "primary_climate_doi": "10.1007/s00382-013-1896-4",
            "environmental_emulation_reference": (
                "Salter et al. 2016, Environmetrics 27:507-523"
            ),
            "environmental_emulation_doi": "10.1002/env.2405",
        },
        "finite_special_case_boundary": (
            "deterministic finite worlds; exact simulator outputs; no emulator, observation-error, "
            "model-discrepancy, or implausibility-threshold approximation"
        ),
        "history_matching_baseline": {
            "wave1": history_wave1,
            "wave2": history_wave2,
            "eliminated_between_waves": history_eliminated,
            "contraction_fraction": history_contraction,
        },
        "eog_reconstruction": {
            "wave1_compatible_world_ids": list(eog_wave1.compatible_world_ids),
            "wave1_incompatible_world_ids": list(eog_wave1.incompatible_world_ids),
            "wave2_compatible_world_ids": list(eog_wave2.compatible_world_ids),
            "wave2_incompatible_world_ids": list(eog_wave2.incompatible_world_ids),
            "eliminated_between_waves": list(eog_update.eliminated_world_ids),
            "contraction_fraction": eog_update.contraction_fraction,
            "became_identifiable": eog_update.became_identifiable,
        },
        "negative_boundary": {
            "wave1_nroy_equals_eog_compatible_set": wave1_equal,
            "wave2_nroy_equals_eog_compatible_set": wave2_equal,
            "sequential_contraction_matches": (
                history_eliminated == list(eog_update.eliminated_world_ids)
                and abs(history_contraction - eog_update.contraction_fraction) < 1e-12
            ),
            "do_not_claim_generic_world_filtering_as_unique": True,
            "do_not_claim_compatible_world_set_as_unique": True,
            "do_not_claim_sequential_world_set_contraction_as_unique": True,
            "remaining_eog_question": (
                "how biogeographic reachability worlds are declared from occurrence, geographic, "
                "environmental, barrier, temporal, and analyst-choice constraints; how alternative "
                "relaxations remain Pareto-separated; and how finite-universe structural claims are certified"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_history_matching_nroy_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
