#!/usr/bin/env python3
"""Circuit-theory negative boundary and world-aggregation test.

McRae et al. (2008) explicitly introduced circuit-theoretic ecological connectivity as a
way to integrate contributions of multiple dispersal pathways.  EOG therefore must not
claim novelty merely for recognizing multiple routes or route redundancy.

This benchmark asks a narrower question that matters to the remaining EOG mainline:
what happens when two routes do **not** coexist in one declared ecological/analytical
world, but instead belong to two mutually alternative admissible worlds?

Known truth:

- world_B contains only A-B-C;
- world_D contains only A-D-C;
- both worlds can realize observed endpoint C from source A;
- each world has one path and effective resistance 2;
- if the worlds are incorrectly unioned into one graph, the aggregate graph has two
  parallel paths, edge-disjoint redundancy 2, and effective resistance 1.

Circuit theory is correct for the aggregate graph **if that graph is the declared
landscape**.  The negative boundary is that multiple-path integration itself is prior
art.  The additional EOG question is whether uncertain/mutually exclusive world
representations should be aggregated before connectivity is calculated.  EOG retains
world identity and therefore does not manufacture simultaneous redundancy that occurs
in no individual admissible world.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog import BridgeEdge, BridgeWeights, infer_bridge
from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    build_world_flow_set,
    reconstruct_compatible_worlds,
)


NODE_IDS = ("A", "B", "C", "D")
INDEX = {node_id: i for i, node_id in enumerate(NODE_IDS)}
WORLD_B_EDGES = (("A", "B"), ("B", "C"))
WORLD_D_EDGES = (("A", "D"), ("D", "C"))


def _dynamic_operator(edges):
    declared = [
        DynamicReachabilityEdge(
            source=INDEX[source],
            target=INDEX[target],
            geographic_support=1.0,
        )
        for source, target in edges
    ]
    return build_dynamic_transition_operator(NODE_IDS, declared, loss_support=1.0)


def _finite_world(world_id, edges):
    return FiniteWorld(world_id, _dynamic_operator(edges), ("A",))


def _bridge_edges(edges):
    return tuple(
        BridgeEdge(
            INDEX[left],
            INDEX[right],
            geographic_cost=1.0,
            environmental_cost=0.0,
            barrier_cost=0.0,
        )
        for left, right in edges
    )


def _bridge_summary(edges):
    result = infer_bridge(
        len(NODE_IDS),
        _bridge_edges(edges),
        INDEX["A"],
        INDEX["C"],
        weights=BridgeWeights(geographic=1.0, environmental=0.0, barrier=0.0),
    )
    return {
        "minimum_path": [NODE_IDS[index] for index in result.minimum_cost_path.nodes],
        "minimum_cost": result.minimum_cost_path.cumulative_cost,
        "minimum_bottleneck": result.minimum_bottleneck_path.bottleneck_cost,
        "edge_disjoint_path_count": result.edge_disjoint_path_count,
    }


def _effective_resistance(edges, source="A", target="C") -> float:
    """Effective resistance for an undirected unit-resistance graph."""

    n_nodes = len(NODE_IDS)
    laplacian = np.zeros((n_nodes, n_nodes), dtype=float)
    for left, right in edges:
        i = INDEX[left]
        j = INDEX[right]
        conductance = 1.0
        laplacian[i, i] += conductance
        laplacian[j, j] += conductance
        laplacian[i, j] -= conductance
        laplacian[j, i] -= conductance

    source_index = INDEX[source]
    target_index = INDEX[target]
    keep = [index for index in range(n_nodes) if index != target_index]
    reduced = laplacian[np.ix_(keep, keep)]
    injection = np.zeros(n_nodes, dtype=float)
    injection[source_index] = 1.0
    injection[target_index] = -1.0
    reduced_injection = injection[keep]
    voltages_reduced = np.linalg.solve(reduced, reduced_injection)
    voltages = np.zeros(n_nodes, dtype=float)
    voltages[keep] = voltages_reduced
    voltages[target_index] = 0.0
    return float(voltages[source_index] - voltages[target_index])


def _edge_currents(edges, source="A", target="C"):
    n_nodes = len(NODE_IDS)
    laplacian = np.zeros((n_nodes, n_nodes), dtype=float)
    for left, right in edges:
        i = INDEX[left]
        j = INDEX[right]
        laplacian[i, i] += 1.0
        laplacian[j, j] += 1.0
        laplacian[i, j] -= 1.0
        laplacian[j, i] -= 1.0
    source_index = INDEX[source]
    target_index = INDEX[target]
    keep = [index for index in range(n_nodes) if index != target_index]
    injection = np.zeros(n_nodes, dtype=float)
    injection[source_index] = 1.0
    injection[target_index] = -1.0
    voltages_reduced = np.linalg.solve(
        laplacian[np.ix_(keep, keep)], injection[keep]
    )
    voltages = np.zeros(n_nodes, dtype=float)
    voltages[keep] = voltages_reduced
    currents = []
    for left, right in edges:
        current = abs(voltages[INDEX[left]] - voltages[INDEX[right]])
        currents.append([left, right, float(current)])
    return currents


def run_circuit_world_aggregation_boundary():
    world_b = _finite_world("world_B", WORLD_B_EDGES)
    world_d = _finite_world("world_D", WORLD_D_EDGES)
    worlds = (world_b, world_d)
    reconstruction = reconstruct_compatible_worlds(
        worlds, ("A", "C"), max_steps=2
    )
    flow_set = build_world_flow_set(reconstruction, worlds)

    union_edges = tuple(sorted(set(WORLD_B_EDGES) | set(WORLD_D_EDGES)))
    bridge_b = _bridge_summary(WORLD_B_EDGES)
    bridge_d = _bridge_summary(WORLD_D_EDGES)
    bridge_union = _bridge_summary(union_edges)
    resistance_b = _effective_resistance(WORLD_B_EDGES)
    resistance_d = _effective_resistance(WORLD_D_EDGES)
    resistance_union = _effective_resistance(union_edges)
    union_currents = _edge_currents(union_edges)

    world_edge_sets = {
        "world_B": [list(edge) for edge in WORLD_B_EDGES],
        "world_D": [list(edge) for edge in WORLD_D_EDGES],
    }
    no_world_has_union = all(
        set(tuple(edge) for edge in edges) != set(union_edges)
        for edges in world_edge_sets.values()
    )

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "circuit-theoretic ecological connectivity",
            "reference": "McRae et al. 2008, Ecology 89:2712-2724",
            "doi": "10.1890/07-1861.1",
            "prior_art_boundary": "integration of contributions from multiple dispersal pathways",
        },
        "declared_worlds": {
            "world_edge_sets": world_edge_sets,
            "compatible_world_ids": list(reconstruction.compatible_world_ids),
            "identifiable": reconstruction.identifiable,
            "contingent_node_ids": list(flow_set.contingent_ids),
            "worlds_remain_separate": len(reconstruction.compatible_world_ids) == 2,
        },
        "within_world_connectivity": {
            "world_B_bridge": bridge_b,
            "world_D_bridge": bridge_d,
            "world_B_effective_resistance": resistance_b,
            "world_D_effective_resistance": resistance_d,
        },
        "incorrect_world_union": {
            "union_edges": [list(edge) for edge in union_edges],
            "bridge": bridge_union,
            "effective_resistance": resistance_union,
            "edge_currents": union_currents,
            "no_individual_world_contains_union_graph": no_world_has_union,
        },
        "negative_boundary": {
            "multiple_pathways_are_prior_art": True,
            "route_redundancy_is_not_unique_to_eog": True,
            "parallel_paths_reduce_effective_resistance": (
                abs(resistance_b - 2.0) < 1e-12
                and abs(resistance_d - 2.0) < 1e-12
                and abs(resistance_union - 1.0) < 1e-12
            ),
            "aggregate_graph_manufactures_redundancy": (
                bridge_b["edge_disjoint_path_count"] == 1
                and bridge_d["edge_disjoint_path_count"] == 1
                and bridge_union["edge_disjoint_path_count"] == 2
                and no_world_has_union
            ),
            "remaining_eog_question": (
                "whether alternative ecological/analytical world representations may be "
                "aggregated before connectivity inference, or must remain world-indexed"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_circuit_world_aggregation_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
