#!/usr/bin/env python3
"""Exact observed-positive constraint-relaxation benchmark for frozen finite graphs.

Research-only: derives edge breakpoints from declared requirements, reuses EOG's
native FiniteWorld inverse reconstruction and Pareto frontier, and checks every
compatibility decision against independent bounded directed-graph traversal.
This is NOT a new public API, calibrated dispersal law, or historical inference.
"""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from itertools import product
import json
import math
from pathlib import Path
from typing import Sequence

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    minimum_relaxation_frontier,
    reconstruct_compatible_worlds,
)


@dataclass(frozen=True)
class DirectedRequirement:
    source: str
    target: str
    geographic_km: float
    environmental_units: float
    barrier_permission: float = 0.0
    hard_unavailable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("edge source must be a nonempty ID")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("edge target must be a nonempty ID")
        if self.source == self.target:
            raise ValueError("self transitions are not accepted")
        for label in ("geographic_km", "environmental_units"):
            value = getattr(self, label)
            if isinstance(value, bool) or not math.isfinite(float(value)) or value < 0:
                raise ValueError(f"{label} must be finite and nonnegative")
        if self.barrier_permission not in (0, 1):
            raise ValueError("barrier_permission is categorical: 0 or 1")
        if not isinstance(self.hard_unavailable, bool):
            raise ValueError("hard_unavailable must be explicitly boolean")


def _validated_ids(ids: Sequence[str], label: str) -> tuple[str, ...]:
    values = tuple(ids)
    if not values or any(not isinstance(s, str) or not s.strip() for s in values):
        raise ValueError(f"{label} requires nonempty string IDs")
    if len(set(values)) != len(values):
        raise ValueError(f"{label} contains duplicate IDs")
    return values


def _validate_baseline(baseline: tuple[float, float, float]) -> None:
    if len(baseline) != 3:
        raise ValueError("baseline needs geographic, environmental and barrier limits")
    for value in baseline:
        if isinstance(value, bool) or not math.isfinite(float(value)) or value < 0:
            raise ValueError("baseline limits must be finite and nonnegative")
    if baseline[2] not in (0, 1):
        raise ValueError("baseline barrier permission must be categorical 0 or 1")


def _paths(
    node_ids: tuple[str, ...],
    active_edges: Sequence[DirectedRequirement],
    source_ids: tuple[str, ...],
    max_steps: int,
) -> dict[str, tuple[str, ...]]:
    """Independent, deterministic unweighted directed reachability witness."""
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in active_edges:
        adjacency[edge.source].append(edge.target)
    for targets in adjacency.values():
        targets.sort()
    queue = deque((source_id, (source_id,)) for source_id in sorted(source_ids))
    paths = {source_id: (source_id,) for source_id in source_ids}
    while queue:
        node_id, path = queue.popleft()
        if len(path) - 1 == max_steps:
            continue
        for target in adjacency[node_id]:
            if target not in paths:
                next_path = path + (target,)
                paths[target] = next_path
                queue.append((target, next_path))
    return paths


