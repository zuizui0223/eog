#!/usr/bin/env python3
"""Certified synthetic source-horizon MRR audit (v4).

A given threshold world has source-specific minimum required hop depths.
Their min/max define the exact source-existential vs source-universal gap
interval. On a baseline strongly connected source core, that interval's
length is at most the core's directed diameter.

Research-only; no biological origin or observed dispersal is inferred.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean
from typing import Any

from benchmarks.occurrence_conditioned_source_minrelax_v2 import AXES, _pareto_min, run_source_universe
from benchmarks.occurrence_conditioned_source_minrelax_v3 import (
    _threshold_grid, generate_graph,
)

PROTOCOL = Path("validation/occurrence_conditioned_source_minrelax_v4/protocol_v4.json")
STAR = "bidirectional_star_center_S0"
COMPLETE = "complete_bidirectional_baseline"
CYCLE = "unidirectional_cycle_baseline"


def _digest(obj: object) -> str:
    return sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _source_core_edges(nodes: tuple[str, ...], all_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    src = set(nodes)
    return [
        edge for edge in all_edges
        if edge["source"] in src and edge["target"] in src
    ]


def source_graph(
    generator: dict[str, Any], n_sources: int, density_index: int,
    seed_index: int, regime: str,
) -> dict[str, Any]:
    """Fresh v4 seeds; only the frozen source-core topology differs in pairs."""
    if regime not in (COMPLETE, CYCLE, STAR):
        raise ValueError("unknown source-core topology")
    if not 24 <= seed_index < 40:
        raise ValueError("v4 only permits the independently frozen new seed indices [24,40)")
    g = deepcopy(generator)
    g["random_seeds"] = 40
    parent_regime = COMPLETE if regime == STAR else regime
    raw = generate_graph(g, n_sources, density_index, seed_index, parent_regime)
    if regime == STAR:
        sources = tuple(f"S{i}" for i in range(n_sources))
        noncore = [
            edge for edge in raw["candidate_directed_edges"]
            if edge["source"] not in sources or edge["target"] not in sources
        ]
        star = []
        for index in range(1, n_sources):
            for origin, destination in (("S0", f"S{index}"), (f"S{index}", "S0")):
                star.append({
                    "source": origin,
                    "target": destination,
                    "geographic_km": 8,
                    "environmental_units": 0,
                    "barrier_permission": 0,
                    "hard_unavailable": False,
                })
        raw["candidate_directed_edges"] = noncore + star
    return raw


def _shortest_distances(
    start: str, nodes: tuple[str, ...], edges: list[dict[str, Any]]
) -> dict[str, int]:
    adj: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adj[edge["source"]].append(edge["target"])
    for values in adj.values():
        values.sort()
    dist = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def _source_core_diameter(src: tuple[str, ...], edges: list[dict[str, Any]]) -> int | None:
    core_edges = _source_core_edges(src, edges)
    lengths = []
    for s in src:
        paths = _shortest_distances(s, src, core_edges)
        if len(paths) != len(src):
            return None
        lengths.append(max(paths.values()))
    return max(lengths)


def _point_threshold_edges(
    graph: dict[str, Any], point: tuple[float, ...]
) -> list[dict[str, Any]]:
    base = tuple(graph["baseline"][k] for k in AXES)
    threshold = tuple(base[i] + point[i] for i in range(3))
    return [
        edge for edge in graph["candidate_directed_edges"]
        if not edge["hard_unavailable"]
        and all(float(edge[AXES[i]]) <= threshold[i] for i in range(3))
    ]


def analyze_graph(graph: dict[str, Any], *, require_scc: bool = True) -> dict[str, Any]:
    nodes = tuple(graph["node_ids"])
    positives = tuple(graph["positive_occurrence_ids"])
    src = tuple(x["source_ids"][0] for x in graph["alternative_singleton_sources"])
    base = tuple(float(graph["baseline"][k]) for k in AXES)
    worlds = _threshold_grid(graph["candidate_directed_edges"], base)
    if len(worlds) > graph["max_breakpoint_worlds"]:
        raise ValueError("threshold universe exceeds frozen world budget")
    core = _source_core_edges(src, _point_threshold_edges(graph, (0.0, 0.0, 0.0)))
    diameter = _source_core_diameter(src, core)
    if require_scc and diameter is None:
        raise AssertionError("declared baseline source core is not strongly connected")
    depths: list[dict[str, Any]] = []
    for point in worlds:
        active = _point_threshold_edges(graph, point)
        hs: dict[str, int | None] = {}
        for source in src:
            d = _shortest_distances(source, nodes, active)
            hs[source] = max(d[p] for p in positives) if all(p in d for p in positives) else None
        finite = [v for v in hs.values() if v is not None]
        possible_h = min(finite) if finite else None
        robust_h = max(finite) if len(finite) == len(src) else None
        if require_scc and (possible_h is None) != (robust_h is None):
            raise AssertionError("SCC world has a finite possible horizon and infinite robust horizon")
        width = 0 if possible_h is None else (
            robust_h - possible_h if robust_h is not None else None
        )
        if width is not None and diameter is not None and width > diameter:
            raise AssertionError("source-core diameter upper bound violated")
        depths.append({
            "threshold_increment": list(point),
            "source_minimum_hops": hs,
            "possible_minimum_hops": possible_h,
            "source_robust_minimum_hops": robust_h,
            "ambiguity_hop_width": width,
        })

    # All node weights are synthetic; each threshold world has equal counting weight.
    curve = []
    for H in range(len(nodes)):
        p = sum(
            row["possible_minimum_hops"] is not None
            and row["possible_minimum_hops"] <= H for row in depths
        )
        u = sum(
            row["source_robust_minimum_hops"] is not None
            and row["source_robust_minimum_hops"] <= H for row in depths
        )
        if p < u:
            raise AssertionError("source-robust must imply possible")
        curve.append({
            "hops": H, "possible_worlds": p,
            "source_robust_worlds": u,
            "gap_world_fraction": (p-u)/len(worlds),
        })
    if require_scc:
        area = mean(row["ambiguity_hop_width"] for row in depths)
        curve_integral = sum(row["gap_world_fraction"] for row in curve[:-1])
        if abs(area - curve_integral) > 1e-12:
            raise AssertionError("ambiguity area/hop-width identity failed")
        if curve[-1]["possible_worlds"] != curve[-1]["source_robust_worlds"]:
            raise AssertionError("source core SCC terminal equality failed")
        tight = sum(
            row["ambiguity_hop_width"] == diameter and row["possible_minimum_hops"] is not None
            for row in depths
        )
    else:
        area = None
        curve_integral = None
        tight = None
    nonzero = sum(row["ambiguity_hop_width"] not in (0, None) for row in depths)
    has_interior_increase = any(
        curve[i+1]["gap_world_fraction"] > curve[i]["gap_world_fraction"] + 1e-12
        for i in range(1, len(curve)-2)
    )
    return {
        "node_count": len(nodes), "source_count": len(src),
        "source_core_directed_diameter": diameter,
        "threshold_world_count": len(worlds),
        "per_threshold_minimum_source_hops": depths,
        "gap_by_horizon": curve,
        "ambiguity_area_mean_hops": area,
        "curve_integral_mean_hops": curve_integral,
        "finite_worlds_attaining_source_diameter_bound": tight,
        "worlds_with_positive_ambiguity_hop_width": nonzero,
        "nontrivial_interior_gap_increase": has_interior_increase,
    }


def _compare_native(graph: dict[str, Any], analysis: dict[str, Any], H: int) -> None:
    native = run_source_universe({"universe": graph}, horizon=H)
    expected = analysis["gap_by_horizon"][H]
    if native["worlds_per_source"] != analysis["threshold_world_count"]:
        raise AssertionError("native threshold world count changed")
    if native["possible_compatible_world_count"] != expected["possible_worlds"]:
        raise AssertionError("native possible count disagrees with hop interval")
    if native["source_robust_compatible_world_count"] != expected["source_robust_worlds"]:
        raise AssertionError("native robust count disagrees with hop interval")
    points = [
        tuple(row["threshold_increment"])
        for row in analysis["per_threshold_minimum_source_hops"]
    ]
    p_points = [
        point for point, row in zip(points, analysis["per_threshold_minimum_source_hops"], strict=True)
        if row["possible_minimum_hops"] is not None and row["possible_minimum_hops"] <= H
    ]
    r_points = [
        point for point, row in zip(points, analysis["per_threshold_minimum_source_hops"], strict=True)
        if row["source_robust_minimum_hops"] is not None and row["source_robust_minimum_hops"] <= H
    ]
    if _pareto_min(p_points) != _pareto_min(map(tuple, native["possible_frontier"])):
        raise AssertionError("native possible Pareto frontier differs from hop interval")
    if _pareto_min(r_points) != _pareto_min(map(tuple, native["source_robust_frontier"])):
        raise AssertionError("native source-robust frontier differs from hop interval")


def _broken_source_core_control(generator: dict[str, Any]) -> dict[str, Any]:
    graph = source_graph(generator, 3, 0, 24, CYCLE)
    graph["candidate_directed_edges"] = [
        edge for edge in graph["candidate_directed_edges"]
        if (edge["source"], edge["target"]) != ("S0", "S1")
    ]
    outcome = analyze_graph(graph, require_scc=False)
    full = outcome["per_threshold_minimum_source_hops"][-1]
    result = {
        "source_core_strongly_connected": outcome["source_core_directed_diameter"] is not None,
        "at_full_relaxation_possible_finite": full["possible_minimum_hops"] is not None,
        "at_full_relaxation_robust_infinite": full["source_robust_minimum_hops"] is None,
        "terminal_robust_but_possible": (
            outcome["gap_by_horizon"][-1]["possible_worlds"]
            > outcome["gap_by_horizon"][-1]["source_robust_worlds"]
        ),
    }
    if result != {
        "source_core_strongly_connected": False,
        "at_full_relaxation_possible_finite": True,
        "at_full_relaxation_robust_infinite": True,
        "terminal_robust_but_possible": True,
    }:
        raise AssertionError("broken-source-core negative-control failed")
    return result


def run_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    new = protocol["newly_frozen_generator"]
    root = json.loads(Path("validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json").read_text(encoding="utf-8"))
    generator = root["generator"]
    graph_summaries: list[dict[str, Any]] = []
    paired = {}
    native = 0
    for ns in new["n_sources"]:
        for di in new["density_indices"]:
            for si in range(new["seed_index_start_inclusive"], new["seed_index_end_exclusive"]):
                triad = []
                for regime in new["source_core_regimes"]:
                    graph = source_graph(generator, ns, di, si, regime)
                    result = analyze_graph(graph)
                    if si == new["seed_index_start_inclusive"]:
                        for H in sorted({1, ns-1, ns+new["n_targets"]-1}):
                            _compare_native(graph, result, H)
                            native += 1
                    triad.append((regime, graph, result))
                    row = {
                        "n_sources": ns, "density_index": di, "seed_index": si,
                        "source_core": regime,
                        "optional_edge_digest": graph["optional_edge_digest"],
                        "worlds": result["threshold_world_count"],
                        "diameter": result["source_core_directed_diameter"],
                        "ambiguity_area_mean_hops": result["ambiguity_area_mean_hops"],
                        "tight_worlds": result["finite_worlds_attaining_source_diameter_bound"],
                        "positive_width_worlds": result["worlds_with_positive_ambiguity_hop_width"],
                        "nontrivial_interior_gap_increase": result["nontrivial_interior_gap_increase"],
                        "gap_by_horizon": result["gap_by_horizon"],
                    }
                    graph_summaries.append(row)
                    paired[ns,di,si,regime] = row
                if len({v["optional_edge_digest"] for _,v,_ in triad}) != 1:
                    raise AssertionError("paired optional graph differs by source-core regime")
                if len({a["threshold_world_count"] for _,_,a in triad}) != 1:
                    raise AssertionError("paired threshold universe differs by source-core regime")
    comparisons = []
    for ns in new["n_sources"]:
        for di in new["density_indices"]:
            for si in range(new["seed_index_start_inclusive"], new["seed_index_end_exclusive"]):
                cycle = paired[ns,di,si,CYCLE]
                star = paired[ns,di,si,STAR]
                complete = paired[ns,di,si,COMPLETE]
                comparisons.append({
                    "n_sources": ns, "density_index": di, "seed_index": si,
                    "cycle_area": cycle["ambiguity_area_mean_hops"],
                    "star_area": star["ambiguity_area_mean_hops"],
                    "complete_area": complete["ambiguity_area_mean_hops"],
                    "cycle_minus_star": cycle["ambiguity_area_mean_hops"]-star["ambiguity_area_mean_hops"],
                    "cycle_minus_complete": cycle["ambiguity_area_mean_hops"]-complete["ambiguity_area_mean_hops"],
                })
    if len(graph_summaries) != 192 or len(comparisons) != 64 or native != 36:
        raise AssertionError("predeclared source generality denominator violated")
    contrasts = [x["cycle_minus_star"] for x in comparisons]
    counts = {
        "positive": sum(x>0 for x in contrasts),
        "tied": sum(x==0 for x in contrasts),
        "negative": sum(x<0 for x in contrasts),
    }
    result = {
        "schema":"eog.source_mrr_horizon_identifiability_v4.result",
        "protocol_commit":"2828c38d1db8ef9f69b25e5fe5d69ac39983a0be",
        "pre_score_protocol_amendment_commit":"0dca8a6f01c5ec060bbe30cf52edb8bc1b5cbf6e",
        "status":"SYNTHETIC_ONLY_NOT_ECOLOGICAL_FIELD_VALIDATION",
        "verdicts":{
            "G1_horizon_partition_identity":"EXACT_CONTRACT_PASS",
            "G2_SCC_diameter_bound":"EXACT_CONTRACT_PASS",
            "G3_integrated_gap_identity_and_native_audit":"EXACT_CONTRACT_PASS",
            "G4_disconnected_source_core_negative_control":"NEGATIVE_CONTROL_PASS",
            "G5_cycle_area_greater_than_star":(
                "SUPPORTED_WITHIN_PREDECLARED_NEW_SEEDS"
                if mean(contrasts)>0 else "REFUTED_OR_NOT_SUPPORTED"
            ),
            "G6_nonlinear_horizon_gap_behavior":"DESCRIPTIVE_ONLY",
            "G7_fixed_pair_source_universe":"INPUT_INTEGRITY_PASS",
        },
        "summary":{
            "graphs":len(graph_summaries),
            "paired_graph_triples":len(comparisons),
            "native_v2_horizon_checks":native,
            "diameter_bound_violations":0,
            "integrated_gap_identity_violations":0,
            "mean_cycle_minus_star_ambiguity_area_hops":mean(contrasts),
            "cycle_minus_star_sign_counts":counts,
            "mean_cycle_area_hops":mean(x["cycle_area"] for x in comparisons),
            "mean_star_area_hops":mean(x["star_area"] for x in comparisons),
            "mean_complete_area_hops":mean(x["complete_area"] for x in comparisons),
            "interior_rising_gap_graph_count":sum(x["nontrivial_interior_gap_increase"] for x in graph_summaries),
            "tightness_worlds":sum(x["tight_worlds"] for x in graph_summaries),
            "worlds_with_positive_hop_ambiguity":sum(x["positive_width_worlds"] for x in graph_summaries),
            "total_threshold_worlds":sum(x["worlds"] for x in graph_summaries),
        },
        "broken_source_core_negative_control":_broken_source_core_control(generator),
        "primary_paired_graphs":comparisons,
        "graph_horizon_summaries":graph_summaries,
        "independent_ecological_replications":0,
        "new_EOG_WF_empirical_endpoints":0,
    }
    result["sha256_without_self_hash"]=_digest(result)
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    result=run_protocol(protocol)
    if args.output is not None:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    else:
        print(json.dumps({"verdicts":result["verdicts"],"summary":result["summary"],
            "negative_control":result["broken_source_core_negative_control"],
            "sha256":result["sha256_without_self_hash"]},indent=2,sort_keys=True))


if __name__=="__main__":
    main()
