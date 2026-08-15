#!/usr/bin/env python3
"""Known-truth estimand comparison: static bridge vs temporal world reconstruction.

The comparator deliberately reuses EOG's existing v0.1 bridge implementation rather
than implementing a toy substitute for an external connectivity method.  The bridge
operator answers a valid static graph question: what cumulative/minimax/redundant path
connects source and target on one declared graph?  The prospective temporal inverse
layer answers a different question: which ordered transition worlds are compatible
with a time-stamped positive occurrence?

Two temporal worlds below contain the same time-aggregated A-B-C edge set.  Their edge
order differs.  Therefore a static bridge graph is identical for both, while only one
world can reach C by t2 when source mass is injected once at t0.

Passing this benchmark is evidence of estimand separation, not superiority of one
method over the other.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog import BridgeEdge, BridgeWeights, infer_bridge
from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
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


def _temporal_worlds():
    nodes = ("A", "B", "C")
    ab = _operator(nodes, (("A", "B", 1.0),))
    bc = _operator(nodes, (("B", "C", 1.0),))
    ordered = TemporalWorld(
        "ordered",
        ("t0", "t1", "t2"),
        (ab, bc),
        ("A",),
    )
    reversed_order = TemporalWorld(
        "reversed",
        ("t0", "t1", "t2"),
        (bc, ab),
        ("A",),
    )
    return ordered, reversed_order


def _time_aggregated_edges(world):
    node_ids = world.node_ids
    edges = set()
    for operator in world.operators:
        sources, targets = np.nonzero(operator.transition > 0.0)
        for source, target in zip(sources.tolist(), targets.tolist(), strict=True):
            edges.add((node_ids[source], node_ids[target]))
    return tuple(sorted(edges))


def _static_bridge_summary():
    edges = (
        BridgeEdge(0, 1, geographic_cost=1.0, environmental_cost=0.0),
        BridgeEdge(1, 2, geographic_cost=1.0, environmental_cost=0.0),
    )
    result = infer_bridge(
        3,
        edges,
        0,
        2,
        weights=BridgeWeights(geographic=1.0, environmental=0.0, barrier=0.0),
    )
    return {
        "minimum_cost_nodes": list(result.minimum_cost_path.nodes),
        "minimum_cost": result.minimum_cost_path.cumulative_cost,
        "minimum_bottleneck": result.minimum_bottleneck_path.bottleneck_cost,
        "geographic_cost": result.minimum_cost_path.geographic_cost,
        "environmental_cost": result.minimum_cost_path.environmental_cost,
        "barrier_cost": result.minimum_cost_path.barrier_cost,
        "edge_disjoint_path_count": result.edge_disjoint_path_count,
    }


def run_bridge_temporal_comparator():
    ordered, reversed_order = _temporal_worlds()
    ordered_edges = _time_aggregated_edges(ordered)
    reversed_edges = _time_aggregated_edges(reversed_order)
    bridge = _static_bridge_summary()

    reconstruction = reconstruct_temporal_worlds(
        (ordered, reversed_order),
        (("C", "t2"),),
    )
    unsupported = dict(reconstruction.unsupported_observations_by_world)

    return {
        "schema_version": 1,
        "claim_boundary": (
            "known-truth static-connectivity vs temporal-realizability estimand separation; "
            "not method superiority"
        ),
        "time_aggregated_graph": {
            "ordered_edges": [list(edge) for edge in ordered_edges],
            "reversed_edges": [list(edge) for edge in reversed_edges],
            "identical_static_edge_set": ordered_edges == reversed_edges,
        },
        "static_bridge": bridge,
        "temporal_inverse": {
            "compatible_world_ids": list(reconstruction.compatible_world_ids),
            "incompatible_world_ids": list(reconstruction.incompatible_world_ids),
            "reversed_unsupported_observations": [
                list(row) for row in unsupported["reversed"]
            ],
            "identifiable_with_C_t2": reconstruction.identifiable,
        },
        "separation_checks": {
            "static_bridge_is_well_defined": (
                bridge["minimum_cost_nodes"] == [0, 1, 2]
                and bridge["minimum_cost"] == 2.0
                and bridge["minimum_bottleneck"] == 1.0
            ),
            "static_graph_cannot_encode_edge_order": ordered_edges == reversed_edges,
            "temporal_order_changes_realizability": (
                reconstruction.compatible_world_ids == ("ordered",)
                and reconstruction.incompatible_world_ids == ("reversed",)
            ),
            "bridge_and_temporal_inverse_answer_different_questions": (
                ordered_edges == reversed_edges
                and reconstruction.compatible_world_ids == ("ordered",)
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_bridge_temporal_comparator()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
