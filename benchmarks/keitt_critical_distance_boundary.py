#!/usr/bin/env python3
"""Negative novelty boundary against Keitt-style critical distance connectivity.

Keitt, Urban & Milne (1997, Conservation Ecology 1:4) represented habitat patches as a
graph and varied a patch-distance connection threshold to resolve connectivity across
scales.  In a purely one-dimensional geographic relaxation problem, EOG's declared
water-level / basin-merge diagnostic should reduce to the same critical threshold.

This benchmark intentionally expects equality.  It therefore removes the following
from any EOG novelty claim:

- varying a geographic connection threshold;
- detecting the first threshold at which two patch components connect;
- recovering a stepping-stone-mediated critical dispersal distance.

The prospective EOG contribution must be sought beyond this special case: multiple
geographic/environmental/barrier relaxation axes, compatible-world sets, analyst-choice
uncertainty, underidentification, and explicit finite-universe certificates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    build_monotone_relaxation_family,
    infer_basin_merge,
)


PATCH_X = {"A": 0.0, "B": 4.0, "C": 10.0}
PAIR_DISTANCE = {
    tuple(sorted((left, right))): abs(PATCH_X[left] - PATCH_X[right])
    for left in PATCH_X
    for right in PATCH_X
    if left != right
}


def _neighbors(threshold: float) -> dict[str, set[str]]:
    graph = {node_id: set() for node_id in PATCH_X}
    for (left, right), distance in PAIR_DISTANCE.items():
        if distance <= threshold:
            graph[left].add(right)
            graph[right].add(left)
    return graph


def _connected(threshold: float, source: str = "A", target: str = "C") -> bool:
    graph = _neighbors(threshold)
    seen = {source}
    stack = [source]
    while stack:
        node = stack.pop()
        if node == target:
            return True
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return target in seen


def _critical_distance() -> float:
    levels = sorted({0.0, *PAIR_DISTANCE.values()})
    for level in levels:
        if _connected(level):
            return level
    raise RuntimeError("declared patch graph never connects source and target")


def _operator_at_threshold(threshold: float):
    node_ids = tuple(PATCH_X)
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    edges = []
    for (left, right), distance in sorted(PAIR_DISTANCE.items()):
        if distance <= threshold:
            for source, target in ((left, right), (right, left)):
                edges.append(
                    DynamicReachabilityEdge(
                        source=index[source],
                        target=index[target],
                        geographic_support=1.0,
                    )
                )
    return build_dynamic_transition_operator(node_ids, edges, loss_support=1.0)


def _eog_family():
    levels = (0.0, 4.0, 6.0, 10.0)
    level_worlds = {}
    for level in levels:
        world = FiniteWorld(
            world_id=f"distance_{level:g}",
            operator=_operator_at_threshold(level),
            source_ids=("A",),
            geographic_relaxation=level,
            analytical_variant="reference",
        )
        level_worlds[level] = {"reference": world}
    return build_monotone_relaxation_family("keitt_distance_threshold", level_worlds)


def run_keitt_critical_distance_boundary():
    critical = _critical_distance()
    family = _eog_family()
    basin = infer_basin_merge(
        family,
        {"source": ("A",), "target": ("C",)},
        max_steps=2,
    )
    direct_distance = PAIR_DISTANCE[("A", "C")]
    stepping_edges = [
        [left, right, distance]
        for (left, right), distance in sorted(PAIR_DISTANCE.items())
        if distance <= critical
    ]

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "Keitt-style patch-distance threshold / percolation connectivity",
            "reference": "Keitt, Urban & Milne 1997, Conservation Ecology 1(1):4",
            "doi": "10.5751/ES-00015-010104",
        },
        "patches": PATCH_X,
        "pair_distances": [
            [left, right, distance]
            for (left, right), distance in sorted(PAIR_DISTANCE.items())
        ],
        "keitt_style_baseline": {
            "critical_distance": critical,
            "direct_A_C_distance": direct_distance,
            "stepping_stone_reduces_required_threshold": critical < direct_distance,
            "edges_present_at_critical_distance": stepping_edges,
        },
        "eog_one_dimensional_family": {
            "levels": list(family.levels),
            "first_possible_level": basin.first_possible_level,
            "first_robust_level": basin.first_robust_level,
            "possible_but_variant_dependent": basin.possible_but_variant_dependent,
            "coverage_certificate": basin.coverage_certificate,
        },
        "negative_boundary": {
            "critical_thresholds_match": (
                basin.first_possible_level == critical
                and basin.first_robust_level == critical
            ),
            "do_not_claim_1d_geographic_water_level_as_unique": True,
            "do_not_claim_stepping_stone_critical_distance_as_unique": True,
            "remaining_layers_to_validate": [
                "multi-axis geographic/environmental/barrier Pareto relaxation",
                "occurrence-conditioned compatible-world reconstruction",
                "analytical-world uncertainty kept explicit",
                "finite-universe robust/contingent/excluded certificates",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_keitt_critical_distance_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
