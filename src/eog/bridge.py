"""Population-pair bridge diagnostics on declared point or patch graphs.

The module evaluates paths between a source and target under explicitly separated
geographic, environmental and structural-barrier costs. Outputs are transition
diagnostics, not suitability, occupancy or colonisation probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Iterable
import warnings

import numpy as np

from .comparative import RobustReference, transform_with_reference


@dataclass(frozen=True)
class BridgeWeights:
    geographic: float = 1.0
    environmental: float = 1.0
    barrier: float = 1.0

    def __post_init__(self) -> None:
        values = (self.geographic, self.environmental, self.barrier)
        if not all(np.isfinite(values)) or any(value < 0 for value in values):
            raise ValueError("bridge weights must be finite and non-negative")
        if not any(value > 0 for value in values):
            raise ValueError("at least one bridge weight must be positive")


@dataclass(frozen=True)
class BridgeEdge:
    source: int
    target: int
    geographic_cost: float
    environmental_cost: float
    barrier_cost: float = 0.0

    def __post_init__(self) -> None:
        if self.source < 0 or self.target < 0 or self.source == self.target:
            raise ValueError("edge endpoints must be distinct non-negative indices")
        values = (self.geographic_cost, self.environmental_cost, self.barrier_cost)
        if not all(np.isfinite(values)) or any(value < 0 for value in values):
            raise ValueError("edge costs must be finite and non-negative")

    def total(self, weights: BridgeWeights) -> float:
        return float(
            weights.geographic * self.geographic_cost
            + weights.environmental * self.environmental_cost
            + weights.barrier * self.barrier_cost
        )


@dataclass(frozen=True)
class BridgePath:
    nodes: tuple[int, ...]
    cumulative_cost: float
    bottleneck_cost: float
    geographic_cost: float
    environmental_cost: float
    barrier_cost: float


@dataclass(frozen=True)
class BridgeInference:
    source: int
    target: int
    minimum_cost_path: BridgePath
    minimum_bottleneck_path: BridgePath
    direct_edge_cost: float | None
    bridge_gain: float | None
    edge_disjoint_path_count: int
    redundancy_threshold: float


def environmental_edge_costs(
    values: np.ndarray,
    edges: Iterable[tuple[int, int]],
    reference: RobustReference,
) -> list[tuple[int, int, float]]:
    """Return shared-reference Euclidean environmental costs for declared edges."""
    transformed = transform_with_reference(values, reference)
    result: list[tuple[int, int, float]] = []
    n = len(transformed)
    for source, target in edges:
        if source < 0 or target < 0 or source >= n or target >= n or source == target:
            raise ValueError("declared edge contains an invalid endpoint")
        result.append(
            (int(source), int(target), float(np.linalg.norm(transformed[source] - transformed[target])))
        )
    return result


def _audit_cost_scales(edges: list[BridgeEdge], weights: BridgeWeights) -> None:
    """Warn when active cost dimensions have strongly incompatible numeric scales.

    Bridge graphs built by :mod:`eog.bridge_builder` store geographic cost in km,
    environmental cost in frozen-reference standardised units, and barrier cost in
    analyst-declared units. Equal numeric weights therefore do not imply equal
    scientific influence. The audit is diagnostic only and does not rescale costs.
    """
    dimensions = (
        ("geographic", weights.geographic, [edge.geographic_cost for edge in edges]),
        ("environmental", weights.environmental, [edge.environmental_cost for edge in edges]),
        ("barrier", weights.barrier, [edge.barrier_cost for edge in edges]),
    )
    active: list[tuple[str, float]] = []
    for name, weight, raw in dimensions:
        positive = np.asarray([value for value in raw if value > 0], dtype=float)
        if weight > 0 and positive.size:
            active.append((name, float(weight * np.median(positive))))
    if len(active) < 2:
        return
    smallest = min(value for _, value in active)
    largest = max(value for _, value in active)
    if smallest > 0 and largest / smallest > 100.0:
        summary = ", ".join(f"{name}={value:.6g}" for name, value in active)
        warnings.warn(
            "bridge cost dimensions differ by more than 100-fold after weighting "
            f"({summary}); declare weights from an explicit scaling or sensitivity policy",
            RuntimeWarning,
            stacklevel=3,
        )


def _adjacency(n_nodes: int, edges: Iterable[BridgeEdge], weights: BridgeWeights):
    graph: list[list[tuple[int, BridgeEdge, float]]] = [[] for _ in range(n_nodes)]
    edge_map: dict[tuple[int, int], BridgeEdge] = {}
    for edge in edges:
        if edge.source >= n_nodes or edge.target >= n_nodes:
            raise ValueError("edge endpoint exceeds n_nodes")
        key = (min(edge.source, edge.target), max(edge.source, edge.target))
        if key in edge_map:
            raise ValueError("duplicate undirected bridge edge")
        cost = edge.total(weights)
        graph[edge.source].append((edge.target, edge, cost))
        graph[edge.target].append((edge.source, edge, cost))
        edge_map[key] = edge
    return graph, edge_map


def _reconstruct(source: int, target: int, previous: list[int], edge_map, weights: BridgeWeights) -> BridgePath:
    if source != target and previous[target] < 0:
        raise ValueError("source and target are disconnected")
    nodes = [target]
    while nodes[-1] != source:
        nodes.append(previous[nodes[-1]])
    nodes.reverse()
    used = [edge_map[(min(a, b), max(a, b))] for a, b in zip(nodes, nodes[1:])]
    totals = [edge.total(weights) for edge in used]
    return BridgePath(
        nodes=tuple(nodes),
        cumulative_cost=float(sum(totals)),
        bottleneck_cost=float(max(totals, default=0.0)),
        geographic_cost=float(sum(edge.geographic_cost for edge in used)),
        environmental_cost=float(sum(edge.environmental_cost for edge in used)),
        barrier_cost=float(sum(edge.barrier_cost for edge in used)),
    )


def _shortest_path(n_nodes: int, graph, source: int, target: int, edge_map, weights):
    distance = [float("inf")] * n_nodes
    previous = [-1] * n_nodes
    distance[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current_cost, node = heapq.heappop(queue)
        if current_cost != distance[node]:
            continue
        if node == target:
            break
        for neighbour, _edge, edge_cost in graph[node]:
            candidate = current_cost + edge_cost
            if candidate < distance[neighbour]:
                distance[neighbour] = candidate
                previous[neighbour] = node
                heapq.heappush(queue, (candidate, neighbour))
    return _reconstruct(source, target, previous, edge_map, weights)


def _minimax_path(n_nodes: int, graph, source: int, target: int, edge_map, weights):
    bottleneck = [float("inf")] * n_nodes
    previous = [-1] * n_nodes
    bottleneck[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current != bottleneck[node]:
            continue
        if node == target:
            break
        for neighbour, _edge, edge_cost in graph[node]:
            candidate = max(current, edge_cost)
            if candidate < bottleneck[neighbour]:
                bottleneck[neighbour] = candidate
                previous[neighbour] = node
                heapq.heappush(queue, (candidate, neighbour))
    return _reconstruct(source, target, previous, edge_map, weights)


def _edge_disjoint_count(
    n_nodes: int,
    edges: list[BridgeEdge],
    source: int,
    target: int,
    weights: BridgeWeights,
    threshold: float,
) -> int:
    allowed = [edge for edge in edges if edge.total(weights) <= threshold]
    residual: dict[tuple[int, int], int] = {}
    neighbours: list[set[int]] = [set() for _ in range(n_nodes)]
    for edge in allowed:
        for a, b in ((edge.source, edge.target), (edge.target, edge.source)):
            residual[(a, b)] = 1
            neighbours[a].add(b)
    flow = 0
    while True:
        previous = [-1] * n_nodes
        previous[source] = source
        queue = [source]
        for node in queue:
            for neighbour in neighbours[node]:
                if previous[neighbour] < 0 and residual.get((node, neighbour), 0) > 0:
                    previous[neighbour] = node
                    queue.append(neighbour)
                    if neighbour == target:
                        break
            if previous[target] >= 0:
                break
        if previous[target] < 0:
            return flow
        node = target
        while node != source:
            parent = previous[node]
            residual[(parent, node)] -= 1
            residual[(node, parent)] = residual.get((node, parent), 0) + 1
            neighbours[node].add(parent)
            node = parent
        flow += 1


def infer_bridge(
    n_nodes: int,
    edges: Iterable[BridgeEdge],
    source: int,
    target: int,
    *,
    weights: BridgeWeights = BridgeWeights(),
    redundancy_threshold: float | None = None,
) -> BridgeInference:
    """Infer cumulative, bottleneck and redundant bridge paths.

    ``redundancy_threshold`` limits the edge costs admitted when counting
    edge-disjoint alternatives. By default it equals the bottleneck of the
    minimum-cumulative-cost path. Mixed cost dimensions are audited for gross
    numeric-scale imbalance but are never automatically rescaled.
    """
    if n_nodes < 2 or source < 0 or target < 0 or source >= n_nodes or target >= n_nodes or source == target:
        raise ValueError("source and target must be distinct valid node indices")
    edge_list = list(edges)
    _audit_cost_scales(edge_list, weights)
    graph, edge_map = _adjacency(n_nodes, edge_list, weights)
    shortest = _shortest_path(n_nodes, graph, source, target, edge_map, weights)
    minimax = _minimax_path(n_nodes, graph, source, target, edge_map, weights)
    threshold = shortest.bottleneck_cost if redundancy_threshold is None else float(redundancy_threshold)
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("redundancy_threshold must be finite and non-negative")
    direct = edge_map.get((min(source, target), max(source, target)))
    direct_cost = None if direct is None else direct.total(weights)
    gain = None if direct_cost is None else float(direct_cost - shortest.cumulative_cost)
    return BridgeInference(
        source=source,
        target=target,
        minimum_cost_path=shortest,
        minimum_bottleneck_path=minimax,
        direct_edge_cost=direct_cost,
        bridge_gain=gain,
        edge_disjoint_path_count=_edge_disjoint_count(
            n_nodes, edge_list, source, target, weights, threshold
        ),
        redundancy_threshold=threshold,
    )
