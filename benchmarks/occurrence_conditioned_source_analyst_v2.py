#!/usr/bin/env python3
"""Alternative source and analytical-graph sensitivity for EOG minimum-relaxation.

Post-closure *synthetic* research only, with source/graph variants fixed in
validation/occurrence_conditioned_source_analyst_v2/protocol_v2.json BEFORE scoring.
For each hypothesis this calls the original EOG finite reconstruction / Pareto
frontier (via the v1 benchmark); a shared breakpoint lattice is independently
checked against bounded graph BFS. No public API or empirical endpoint is added.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
import math
from pathlib import Path
import runpy
from typing import Sequence


def _engine() -> dict[str, object]:
    return runpy.run_path(
        str(Path(__file__).resolve().parent / "occurrence_conditioned_minrelax_v1.py")
    )


def _nondominated(rows: Sequence[tuple[float, float, float]]) -> list[list[float]]:
    """Generic finite 3-axis minima for comparisons, not a new EOG core API."""
    vectors = set(rows)
    retained = []
    for v in sorted(vectors):
        if not any(
            u != v and all(a <= b for a, b in zip(u, v, strict=True))
            for u in vectors
        ):
            retained.append(list(v))
    return retained


def _run_matrix(
    *,
    source_hypotheses: Sequence[str] = ("A", "B"),
    analyst_variants: Sequence[str] = ("soft_crossing", "hard_sea_mask"),
    reverse_edges: bool = False,
) -> dict[str, object]:
    m = _engine()
    Edge = m["DirectedRequirement"]
    infer = m["infer_required_relaxations"]
    bfs = m["_paths"]
    baseline = (10.0, 1.0, 0.0)
    nodes = ("A", "B", "X", "Y")
    positive_nodes = ("A", "B")
    edges = tuple(m["_example_requirements"]()) + (Edge("B", "A", 25.0, 0.0),)
    if reverse_edges:
        edges = tuple(reversed(edges))
    sources = tuple(source_hypotheses)
    variants = tuple(analyst_variants)
    if set(sources) != {"A", "B"} or len(sources) != 2:
        raise ValueError("source hypotheses must be the two predeclared alternatives A/B")
    if set(variants) != {"soft_crossing", "hard_sea_mask"} or len(variants) != 2:
        raise ValueError("only the two preregistered graph variants are admissible")
    edges_for_variant = {
        "soft_crossing": tuple(edges),
        "hard_sea_mask": tuple(
            Edge(edge.source, edge.target, edge.geographic_km, edge.environmental_units,
                 edge.barrier_permission, hard_unavailable=(edge.source, edge.target) in {
                     ("A", "Y"), ("Y", "B")
                 })
            for edge in edges
        ),
    }
    axes = (
        tuple(sorted({baseline[0]} | {e.geographic_km for e in edges if e.geographic_km > baseline[0]})),
        tuple(sorted({baseline[1]} | {e.environmental_units for e in edges if e.environmental_units > baseline[1]})),
        tuple(sorted({baseline[2]} | {float(e.barrier_permission) for e in edges if e.barrier_permission > baseline[2]})),
    )
    thresholds = tuple(product(*axes))
    if len(thresholds) != 12:
        raise AssertionError("predeclared 3 x 2 x 2 threshold grid was altered")

    details = []
    per_hypothesis = {}
    for variant in sorted(variants):
        for source in sorted(sources):
            result = infer(
                node_ids=nodes,
                requirements=edges_for_variant[variant],
                source_ids=(source,),
                observed_positive_ids=positive_nodes,
                baseline=baseline,
                max_steps=3,
                max_worlds=128,
            )
            frontier = tuple(tuple(
                row["relaxations"][name]
                for name in ("geographic_km", "environmental_units", "barrier_permission")
            ) for row in result["frontier"])
            per_hypothesis[f"{variant}__source_{source}"] = {
                "finite_breakpoint_worlds": result["world_count"],
                "native_compatible_worlds": result["compatible_world_count"],
                "source_specific_frontier": [list(v) for v in sorted(frontier)],
                "eog_reconstruction_fingerprint": result["eog_reconstruction_fingerprint"],
                "eog_frontier_fingerprint": result["eog_frontier_fingerprint"],
                "independent_eog_bfs_equal": result["independent_bfs_agrees_for_every_world"],
            }
            for threshold in thresholds:
                increment = tuple(threshold[i] - baseline[i] for i in range(3))
                predicted_by_native_frontier = any(
                    all(f[i] <= increment[i] for i in range(3)) for f in frontier
                )
                active = tuple(
                    edge for edge in edges_for_variant[variant] if not edge.hard_unavailable
                    and edge.geographic_km <= threshold[0]
                    and edge.environmental_units <= threshold[1]
                    and edge.barrier_permission <= threshold[2]
                )
                paths = bfs(nodes, active, (source,), 3)
                independently_reachable = all(node in paths for node in positive_nodes)
                if predicted_by_native_frontier != independently_reachable:
                    raise AssertionError(
                        f"frontier/BFS mismatch at {variant}/{source}/{threshold}"
                    )
                details.append({
                    "variant": variant,
                    "source": source,
                    "threshold": threshold,
                    "increment": increment,
                    "feasible": independently_reachable,
                })
    by_level = {}
    n_hypotheses = len(sources) * len(variants)
    for threshold in thresholds:
        level = [item for item in details if item["threshold"] == threshold]
        if len(level) != n_hypotheses:
            raise AssertionError("incomplete source x graph universe")
        supported = sum(item["feasible"] for item in level)
        key = "g" + str(threshold[0]) + "_e" + str(threshold[1]) + "_b" + str(threshold[2])
        by_level[key] = {
            "threshold": list(threshold),
            "increment": [threshold[i]-baseline[i] for i in range(3)],
            "compatible_hypothesis_count": supported,
            "exists_any_hypothesis": supported > 0,
            "compatible_all_hypotheses": supported == n_hypotheses,
            "compatible_both_sources_in_soft_graph": all(
                item["feasible"] for item in level if item["variant"] == "soft_crossing"
            ),
            "source_analyst_unresolved": 0 < supported < n_hypotheses,
        }

    possible = _nondominated([
        tuple(r["increment"]) for r in by_level.values()
        if r["exists_any_hypothesis"]
    ])
    universal = _nondominated([
        tuple(r["increment"]) for r in by_level.values()
        if r["compatible_all_hypotheses"]
    ])
    universal_soft = _nondominated([
        tuple(r["increment"]) for r in by_level.values()
        if r["compatible_both_sources_in_soft_graph"]
    ])
    # A true threshold never becomes false after any coordinate is relaxed,
    # conditional on a fixed network, source and observation set.
    monotonicity_checks = 0
    for a in details:
        for b in details:
            if a["variant"] != b["variant"] or a["source"] != b["source"]:
                continue
            if all(x <= y for x, y in zip(a["threshold"], b["threshold"], strict=True)):
                monotonicity_checks += 1
                if a["feasible"] and not b["feasible"]:
                    raise AssertionError("edge-inclusion monotonicity violated")
    return {
        "schema_version": 1,
        "claim_boundary": "predeclared 2-source x 2-analytic-graph synthetic alternatives; no field source identification",
        "source_hypotheses": sorted(sources),
        "analyst_variants": sorted(variants),
        "baseline": list(baseline),
        "shared_absolute_threshold_axes": [list(axis) for axis in axes],
        "threshold_worlds": len(thresholds),
        "source_graph_hypotheses": n_hypotheses,
        "tested_hypothesis_threshold_pairs": len(details),
        "per_hypothesis": per_hypothesis,
        "possible_at_least_one_hypothesis_frontier": possible,
        "compatible_every_hypothesis_frontier": universal,
        "compatible_both_sources_soft_graph_frontier": universal_soft,
        "possible_threshold_count": sum(r["exists_any_hypothesis"] for r in by_level.values()),
        "universal_threshold_count": sum(r["compatible_all_hypotheses"] for r in by_level.values()),
        "source_analyst_unresolved_threshold_count": sum(r["source_analyst_unresolved"] for r in by_level.values()),
        "monotone_ordered_pairs_checked": monotonicity_checks,
        "independent_bfs_agreed_with_eog_for_all_pairs": True,
        "hard_graph_barrier_only_rescue_never_compatible_for_source_A": not any(
            row["feasible"] for row in details
            if row["variant"] == "hard_sea_mask" and row["source"] == "A"
            and row["increment"] == (0.0, 0.0, 1.0)
        ),
        "exact_finite_world_coverage": True,
        "threshold_results": [by_level[k] for k in sorted(by_level)],
    }


def run_benchmark() -> dict[str, object]:
    return _run_matrix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_benchmark()
    content = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(content, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
