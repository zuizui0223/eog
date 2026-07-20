"""Deterministic construction of candidate bridge graphs from point or patch states."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np

from .bridge import BridgeEdge
from .comparative import RobustReference, transform_with_reference


@dataclass(frozen=True)
class BridgeNode:
    node_id: str
    latitude: float
    longitude: float
    environmental_state: tuple[float, ...]
    group: str = ""
    time_order: float | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not np.isfinite((self.latitude, self.longitude)).all():
            raise ValueError("coordinates must be finite")
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ValueError("coordinates are outside latitude/longitude bounds")
        state = np.asarray(self.environmental_state, dtype=float)
        if state.ndim != 1 or state.size == 0 or not np.isfinite(state).all():
            raise ValueError("environmental_state must be a finite non-empty vector")
        if self.time_order is not None and not np.isfinite(self.time_order):
            raise ValueError("time_order must be finite when supplied")


@dataclass(frozen=True)
class BridgeGraphDeclaration:
    k_nearest: int | None = None
    max_geographic_km: float | None = None
    max_environmental_distance: float | None = None
    directed_by_time: bool = False

    def __post_init__(self) -> None:
        if self.k_nearest is None and self.max_geographic_km is None:
            raise ValueError("declare k_nearest, max_geographic_km, or both")
        if self.k_nearest is not None and self.k_nearest < 1:
            raise ValueError("k_nearest must be positive")
        for value, name in (
            (self.max_geographic_km, "max_geographic_km"),
            (self.max_environmental_distance, "max_environmental_distance"),
        ):
            if value is not None and (not np.isfinite(value) or value <= 0):
                raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class BuiltBridgeGraph:
    nodes: tuple[BridgeNode, ...]
    edges: tuple[BridgeEdge, ...]
    node_index: Mapping[str, int]
    declaration: BridgeGraphDeclaration
    fingerprint: str


def haversine_km(a: BridgeNode, b: BridgeNode) -> float:
    """Great-circle distance between two nodes in kilometres."""
    radius = 6371.0088
    lat1, lon1, lat2, lon2 = map(math.radians, (a.latitude, a.longitude, b.latitude, b.longitude))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return float(2 * radius * math.asin(min(1.0, math.sqrt(value))))


def _barrier_cost(barriers: Mapping[tuple[str, str], float], a: str, b: str) -> float:
    value = barriers.get((a, b), barriers.get((b, a), 0.0))
    if not np.isfinite(value) or value < 0:
        raise ValueError("barrier costs must be finite and non-negative")
    return float(value)


def build_bridge_graph(
    nodes: Sequence[BridgeNode],
    reference: RobustReference,
    declaration: BridgeGraphDeclaration,
    *,
    barriers: Mapping[tuple[str, str], float] | None = None,
) -> BuiltBridgeGraph:
    """Build a stable candidate graph under explicit geographic and environmental rules."""
    ordered = tuple(sorted(nodes, key=lambda node: node.node_id))
    if len(ordered) < 2 or len({node.node_id for node in ordered}) != len(ordered):
        raise ValueError("nodes must contain at least two unique node IDs")
    states = np.asarray([node.environmental_state for node in ordered], dtype=float)
    transformed = transform_with_reference(states, reference)
    index = {node.node_id: i for i, node in enumerate(ordered)}
    barriers = barriers or {}

    pair_rows: list[tuple[float, int, int, float]] = []
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            geo = haversine_km(ordered[i], ordered[j])
            env = float(np.linalg.norm(transformed[i] - transformed[j]))
            if declaration.max_geographic_km is not None and geo > declaration.max_geographic_km:
                continue
            if declaration.max_environmental_distance is not None and env > declaration.max_environmental_distance:
                continue
            if declaration.directed_by_time:
                ti, tj = ordered[i].time_order, ordered[j].time_order
                if ti is None or tj is None:
                    raise ValueError("all nodes require time_order when directed_by_time is true")
                if ti == tj:
                    continue
            pair_rows.append((geo, i, j, env))

    selected: set[tuple[int, int]] = set()
    if declaration.k_nearest is None:
        selected = {(i, j) for _, i, j, _ in pair_rows}
    else:
        by_node: dict[int, list[tuple[float, str, int, int]]] = {i: [] for i in range(len(ordered))}
        for geo, i, j, _ in pair_rows:
            by_node[i].append((geo, ordered[j].node_id, i, j))
            by_node[j].append((geo, ordered[i].node_id, i, j))
        for rows in by_node.values():
            for _, _, i, j in sorted(rows)[: declaration.k_nearest]:
                selected.add((i, j))

    lookup = {(i, j): (geo, env) for geo, i, j, env in pair_rows}
    edges = tuple(
        BridgeEdge(
            source=i,
            target=j,
            geographic_cost=lookup[(i, j)][0],
            environmental_cost=lookup[(i, j)][1],
            barrier_cost=_barrier_cost(barriers, ordered[i].node_id, ordered[j].node_id),
        )
        for i, j in sorted(selected)
    )
    payload = {
        "nodes": [
            {
                "node_id": n.node_id,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "environmental_state": list(n.environmental_state),
                "group": n.group,
                "time_order": n.time_order,
            }
            for n in ordered
        ],
        "declaration": declaration.__dict__,
        "reference": reference.to_dict(),
        "barriers": sorted((a, b, float(v)) for (a, b), v in barriers.items()),
        "edges": [edge.__dict__ for edge in edges],
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return BuiltBridgeGraph(ordered, edges, index, declaration, fingerprint)