def infer_required_relaxations(
    *,
    node_ids: Sequence[str],
    requirements: Sequence[DirectedRequirement],
    source_ids: Sequence[str],
    observed_positive_ids: Sequence[str],
    baseline: tuple[float, float, float],
    max_steps: int,
    max_worlds: int = 512,
) -> dict[str, object]:
    """Find minimum required relaxations on exact edge-derived breakpoints.

    All reported necessity is conditional on the frozen candidate edge universe,
    externally declared sources, observed positives and bounded propagation depth.
    A route witness is a constructed feasible path, never a historical trajectory.
    """
    nodes = _validated_ids(node_ids, "node_ids")
    sources = _validated_ids(source_ids, "source_ids")
    positives = _validated_ids(observed_positive_ids, "observed_positive_ids")
    if not set(sources).issubset(positives) or not set(positives).issubset(nodes):
        raise ValueError("sources must be observed positives and positives within node IDs")
    if len(positives) < 2 or not (set(positives) - set(sources)):
        raise ValueError("at least one non-source positive target is required")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if isinstance(max_worlds, bool) or not isinstance(max_worlds, int) or max_worlds < 1:
        raise ValueError("max_worlds must be a positive integer")
    _validate_baseline(baseline)

    edges = tuple(sorted(requirements, key=lambda e: (e.source, e.target)))
    pairs = [(e.source, e.target) for e in edges]
    if len(set(pairs)) != len(pairs):
        raise ValueError("directed edge requirements must have unique endpoints")
    if any(e.source not in nodes or e.target not in nodes for e in edges):
        raise ValueError("edge endpoint outside declared node set")

    available = tuple(edge for edge in edges if not edge.hard_unavailable)
    axes = (
        tuple(sorted({baseline[0]} | {e.geographic_km for e in available if e.geographic_km > baseline[0]})),
        tuple(sorted({baseline[1]} | {e.environmental_units for e in available if e.environmental_units > baseline[1]})),
        tuple(sorted({baseline[2]} | {float(e.barrier_permission) for e in available if e.barrier_permission > baseline[2]})),
    )
    count = math.prod(len(values) for values in axes)
    if count > max_worlds:
        raise ValueError(f"finite breakpoint universe requires {count} worlds > max_worlds={max_worlds}; fail closed")

    index = {node_id: position for position, node_id in enumerate(nodes)}
    worlds: list[FiniteWorld] = []
    active_by_id: dict[str, tuple[DirectedRequirement, ...]] = {}
    thresholds: dict[str, tuple[float, float, float]] = {}
    for gi, ei, bi in product(*(range(len(axis)) for axis in axes)):
        g, e, b = axes[0][gi], axes[1][ei], axes[2][bi]
        world_id = f"g{gi:03d}_e{ei:03d}_b{bi:03d}"
        active = tuple(
            edge for edge in available
            if edge.geographic_km <= g and edge.environmental_units <= e
            and edge.barrier_permission <= b
        )
        operator = build_dynamic_transition_operator(
            nodes,
            tuple(
                DynamicReachabilityEdge(
                    source=index[edge.source],
                    target=index[edge.target],
                    geographic_support=1.0,
                    environmental_support=1.0,
                    barrier_support=1.0,
                )
                for edge in active
            ),
            loss_support=1.0,
        )
        worlds.append(FiniteWorld(
            world_id=world_id,
            operator=operator,
            source_ids=tuple(sources),
            geographic_relaxation=g - baseline[0],
            environmental_relaxation=e - baseline[1],
            barrier_relaxation=b - baseline[2],
        ))
        active_by_id[world_id] = active
        thresholds[world_id] = (g, e, b)

    reconstruction = reconstruct_compatible_worlds(
        worlds, positives, max_steps=max_steps, support_tolerance=0.0
    )
    by_eog = {row.world_id: row.compatible for row in reconstruction.world_results}
    witness_by_id: dict[str, dict[str, tuple[str, ...]]] = {}
    for world in worlds:
        paths = _paths(nodes, active_by_id[world.world_id], sources, max_steps)
        independently_compatible = all(target in paths for target in positives)
        if independently_compatible != by_eog[world.world_id]:
            raise AssertionError(f"native EOG/BFS compatibility disagreement at {world.world_id}")
        witness_by_id[world.world_id] = {
            target: paths[target] for target in positives if target not in sources and target in paths
        }

    frontier = minimum_relaxation_frontier(reconstruction, worlds)
    rows = []
    for point in frontier.points:
        g, e, b = thresholds[point.world_id]
        rows.append({
            "world_id": point.world_id,
            "relaxations": {
                "geographic_km": point.geographic_relaxation,
                "environmental_units": point.environmental_relaxation,
                "barrier_permission": point.barrier_relaxation,
            },
            "absolute_limits": {"geographic_km": g, "environmental_units": e, "barrier_permission": b},
            "witness_paths_not_historical": {
                target: list(path) for target, path in witness_by_id[point.world_id].items()
            },
        })

    axis_minima = None
    axis_minima_jointly_feasible = None
    if rows:
        axis_minima = {
            axis: min(row["relaxations"][axis] for row in rows)
            for axis in ("geographic_km", "environmental_units", "barrier_permission")
        }
        critical = tuple(baseline[i] + tuple(axis_minima.values())[i] for i in range(3))
        active = [edge for edge in available if all((
            edge.geographic_km <= critical[0],
            edge.environmental_units <= critical[1],
            edge.barrier_permission <= critical[2],
        ))]
        paths = _paths(nodes, active, sources, max_steps)
        axis_minima_jointly_feasible = all(target in paths for target in positives)
    status = (
        "baseline_compatible" if "g000_e000_b000" in reconstruction.compatible_world_ids
        else "rescued_by_declared_relaxation" if rows
        else "no_feasible_world_within_declared_graph_and_step_limit"
    )
    return {
        "schema_version": 1,
        "claim_boundary": "exact declared-finite-graph necessity only; not observed dispersal history",
        "status": status,
        "observed_positive_ids": list(positives),
        "declared_source_ids": list(sources),
        "baseline_limits": dict(zip(("geographic_km", "environmental_units", "barrier_permission"), baseline)),
        "max_steps": max_steps,
        "world_count": count,
        "compatible_world_count": len(reconstruction.compatible_world_ids),
        "candidate_breakpoint_count_by_axis": [len(axis) for axis in axes],
        "frontier": rows,
        "coordinatewise_minima": axis_minima,
        "coordinatewise_minima_jointly_feasible": axis_minima_jointly_feasible,
        "independent_bfs_agrees_for_every_world": True,
        "coverage_certificate": "all_declared_finite_edge_breakpoints_enumerated_within_fixed_candidate_graph",
        "eog_reconstruction_fingerprint": reconstruction.fingerprint,
        "eog_frontier_fingerprint": frontier.fingerprint,
    }


def _example_requirements() -> tuple[DirectedRequirement, ...]:
    return (
        DirectedRequirement("A", "X", 8.0, 2.0),
        DirectedRequirement("X", "B", 8.0, 2.0),
        DirectedRequirement("A", "B", 30.0, 0.0),
        DirectedRequirement("A", "Y", 7.0, 0.0, 1.0),
        DirectedRequirement("Y", "B", 7.0, 0.0, 1.0),
    )


def run_benchmark() -> dict[str, object]:
    common = {
        "source_ids": ("A",),
        "baseline": (10.0, 1.0, 0.0),
        "max_steps": 3,
    }
    primary = infer_required_relaxations(
        node_ids=("A", "B", "X", "Y"),
        requirements=_example_requirements(),
        observed_positive_ids=("A", "B"),
        **common,
    )
    added_positive = infer_required_relaxations(
        node_ids=("A", "B", "C", "X", "Y"),
        requirements=_example_requirements() + (DirectedRequirement("A", "C", 15.0, 1.0),),
        observed_positive_ids=("A", "B", "C"),
        **common,
    )
    closed = infer_required_relaxations(
        node_ids=("A", "B"),
        requirements=(DirectedRequirement("A", "B", 20.0, 2.0, 1.0, hard_unavailable=True),),
        observed_positive_ids=("A", "B"),
        **common,
    )
    return {
        "schema_version": 1,
        "claim_boundary": "synthetic conditional graph inversion; not empirical ecological inference",
        "primary": primary,
        "additional_positive": added_positive,
        "hard_unavailable_stop": closed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_benchmark()
    content = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(content, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
