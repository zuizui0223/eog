#!/usr/bin/env python3
"""Synthetic source-uncertain minimum required relaxation (MRR), research-only v2.

Use the *existing* EOG-v1 occurrence-conditioned finite-world reconstruction
for each frozen singleton source. Independently enumerate the same threshold
lattice with a separate bounded directed reachability algorithm, then verify
source-existential / source-universal Pareto fronts and the antichain join rule.

Neither a surviving source nor a displayed path is observed natural ancestry.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
from typing import Iterable, Mapping

from benchmarks.occurrence_conditioned_minrelax_v1 import (
    DirectedRequirement,
    infer_required_relaxations,
)

AXES = ("geographic_km", "environmental_units", "barrier_permission")
Point = tuple[float, float, float]
DEFAULT_PROTOCOL = Path("validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json")


def _pareto_min(points: Iterable[Point]) -> tuple[Point, ...]:
    """Return the unique non-dominated antichain in an axiswise ordered grid."""
    unique = sorted(set(points))
    return tuple(
        x for x in unique
        if not any(
            all(y[i] <= x[i] for i in range(3))
            and any(y[i] < x[i] for i in range(3))
            for y in unique
        )
    )


def _source_reachable(
    source: str, active: tuple[DirectedRequirement, ...], horizon: int
) -> set[str]:
    """Independent set-BFS (the parent benchmark separately audits EOG BFS)."""
    reached = {source}
    frontier = {source}
    for _ in range(horizon):
        extension = {edge.target for edge in active if edge.source in frontier}
        extension.difference_update(reached)
        reached.update(extension)
        frontier = extension
        if not frontier:
            break
    return reached


def _required_edges(
    spec: Mapping[str, object],
    *,
    reverse_edges: bool,
    make_hard_unavailable: tuple[str, str] | None,
) -> tuple[DirectedRequirement, ...]:
    original = spec["universe"]["candidate_directed_edges"]
    edges = []
    found_hard = False
    for row in original:
        key = (row["source"], row["target"])
        modified = dict(row)
        if key == make_hard_unavailable:
            if modified["hard_unavailable"]:
                raise ValueError("requested edge is already hard unavailable")
            modified["hard_unavailable"] = True
            found_hard = True
        edges.append(DirectedRequirement(**modified))
    if make_hard_unavailable is not None and not found_hard:
        raise ValueError("hard-unavailable edge was not in the frozen graph")
    if reverse_edges:
        edges.reverse()
    return tuple(edges)


def _breakpoints(
    edges: tuple[DirectedRequirement, ...], baseline: Point, max_worlds: int
) -> tuple[Point, ...]:
    active = [edge for edge in edges if not edge.hard_unavailable]
    axes = tuple(
        sorted({baseline[i]} | {
            float(getattr(edge, AXES[i]))
            for edge in active if float(getattr(edge, AXES[i])) > baseline[i]
        })
        for i in range(3)
    )
    count = len(axes[0]) * len(axes[1]) * len(axes[2])
    if count > max_worlds:
        raise ValueError(f"finite breakpoint universe requires {count} worlds > max_worlds={max_worlds}")
    return tuple(
        tuple(round(value - baseline[i], 10) for i, value in enumerate(levels))
        for levels in product(*axes)
    )


def run_source_universe(
    spec: Mapping[str, object],
    *,
    horizon: int,
    source_order: tuple[str, ...] | None = None,
    reverse_edges: bool = False,
    make_hard_unavailable: tuple[str, str] | None = None,
    max_worlds: int | None = None,
) -> dict[str, object]:
    """Calculate possible and source-universal MRR frontiers on one fixed graph.

    All candidate source hypotheses use identical positive evidence, candidate
    edges, units, baseline, breakpoint lattice and horizon. Source hypotheses
    remain *declared alternatives*, not empirically inferred origins.
    """
    universe = spec["universe"]
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    nodes = tuple(universe["node_ids"])
    positives = tuple(universe["positive_occurrence_ids"])
    baseline = tuple(float(universe["baseline"][axis]) for axis in AXES)
    variants = {row["id"]: tuple(row["source_ids"]) for row in universe["alternative_singleton_sources"]}
    if len(variants) != len(universe["alternative_singleton_sources"]):
        raise ValueError("source variants must have unique IDs")
    if any(len(ids) != 1 or ids[0] not in positives for ids in variants.values()):
        raise ValueError("source variants must be singleton observed positives")
    if not set(positives).issubset(nodes) or len(positives) < 2:
        raise ValueError("observed positives must be in the node universe")
    if source_order is not None and set(source_order) != set(variants):
        raise ValueError("source order must cover exactly the frozen candidate sources")
    source_order = tuple(sorted(variants))
    edges = _required_edges(
        spec,
        reverse_edges=reverse_edges,
        make_hard_unavailable=make_hard_unavailable,
    )
    budget = universe["max_breakpoint_worlds"] if max_worlds is None else max_worlds
    grid = _breakpoints(edges, baseline, budget)
    independent_feasible: dict[str, set[Point]] = {}
    native_counts: dict[str, int] = {}
    native_frontiers: dict[str, tuple[Point, ...]] = {}
    native_fingerprints: dict[str, str] = {}
    for source_id in source_order:
        native = infer_required_relaxations(
            node_ids=nodes,
            requirements=edges,
            source_ids=variants[source_id],
            observed_positive_ids=positives,
            baseline=baseline,
            max_steps=horizon,
            max_worlds=budget,
        )
        if native["world_count"] != len(grid):
            raise AssertionError("native EOG and independent grid sizes differ")
        viable: set[Point] = set()
        for point in grid:
            absolute = tuple(baseline[i] + point[i] for i in range(3))
            active_edges = tuple(
                edge for edge in edges
                if not edge.hard_unavailable
                and all(float(getattr(edge, AXES[i])) <= absolute[i] for i in range(3))
            )
            if set(positives).issubset(_source_reachable(variants[source_id][0], active_edges, horizon)):
                viable.add(point)
        direct_frontier = _pareto_min(viable)
        native_frontier = _pareto_min(
            tuple(float(row["relaxations"][axis]) for axis in AXES)
            for row in native["frontier"]
        )
        if len(viable) != native["compatible_world_count"] or direct_frontier != native_frontier:
            raise AssertionError(f"native EOG / independent source-world disagreement for {source_id}")
        independent_feasible[source_id] = viable
        native_counts[source_id] = native["compatible_world_count"]
        native_frontiers[source_id] = direct_frontier
        native_fingerprints[source_id] = native["eog_reconstruction_fingerprint"]

    all_possible = set().union(*independent_feasible.values())
    all_robust = set.intersection(*(set(values) for values in independent_feasible.values()))
    frontier_possible = _pareto_min(all_possible)
    frontier_robust = _pareto_min(all_robust)
    frontiers = [native_frontiers[k] for k in source_order]
    antichain_possible = _pareto_min(point for row in frontiers for point in row)
    antichain_robust = _pareto_min(
        tuple(max(row[i] for row in choices) for i in range(3))
        for choices in product(*frontiers)
    ) if all(frontiers) else ()
    if frontier_possible != antichain_possible or frontier_robust != antichain_robust:
        raise AssertionError("antichain union/join theorem failed")
    naïve_intersection = set.intersection(*(set(rows) for rows in frontiers))
    return {
        "schema": "eog.source_uncertain_minrelax.known_truth_v2",
        "status": (
            "source_robust_feasible"
            if all_robust else "no_source_robust_world_within_declared_source_and_graph_universe"
        ),
        "worlds_per_source": len(grid),
        "source_world_pairs": len(grid) * len(variants),
        "horizon_steps_not_years": horizon,
        "source_ids": list(source_order),
        "compatible_world_counts_by_source": native_counts,
        "source_frontiers": {
            k: [list(p) for p in native_frontiers[k]] for k in source_order
        },
        "possible_compatible_world_count": len(all_possible),
        "source_robust_compatible_world_count": len(all_robust),
        "possible_frontier": [list(p) for p in frontier_possible],
        "source_robust_frontier": [list(p) for p in frontier_robust],
        "naive_source_frontier_intersection": [list(p) for p in sorted(naïve_intersection)],
        "native_reconstruction_fingerprint_by_source": native_fingerprints,
        "independent_bfs_and_antichain_join_both_verified": True,
        "frozen_source_hypotheses_are_not_natal_origin_observations": True,
        "claim_boundary": (
            "complete finite declared source+edge+threshold+horizon lattice only; "
            "no historical-source, movement or biological impossibility inference"
        ),
    }


def run_protocol(spec: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema": "eog.source_uncertain_minrelax.known_truth_v2_result",
        "protocol_base_main_sha": spec["base_main_sha"],
        "H1": run_source_universe(spec, horizon=1),
        "H2": run_source_universe(spec, horizon=2),
        "hard_edge_boundary": run_source_universe(
            spec, horizon=1, make_hard_unavailable=("C", "T")
        ),
        "new_eog_wf_endpoints": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = run_protocol(spec)
    content = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(content, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
