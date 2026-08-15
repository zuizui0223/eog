#!/usr/bin/env python3
"""Negative novelty boundary against minimum cumulative environmental exposure.

Dobrowski & Parks (2016) showed that endpoint distance can miss climatic resistance
along a trajectory and used least-cost modelling to identify paths that minimize
cumulative exposure to climates dissimilar from the source climate.  Their MCE is a
cumulative tally of climate dissimilarity encountered along the selected path after
separating the base path-distance contribution.

This benchmark constructs a small graph analogue with equal-climate endpoints:

- A-B-C is the geographically shorter route but crosses a strong warm anomaly at B;
- A-D-E-C is geographically longer but remains near the source climate.

An independent minimum-cumulative-exposure calculation and EOG's existing bridge
operator, when asked the same pure environmental-cost question, should choose the same
longer low-exposure route.  Equality is the expected result and defines a negative
novelty boundary.

The benchmark therefore removes from any EOG novelty claim, by themselves:

- endpoint similarity != path environmental feasibility;
- choosing a least-exposure path through environmental space;
- cumulative environmental exposure and its path bottleneck.

The remaining prospective distinction must lie in the inverse multi-world architecture:
occurrence-conditioned compatible-world sets, multiple relaxation axes retained as a
Pareto set, analytical-world uncertainty, underidentification, and explicit finite-
universe certificates.
"""
from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path

from eog import BridgeEdge, BridgeWeights, infer_bridge


TEMPERATURE = {
    "A": 0.0,
    "B": 2.0,
    "C": 0.0,
    "D": 0.2,
    "E": 0.2,
}

# Unit-length graph edges.  There are exactly two source-target route families:
# short/high-exposure A-B-C and long/low-exposure A-D-E-C.
EDGES = (
    ("A", "B", 1.0),
    ("B", "C", 1.0),
    ("A", "D", 1.0),
    ("D", "E", 1.0),
    ("E", "C", 1.0),
)


def _edge_exposure(left: str, right: str, length: float) -> float:
    """Trapezoidal graph analogue of integrated dissimilarity from source climate."""

    source_temperature = TEMPERATURE["A"]
    left_dissimilarity = abs(TEMPERATURE[left] - source_temperature)
    right_dissimilarity = abs(TEMPERATURE[right] - source_temperature)
    return 0.5 * (left_dissimilarity + right_dissimilarity) * float(length)


def _adjacency(cost_mode: str):
    graph = {node_id: [] for node_id in TEMPERATURE}
    for left, right, length in EDGES:
        if cost_mode == "distance":
            cost = float(length)
        elif cost_mode == "exposure":
            cost = _edge_exposure(left, right, length)
        else:
            raise ValueError(f"unknown cost mode: {cost_mode}")
        graph[left].append((right, cost))
        graph[right].append((left, cost))
    return graph


def _shortest_path(cost_mode: str):
    graph = _adjacency(cost_mode)
    source = "A"
    target = "C"
    queue = [(0.0, (source,), source)]
    best = {source: 0.0}
    while queue:
        cost, path, node = heapq.heappop(queue)
        if cost != best.get(node):
            continue
        if node == target:
            return cost, path
        for neighbor, edge_cost in graph[node]:
            candidate = cost + edge_cost
            if candidate < best.get(neighbor, float("inf")) - 1e-15:
                best[neighbor] = candidate
                heapq.heappush(queue, (candidate, path + (neighbor,), neighbor))
    raise RuntimeError("target is disconnected")


def _path_exposure(path) -> float:
    lookup = {
        frozenset((left, right)): _edge_exposure(left, right, length)
        for left, right, length in EDGES
    }
    return sum(lookup[frozenset((left, right))] for left, right in zip(path[:-1], path[1:]))


def _path_length(path) -> float:
    lookup = {frozenset((left, right)): length for left, right, length in EDGES}
    return sum(lookup[frozenset((left, right))] for left, right in zip(path[:-1], path[1:]))


def _bridge_summary():
    node_ids = tuple(TEMPERATURE)
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    bridge_edges = tuple(
        BridgeEdge(
            index[left],
            index[right],
            geographic_cost=float(length),
            environmental_cost=_edge_exposure(left, right, length),
            barrier_cost=0.0,
        )
        for left, right, length in EDGES
    )
    result = infer_bridge(
        len(node_ids),
        bridge_edges,
        index["A"],
        index["C"],
        weights=BridgeWeights(geographic=0.0, environmental=1.0, barrier=0.0),
    )
    path_ids = tuple(node_ids[index_value] for index_value in result.minimum_cost_path.nodes)
    bottleneck_ids = tuple(
        node_ids[index_value] for index_value in result.minimum_bottleneck_path.nodes
    )
    return {
        "minimum_environmental_path": list(path_ids),
        "minimum_environmental_cost": result.minimum_cost_path.environmental_cost,
        "minimum_bottleneck_path": list(bottleneck_ids),
        "minimum_bottleneck_cost": result.minimum_bottleneck_path.bottleneck_cost,
        "geographic_length_of_environmental_path": _path_length(path_ids),
    }


def run_mce_environmental_exposure_boundary():
    distance_cost, distance_path = _shortest_path("distance")
    exposure_cost, exposure_path = _shortest_path("exposure")
    bridge = _bridge_summary()

    short_path_exposure = _path_exposure(distance_path)
    low_exposure_path_length = _path_length(exposure_path)
    endpoint_temperature_difference = abs(TEMPERATURE["A"] - TEMPERATURE["C"])

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "minimum cumulative exposure / minimum exposure least-cost path",
            "reference": "Dobrowski & Parks 2016, Nature Communications 7:12349",
            "doi": "10.1038/ncomms12349",
        },
        "known_truth": {
            "temperature_by_node": TEMPERATURE,
            "endpoint_temperature_difference": endpoint_temperature_difference,
            "shortest_distance_path": list(distance_path),
            "shortest_distance": distance_cost,
            "exposure_of_shortest_distance_path": short_path_exposure,
            "minimum_exposure_path": list(exposure_path),
            "minimum_cumulative_exposure": exposure_cost,
            "length_of_minimum_exposure_path": low_exposure_path_length,
            "longer_path_has_lower_exposure": (
                low_exposure_path_length > distance_cost and exposure_cost < short_path_exposure
            ),
        },
        "eog_existing_bridge": bridge,
        "negative_boundary": {
            "minimum_exposure_path_matches": (
                tuple(bridge["minimum_environmental_path"]) == exposure_path
            ),
            "minimum_cumulative_exposure_matches": (
                abs(bridge["minimum_environmental_cost"] - exposure_cost) < 1e-12
            ),
            "endpoint_similarity_does_not_imply_zero_path_exposure": (
                endpoint_temperature_difference == 0.0 and short_path_exposure > 0.0
            ),
            "do_not_claim_path_environmental_exposure_as_unique": True,
            "do_not_claim_least_exposure_route_as_unique": True,
            "remaining_layers_to_validate": [
                "occurrence-conditioned multi-axis relaxation Pareto sets",
                "explicit ecological plus analytical admissible-world universes",
                "world-indexed alternatives and underidentification",
                "finite-universe robustness and exclusion certificates",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_mce_environmental_exposure_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
