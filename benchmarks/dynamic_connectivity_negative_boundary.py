#!/usr/bin/env python3
"""Negative novelty boundary for EOG temporal reachability.

This benchmark implements a deliberately minimal time-respecting Boolean connectivity
baseline independent of EOG's probability/support propagation.  At zero support
tolerance, the baseline should recover exactly the same *structural* reached-by-time
states as EOG for a declared TemporalWorld.

It also filters a finite world set by time-stamped positive occurrences using only
Boolean reached-by-time constraints.  That compatible-world set should match EOG's
temporal reconstruction.

These equivalences are the expected result.  They establish a negative boundary:
forward dynamic reachability and positive temporal world filtering are not, by
themselves, EOG-specific algorithmic contributions.  The active EOG distinction must
therefore be sought in the declared model universe, world-indexed uncertainty,
axis-preserving minimum-relaxation inference, analyst-choice uncertainty, and explicit
coverage/certification rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    build_temporal_flow_set,
    reconstruct_temporal_worlds,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = [
        DynamicReachabilityEdge(
            source=index[source],
            target=index[target],
            geographic_support=float(support),
        )
        for source, target, support in edges
    ]
    return build_dynamic_transition_operator(node_ids, declared, loss_support=1.0)


def _empty(node_ids):
    return build_dynamic_transition_operator(node_ids, (), loss_support=1.0)


def _boolean_reached_by_time(world: TemporalWorld) -> np.ndarray:
    """Time-respecting structural reachability with no probabilistic interpretation."""

    n_nodes = len(world.node_ids)
    n_times = len(world.time_labels)
    exact = np.zeros((n_times, n_nodes), dtype=bool)
    source_index = {node_id: i for i, node_id in enumerate(world.node_ids)}
    for source_id, weight in world.source_weight_mapping.items():
        if weight > 0.0:
            exact[0, source_index[source_id]] = True

    for step, operator in enumerate(world.operators):
        adjacency = operator.transition > 0.0
        exact[step + 1] = np.any(exact[step][:, None] & adjacency, axis=0)

    return np.maximum.accumulate(exact, axis=0)


def _boolean_compatible_worlds(worlds, observations):
    ordered = tuple(sorted(worlds, key=lambda world: world.world_id))
    node_index = {node_id: i for i, node_id in enumerate(ordered[0].node_ids)}
    time_index = {time_label: i for i, time_label in enumerate(ordered[0].time_labels)}
    compatible = []
    incompatible = []
    for world in ordered:
        reached = _boolean_reached_by_time(world)
        ok = all(reached[time_index[time], node_index[node]] for node, time in observations)
        (compatible if ok else incompatible).append(world.world_id)
    return tuple(compatible), tuple(incompatible)


def _scenarios():
    nodes = ("A", "B", "C", "D")
    ab = _operator(nodes, (("A", "B", 1.0),))
    bc = _operator(nodes, (("B", "C", 1.0),))
    ac = _operator(nodes, (("A", "C", 0.25),))
    bd_cd = _operator(nodes, (("B", "D", 1.0), ("C", "D", 1.0)))
    branch = _operator(nodes, (("A", "B", 1.0), ("A", "C", 1.0)))
    empty = _empty(nodes)

    return {
        "ordered": TemporalWorld(
            "ordered",
            ("t0", "t1", "t2"),
            (ab, bc),
            ("A",),
        ),
        "reversed": TemporalWorld(
            "reversed",
            ("t0", "t1", "t2"),
            (bc, ab),
            ("A",),
        ),
        "branch_confluence": TemporalWorld(
            "branch_confluence",
            ("t0", "t1", "t2"),
            (branch, bd_cd),
            ("A",),
        ),
        "low_positive_direct": TemporalWorld(
            "low_positive_direct",
            ("t0", "t1", "t2"),
            (ac, empty),
            ("A",),
        ),
    }


def run_dynamic_connectivity_negative_boundary():
    scenarios = _scenarios()
    scenario_rows = {}
    all_equal = True

    for scenario_id, world in scenarios.items():
        baseline = _boolean_reached_by_time(world)
        eog = build_temporal_flow_set((world,), support_tolerance=0.0).reached_by_world[0]
        equal = bool(np.array_equal(baseline, eog))
        all_equal = all_equal and equal
        scenario_rows[scenario_id] = {
            "boolean_reached_by_time": baseline.tolist(),
            "eog_reached_by_time": eog.tolist(),
            "exact_structural_equivalence": equal,
        }

    worlds = (scenarios["ordered"], scenarios["reversed"])
    observations = (("C", "t2"),)
    baseline_compatible, baseline_incompatible = _boolean_compatible_worlds(worlds, observations)
    reconstruction = reconstruct_temporal_worlds(
        worlds,
        observations,
        support_tolerance=0.0,
    )
    filter_equivalence = (
        baseline_compatible == reconstruction.compatible_world_ids
        and baseline_incompatible == reconstruction.incompatible_world_ids
    )

    return {
        "schema_version": 1,
        "claim_boundary": (
            "negative novelty boundary: structural dynamic reachability and positive temporal "
            "filtering are reproducible by time-respecting Boolean connectivity"
        ),
        "scenario_equivalence": scenario_rows,
        "all_forward_reachability_equal": all_equal,
        "positive_observation_filter": {
            "observations": [list(row) for row in observations],
            "boolean_compatible_world_ids": list(baseline_compatible),
            "eog_compatible_world_ids": list(reconstruction.compatible_world_ids),
            "boolean_incompatible_world_ids": list(baseline_incompatible),
            "eog_incompatible_world_ids": list(reconstruction.incompatible_world_ids),
            "exact_filter_equivalence": filter_equivalence,
        },
        "novelty_boundary": {
            "do_not_claim_forward_dynamic_reachability_as_unique": all_equal,
            "do_not_claim_positive_world_filtering_as_unique": filter_equivalence,
            "remaining_eog_layers_to_validate": [
                "explicit ecological plus analytical world-universe declaration",
                "world-indexed support/probability sets without averaging away identity",
                "axis-preserving occurrence-conditioned minimum-relaxation frontiers",
                "finite-universe robust/contingent/excluded certificates and monotonicity",
                "survey discrimination tied to underidentified world sets",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_dynamic_connectivity_negative_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
