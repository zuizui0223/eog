#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)
from eog.v2.temporal_reachability import TemporalWorld
from eog.v2.temporal_reconstruction import (
    compare_temporal_reconstructions,
    reconstruct_temporal_worlds,
)
from eog.v2.world_reconstruction import (
    FiniteWorld,
    build_world_flow_set,
    compare_world_flow_universes,
    reconstruct_compatible_worlds,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_virtual_worlds_v1/protocol_v1.json"


def _sha256(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _operator(node_ids, edge_specs):
    index = {node: i for i, node in enumerate(node_ids)}
    edges = []
    for row in edge_specs:
        source, target = row[:2]
        kwargs = dict(row[2]) if len(row) > 2 else {}
        edges.append(
            DynamicReachabilityEdge(
                index[source],
                index[target],
                geographic_support=float(kwargs.get("geographic_support", 1.0)),
                environmental_support=float(kwargs.get("environmental_support", 1.0)),
                barrier_support=float(kwargs.get("barrier_support", 1.0)),
                directional_support=float(kwargs.get("directional_support", 1.0)),
            )
        )
    return build_dynamic_transition_operator(node_ids, tuple(edges), loss_support=1.0)


def _reachable(operator, source, target, max_steps):
    summary = summarize_first_passage(
        operator,
        (source,),
        target,
        max_steps=max_steps,
    )
    return {
        "reachable": bool(summary.horizon_support > 1e-15),
        "horizon_support": float(summary.horizon_support),
        "first_positive_step": summary.first_positive_step,
    }


def _adjacency(operator):
    out = {node: [] for node in operator.node_ids}
    for i, source in enumerate(operator.node_ids):
        for j, target in enumerate(operator.node_ids):
            if operator.raw_support[i, j] > 0:
                out[source].append(target)
    return {key: tuple(sorted(value)) for key, value in out.items()}


def _simple_paths(operator, source, target, max_depth=8):
    graph = _adjacency(operator)
    paths = []

    def visit(node, path):
        if len(path) - 1 > max_depth:
            return
        if node == target:
            paths.append(tuple(path))
            return
        for nxt in graph[node]:
            if nxt in path:
                continue
            visit(nxt, [*path, nxt])

    visit(source, [source])
    return tuple(sorted(paths))


def _knockout_operator(operator, *, node=None, edge=None):
    specs = []
    for i, source in enumerate(operator.node_ids):
        for j, target in enumerate(operator.node_ids):
            if operator.raw_support[i, j] <= 0:
                continue
            if node is not None and (source == node or target == node):
                continue
            if edge is not None and (source, target) == edge:
                continue
            specs.append((source, target, {"geographic_support": 1.0}))
    return _operator(operator.node_ids, specs)


def V1_suitable_but_unreachable():
    nodes = ("S", "T")
    open_op = _operator(nodes, (("S", "T", {"barrier_support": 1.0}),))
    closed_op = _operator(nodes, (("S", "T", {"barrier_support": 0.0}),))
    A = {"S": True, "T": True}
    open_r = _reachable(open_op, "S", "T", 1)
    closed_r = _reachable(closed_op, "S", "T", 1)
    return {
        "local_viability_T_all_worlds": A["T"],
        "open_reachable": open_r["reachable"],
        "closed_reachable": closed_r["reachable"],
        "supported": A["T"] and open_r["reachable"] and not closed_r["reachable"],
    }


def V2_endpoint_match_intermediate_gap():
    nodes = ("S", "X", "T")
    endpoint_environment = {"S": 0.0, "X": 10.0, "T": 0.0}
    endpoint_distance = abs(endpoint_environment["S"] - endpoint_environment["T"])
    endpoint_only = _operator(
        nodes,
        (
            ("S", "X", {"environmental_support": 1.0}),
            ("X", "T", {"environmental_support": 1.0}),
        ),
    )
    pathwise = _operator(
        nodes,
        (
            ("S", "X", {"environmental_support": 0.0}),
            ("X", "T", {"environmental_support": 0.0}),
        ),
    )
    e = _reachable(endpoint_only, "S", "T", 2)
    p = _reachable(pathwise, "S", "T", 2)
    return {
        "endpoint_environmental_distance": endpoint_distance,
        "intermediate_environmental_gap": 10.0,
        "endpoint_only_reachable": e["reachable"],
        "pathwise_reachable": p["reachable"],
        "supported": endpoint_distance == 0.0 and e["reachable"] and not p["reachable"],
    }


def V3_stepping_stone():
    nodes = ("S", "X", "T")
    no_step = _operator(nodes, ())
    with_step = _operator(nodes, (("S", "X"), ("X", "T")))
    n = _reachable(no_step, "S", "T", 2)
    s = _reachable(with_step, "S", "T", 2)
    return {
        "endpoint_local_viability_equal": True,
        "without_step_reachable": n["reachable"],
        "with_step_reachable": s["reachable"],
        "with_step_first_arrival": s["first_positive_step"],
        "supported": not n["reachable"] and s["reachable"] and s["first_positive_step"] == 2,
    }


def V4_bottleneck_vs_redundancy():
    nodes = ("S", "A", "B", "T")
    bottleneck = _operator(nodes, (("S", "A"), ("A", "T")))
    redundant = _operator(
        nodes,
        (("S", "A"), ("A", "T"), ("S", "B"), ("B", "T")),
    )
    b_paths = _simple_paths(bottleneck, "S", "T")
    r_paths = _simple_paths(redundant, "S", "T")
    b_knock = _reachable(
        _knockout_operator(bottleneck, node="A"), "S", "T", 3
    )["reachable"]
    r_knock = _reachable(
        _knockout_operator(redundant, node="A"), "S", "T", 3
    )["reachable"]
    return {
        "observed_occurrences": ["S", "T"],
        "bottleneck_path_count": len(b_paths),
        "redundant_path_count": len(r_paths),
        "bottleneck_after_A_knockout_reachable": b_knock,
        "redundant_after_A_knockout_reachable": r_knock,
        "supported": (
            len(b_paths) == 1
            and len(r_paths) == 2
            and not b_knock
            and r_knock
        ),
    }


def V5_same_distribution_different_history():
    nodes = ("S", "X", "T")
    direct = FiniteWorld(
        "direct_history",
        _operator(nodes, (("S", "T"),)),
        ("S",),
    )
    stepping = FiniteWorld(
        "stepping_history",
        _operator(nodes, (("S", "X"), ("X", "T"))),
        ("S",),
    )
    worlds = (direct, stepping)
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("S", "T"),
        max_steps=2,
    )
    direct_fp = _reachable(direct.operator, "S", "T", 2)
    step_fp = _reachable(stepping.operator, "S", "T", 2)
    return {
        "static_occurrence_set": ["S", "T"],
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "history_count": len(reconstruction.compatible_world_ids),
        "direct_first_arrival": direct_fp["first_positive_step"],
        "stepping_first_arrival": step_fp["first_positive_step"],
        "supported": (
            set(reconstruction.compatible_world_ids)
            == {"direct_history", "stepping_history"}
            and direct_fp["first_positive_step"] == 1
            and step_fp["first_positive_step"] == 2
        ),
    }


def V6_static_alias_temporal_split():
    nodes = ("S", "X", "T")
    no_edges = _operator(nodes, ())
    fast_1 = _operator(nodes, (("S", "T"),))
    slow_1 = _operator(nodes, (("S", "X"),))
    slow_2 = _operator(nodes, (("X", "T"),))

    fast = TemporalWorld(
        "fast_history",
        ("t0", "t1", "t2"),
        (fast_1, no_edges),
        ("S",),
    )
    slow = TemporalWorld(
        "slow_history",
        ("t0", "t1", "t2"),
        (slow_1, slow_2),
        ("S",),
    )
    worlds = (fast, slow)
    before = reconstruct_temporal_worlds(
        worlds,
        (("S", "t0"), ("T", "t2")),
    )
    after = reconstruct_temporal_worlds(
        worlds,
        (("S", "t0"), ("T", "t1"), ("T", "t2")),
    )
    update = compare_temporal_reconstructions(before, after)
    return {
        "before_compatible_world_ids": list(before.compatible_world_ids),
        "after_compatible_world_ids": list(after.compatible_world_ids),
        "eliminated_world_ids": list(update.eliminated_world_ids),
        "contraction_fraction": update.contraction_fraction,
        "supported": (
            set(before.compatible_world_ids) == {"fast_history", "slow_history"}
            and after.compatible_world_ids == ("fast_history",)
            and update.eliminated_world_ids == ("slow_history",)
        ),
    }


def H7_world_expansion_monotonicity():
    nodes = ("S", "U", "T")
    closed = FiniteWorld(
        "closed",
        _operator(nodes, (("S", "U"),)),
        ("S",),
    )
    open_world = FiniteWorld(
        "open",
        _operator(nodes, (("S", "U"), ("U", "T"))),
        ("S",),
    )

    # S and U are the shared positive anchors.  T is an unsampled candidate node.
    # Adding the permissive world may make T possible, but cannot create a new robust
    # impossibility.
    before_r = reconstruct_compatible_worlds(
        (closed,),
        ("S", "U"),
        max_steps=2,
    )
    after_r = reconstruct_compatible_worlds(
        (closed, open_world),
        ("S", "U"),
        max_steps=2,
    )
    before = build_world_flow_set(before_r, (closed,))
    after = build_world_flow_set(after_r, (closed, open_world))
    update = compare_world_flow_universes(before, after)
    return {
        "before_possible_ids": list(before.possible_ids),
        "after_possible_ids": list(after.possible_ids),
        "before_robustly_unreachable_ids": list(before.robustly_unreachable_ids),
        "after_robustly_unreachable_ids": list(after.robustly_unreachable_ids),
        "gained_possible_ids": list(update.gained_possible_ids),
        "lost_robustly_unreachable_ids": list(
            update.lost_robustly_unreachable_ids
        ),
        "monotonicity_holds": update.monotonicity_holds,
        "supported": (
            update.monotonicity_holds
            and "T" in update.gained_possible_ids
            and "T" in update.lost_robustly_unreachable_ids
        ),
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_benchmark_implementation_and_scoring":
        raise RuntimeError("protocol is not frozen")

    results = {
        "V1_suitable_but_unreachable": V1_suitable_but_unreachable(),
        "V2_endpoint_match_intermediate_gap": V2_endpoint_match_intermediate_gap(),
        "V3_stepping_stone": V3_stepping_stone(),
        "V4_bottleneck_vs_redundancy": V4_bottleneck_vs_redundancy(),
        "V5_same_distribution_different_history": V5_same_distribution_different_history(),
        "V6_static_alias_temporal_split": V6_static_alias_temporal_split(),
        "H7_world_expansion_monotonicity": H7_world_expansion_monotonicity(),
    }
    verdicts = {
        "H1_viability_not_reachability": (
            "SUPPORTED" if results["V1_suitable_but_unreachable"]["supported"] else "REFUTED"
        ),
        "H2_pathwise_IBE_matters": (
            "SUPPORTED" if results["V2_endpoint_match_intermediate_gap"]["supported"] else "REFUTED"
        ),
        "H3_stepping_stones_change_reachability": (
            "SUPPORTED" if results["V3_stepping_stone"]["supported"] else "REFUTED"
        ),
        "H4_bottleneck_and_route_redundancy_are_distinct": (
            "SUPPORTED" if results["V4_bottleneck_vs_redundancy"]["supported"] else "REFUTED"
        ),
        "H5_occurrences_do_not_identify_unique_history": (
            "SUPPORTED" if results["V5_same_distribution_different_history"]["supported"] else "REFUTED"
        ),
        "H6_temporal_evidence_contracts_history_fiber": (
            "SUPPORTED" if results["V6_static_alias_temporal_split"]["supported"] else "REFUTED"
        ),
        "H7_robust_impossibility_is_monotone_under_world_expansion": (
            "SUPPORTED" if results["H7_world_expansion_monotonicity"]["supported"] else "REFUTED"
        ),
    }
    payload = {
        "schema": "eog.original_idea_virtual_worlds.result.v1",
        "results": results,
        "predeclared_verdicts": verdicts,
    }
    payload["fingerprint"] = _sha256(payload)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
