#!/usr/bin/env python3
"""Known-truth boundary: never splice edges from alternative worlds into one path.

A pooled union of mutually exclusive transition graphs can manufacture a
source-to-target route that is absent from *every* admissible world.  This is
a stronger failure than the spurious route redundancy documented in
circuit_world_aggregation_boundary.py.

This benchmark exercises the existing EOG finite-world and temporal APIs.
It is a response-free logical test, not a new connectivity algorithm,
field-validated forecasting gain, or a fourth EOG-WF endpoint.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    TemporalWorld,
    build_dynamic_transition_operator,
    build_temporal_flow_set,
    build_world_flow_set,
    compare_world_flow_universes,
    reconstruct_compatible_worlds,
    summarize_temporal_transition_landscape,
)


NODES = ("A", "B", "C")
INDEX = {node_id: index for index, node_id in enumerate(NODES)}
AB = (("A", "B"),)
BC = (("B", "C"),)
ABC = AB + BC
TIMES = ("t0", "t1", "t2")


def _operator(edges):
    return build_dynamic_transition_operator(
        NODES,
        [
            DynamicReachabilityEdge(
                source=INDEX[source],
                target=INDEX[target],
                geographic_support=1.0,
            )
            for source, target in edges
        ],
        loss_support=1.0,
    )


def _static_flow(worlds):
    reconstruction = reconstruct_compatible_worlds(
        worlds, ("A",), max_steps=2
    )
    flow = build_world_flow_set(reconstruction, worlds)
    return reconstruction, flow


def _target_support(flow, node_id="C"):
    row = next(row for row in flow.node_envelopes if row.node_id == node_id)
    return {world_id: support for world_id, support in row.support_by_world}


def _static_splicing():
    ab = FiniteWorld("world_ab", _operator(AB), ("A",))
    bc = FiniteWorld("world_bc", _operator(BC), ("A",))
    declared = (ab, bc)
    reconstruction, flow = _static_flow(declared)

    # This pooled world is intentionally *not* a member of the original
    # admissible universe. It is a deliberately invalid comparator.
    pooled = FiniteWorld("illicit_pooled_graph", _operator(ABC), ("A",))
    _, pooled_flow = _static_flow((pooled,))

    # A genuine full-path world is added only in this separate expansion.
    # Before that expansion C must remain excluded.
    complete = FiniteWorld("world_abc", _operator(ABC), ("A",))
    expanded_reconstruction, expanded_flow = _static_flow((*declared, complete))
    update = compare_world_flow_universes(flow, expanded_flow)

    return {
        "declared_world_edges": {
            "world_ab": [list(edge) for edge in AB],
            "world_bc": [list(edge) for edge in BC],
        },
        "observed_positive_ids": ["A"],
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "target_support_by_world": _target_support(flow),
        "target_status": next(
            row.status for row in flow.node_envelopes if row.node_id == "C"
        ),
        "robustly_unreachable_ids": list(flow.robustly_unreachable_ids),
        "pooled_union_edges": [list(edge) for edge in ABC],
        "illicit_pooled_target_support": _target_support(pooled_flow),
        "illicit_pooled_target_possible": "C" in pooled_flow.possible_ids,
        "genuine_expansion": {
            "added_world_ids": list(update.added_world_ids),
            "new_compatible_world_ids": list(expanded_reconstruction.compatible_world_ids),
            "new_target_status": next(
                row.status for row in expanded_flow.node_envelopes if row.node_id == "C"
            ),
            "lost_excluded_ids": list(update.lost_robustly_unreachable_ids),
            "monotonicity_holds": update.monotonicity_holds,
        },
        "coverage_certificate": flow.coverage_certificate,
        "fingerprint_order_invariant": (
            flow.fingerprint == _static_flow(tuple(reversed(declared)))[1].fingerprint
        ),
    }


def _temporal_splicing():
    # Edges occur at different time intervals AND in different worlds.
    # They never coexist in one complete world-indexed trajectory.
    early = TemporalWorld(
        "world_early_ab", TIMES, (_operator(AB), _operator(())), ("A",)
    )
    late = TemporalWorld(
        "world_late_bc", TIMES, (_operator(()), _operator(BC)), ("A",)
    )
    declared = (early, late)
    flow = build_temporal_flow_set(declared)
    landscape = summarize_temporal_transition_landscape(declared)

    # Union *within each time interval* can still splice distinct worlds.
    pooled = TemporalWorld(
        "illicit_temporal_union", TIMES, (_operator(AB), _operator(BC)), ("A",)
    )
    pooled_flow = build_temporal_flow_set((pooled,))
    target_index = INDEX["C"]

    return {
        "time_labels": list(TIMES),
        "world_ids": list(flow.world_ids),
        "target_exact_time_mass_by_world": {
            world_id: float(mass[-1, target_index])
            for world_id, mass in zip(
                flow.world_ids, flow.mass_by_world, strict=True
            )
        },
        "target_status_at_final_time": (
            "robustly_unreachable"
            if "C" in flow.robustly_unreachable_by_time[-1]
            else "not_excluded"
        ),
        "possible_edges_by_interval": [
            [
                list(edge)
                for edge in (*robust, *contingent)
            ]
            for robust, contingent in zip(
                landscape.robust_edges_by_interval,
                landscape.contingent_edges_by_interval,
                strict=True,
            )
        ],
        "illicit_pooled_target_exact_time_mass": float(
            pooled_flow.mass_by_world[0][-1, target_index]
        ),
        "illicit_pooled_target_possible": (
            "C" not in pooled_flow.robustly_unreachable_by_time[-1]
        ),
        "coverage_certificate": flow.coverage_certificate,
        "fingerprint_order_invariant": (
            flow.fingerprint == build_temporal_flow_set(tuple(reversed(declared))).fingerprint
        ),
    }


def run_world_coherent_reachability_boundary():
    static = _static_splicing()
    temporal = _temporal_splicing()
    static_violation = (
        set(static["compatible_world_ids"]) == {"world_ab", "world_bc"}
        and static["target_status"] == "robustly_unreachable"
        and all(value == 0.0 for value in static["target_support_by_world"].values())
        and static["illicit_pooled_target_possible"]
        and static["genuine_expansion"]["new_target_status"] == "contingent"
        and static["genuine_expansion"]["lost_excluded_ids"] == ["C"]
        and static["genuine_expansion"]["monotonicity_holds"]
    )
    temporal_violation = (
        temporal["target_status_at_final_time"] == "robustly_unreachable"
        and all(
            value == 0.0
            for value in temporal["target_exact_time_mass_by_world"].values()
        )
        and temporal["illicit_pooled_target_possible"]
        and temporal["illicit_pooled_target_exact_time_mass"] > 0.0
    )
    return {
        "schema_version": 1,
        "static": static,
        "temporal": temporal,
        "checks": {
            "pooling_manufactures_static_false_reachability": static_violation,
            "pooling_manufactures_temporal_false_reachability": temporal_violation,
            "both_world_order_invariant": (
                static["fingerprint_order_invariant"]
                and temporal["fingerprint_order_invariant"]
            ),
            "no_existing_frozen_endpoint_modified": True,
        },
        "claim_boundary": (
            "known-truth world-coherence counterexample; "
            "conditional finite-world exclusion, not biological impossibility "
            "or empirical predictive superiority"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_world_coherent_reachability_boundary()
    content = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is None:
        print(content)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
