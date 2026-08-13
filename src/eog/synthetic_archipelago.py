"""Deterministic synthetic archipelagos for EOG-R method validation.

The generator encodes structural truth and observation metadata separately so tests can
represent unsurveyed intermediates and local extinction without deleting potential
transition nodes. Scenarios are fixed development fixtures, not empirical models.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np

from .dynamic_island_reachability import (
    DynamicReachabilityEdge,
    DynamicTransitionOperator,
    build_dynamic_transition_operator,
)


SCENARIO_IDS = (
    "geography_only",
    "environmental_isolation",
    "stepping_stone",
    "missing_intermediate",
    "single_bottleneck",
    "redundant_routes",
    "area_persistence",
    "directional_dispersal",
    "rare_long_jump",
    "local_extinction",
    "unsurveyed_intermediate",
    "multiple_sources",
)


@dataclass(frozen=True)
class SyntheticArchipelagoScenario:
    scenario_id: str
    node_ids: tuple[str, ...]
    coordinates: np.ndarray
    environmental_state: np.ndarray
    area: np.ndarray
    surveyed_mask: np.ndarray
    current_occurrence: np.ndarray
    historical_reached: np.ndarray
    source_ids: tuple[str, ...]
    edges: tuple[DynamicReachabilityEdge, ...]
    loss_support: float
    fingerprint: str

    def build_operator(self) -> DynamicTransitionOperator:
        return build_dynamic_transition_operator(
            self.node_ids,
            self.edges,
            loss_support=self.loss_support,
        )


def _edge(
    source: int,
    target: int,
    *,
    geographic: float = 0.9,
    environmental: float = 1.0,
    barrier: float = 1.0,
    direction: float = 1.0,
    capture: float = 1.0,
) -> DynamicReachabilityEdge:
    return DynamicReachabilityEdge(
        source,
        target,
        geographic_support=geographic,
        environmental_support=environmental,
        barrier_support=barrier,
        directional_support=direction,
        target_capture_support=capture,
    )


def _both(a: int, b: int, **kwargs) -> list[DynamicReachabilityEdge]:
    return [_edge(a, b, **kwargs), _edge(b, a, **kwargs)]


def _fingerprint(
    scenario_id: str,
    node_ids: tuple[str, ...],
    coordinates: np.ndarray,
    environmental_state: np.ndarray,
    area: np.ndarray,
    surveyed_mask: np.ndarray,
    current_occurrence: np.ndarray,
    historical_reached: np.ndarray,
    source_ids: tuple[str, ...],
    edges: tuple[DynamicReachabilityEdge, ...],
    loss_support: float,
) -> str:
    payload = {
        "scenario_id": scenario_id,
        "node_ids": list(node_ids),
        "coordinates": coordinates.tolist(),
        "environmental_state": environmental_state.tolist(),
        "area": area.tolist(),
        "surveyed_mask": surveyed_mask.astype(int).tolist(),
        "current_occurrence": current_occurrence.astype(int).tolist(),
        "historical_reached": historical_reached.astype(int).tolist(),
        "source_ids": list(source_ids),
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "geographic_support": edge.geographic_support,
                "environmental_support": edge.environmental_support,
                "barrier_support": edge.barrier_support,
                "directional_support": edge.directional_support,
                "target_capture_support": edge.target_capture_support,
            }
            for edge in edges
        ],
        "loss_support": loss_support,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _make(
    scenario_id: str,
    node_ids: tuple[str, ...],
    coordinates,
    environmental_state,
    area,
    edges,
    *,
    source_ids=("source",),
    surveyed_mask=None,
    current_occurrence=None,
    historical_reached=None,
    loss_support=0.5,
) -> SyntheticArchipelagoScenario:
    coordinates = np.asarray(coordinates, dtype=float)
    environmental_state = np.asarray(environmental_state, dtype=float)
    if environmental_state.ndim == 1:
        environmental_state = environmental_state[:, None]
    area = np.asarray(area, dtype=float)
    n = len(node_ids)
    surveyed = np.ones(n, dtype=bool) if surveyed_mask is None else np.asarray(surveyed_mask, dtype=bool)
    current = np.zeros(n, dtype=bool) if current_occurrence is None else np.asarray(current_occurrence, dtype=bool)
    historical = np.zeros(n, dtype=bool) if historical_reached is None else np.asarray(historical_reached, dtype=bool)
    edge_tuple = tuple(edges)
    sources = tuple(str(value) for value in source_ids)

    if scenario_id not in SCENARIO_IDS:
        raise ValueError("unknown synthetic scenario_id")
    if len(set(node_ids)) != n or any(not value for value in node_ids):
        raise ValueError("synthetic node IDs must be unique and non-empty")
    if coordinates.shape != (n, 2) or not np.isfinite(coordinates).all():
        raise ValueError("coordinates must be a finite node-by-2 matrix")
    if environmental_state.shape[0] != n or environmental_state.shape[1] < 1 or not np.isfinite(environmental_state).all():
        raise ValueError("environmental_state must be a finite node-by-feature matrix")
    if area.shape != (n,) or not np.isfinite(area).all() or np.any(area < 0.0):
        raise ValueError("area must contain one finite non-negative value per node")
    for label, mask in (("surveyed_mask", surveyed), ("current_occurrence", current), ("historical_reached", historical)):
        if mask.shape != (n,):
            raise ValueError(f"{label} must align with nodes")
    if not sources or any(source not in node_ids for source in sources):
        raise ValueError("source_ids must be a non-empty subset of node_ids")
    if not np.isfinite(loss_support) or loss_support <= 0.0:
        raise ValueError("loss_support must be finite and positive")

    fingerprint = _fingerprint(
        scenario_id,
        node_ids,
        coordinates,
        environmental_state,
        area,
        surveyed,
        current,
        historical,
        sources,
        edge_tuple,
        float(loss_support),
    )
    return SyntheticArchipelagoScenario(
        scenario_id=scenario_id,
        node_ids=node_ids,
        coordinates=coordinates,
        environmental_state=environmental_state,
        area=area,
        surveyed_mask=surveyed,
        current_occurrence=current,
        historical_reached=historical,
        source_ids=sources,
        edges=edge_tuple,
        loss_support=float(loss_support),
        fingerprint=fingerprint,
    )


def build_synthetic_archipelago(scenario_id: str) -> SyntheticArchipelagoScenario:
    """Return one frozen development scenario by ID."""

    if scenario_id == "redundant_routes":
        return _make(
            scenario_id,
            ("source", "upper", "lower", "target"),
            ((0, 0), (1, 1), (1, -1), (2, 0)),
            (0.5, 0.5, 0.5, 0.5),
            (100, 50, 50, 100),
            [
                _edge(0, 1), _edge(1, 0), _edge(0, 2), _edge(2, 0),
                _edge(1, 3), _edge(3, 1), _edge(2, 3), _edge(3, 2),
            ],
            current_occurrence=(True, False, False, False),
            historical_reached=(True, True, True, True),
        )

    if scenario_id == "area_persistence":
        return _make(
            scenario_id,
            ("source", "small_target", "large_target"),
            ((0, 0), (1, 1), (1, -1)),
            (0.5, 0.5, 0.5),
            (100.0, 1.0, 100.0),
            [_edge(0, 1), _edge(1, 0), _edge(0, 2), _edge(2, 0)],
            current_occurrence=(True, False, False),
            historical_reached=(True, True, True),
        )

    if scenario_id == "directional_dispersal":
        return _make(
            scenario_id,
            ("source", "middle", "target"),
            ((0, 0), (1, 0), (2, 0)),
            (0.5, 0.5, 0.5),
            (100, 100, 100),
            [
                _edge(0, 1, direction=1.0),
                _edge(1, 2, direction=1.0),
                _edge(2, 1, direction=0.1),
                _edge(1, 0, direction=0.1),
            ],
            current_occurrence=(True, False, False),
            historical_reached=(True, True, True),
        )

    if scenario_id == "multiple_sources":
        return _make(
            scenario_id,
            ("left_source", "target", "right_source"),
            ((0, 0), (1, 0), (2, 0)),
            (0.5, 0.5, 0.5),
            (100, 100, 100),
            [_edge(0, 1, geographic=0.9), _edge(2, 1, geographic=0.4)],
            source_ids=("left_source", "right_source"),
            current_occurrence=(True, False, True),
            historical_reached=(True, True, True),
        )

    # Remaining scenarios share a four-node linear archipelago.
    node_ids = ("source", "step1", "step2", "target")
    coordinates = ((0, 0), (1, 0), (2, 0), (3, 0))
    environment = (0.5, 0.5, 0.5, 0.5)
    area = (100, 50, 50, 100)
    edges: list[DynamicReachabilityEdge] = []

    if scenario_id == "geography_only" or scenario_id == "stepping_stone":
        for a, b in ((0, 1), (1, 2), (2, 3)):
            edges.extend(_both(a, b))
    elif scenario_id == "environmental_isolation":
        edges.extend(_both(0, 1))
        edges.extend(_both(1, 2, environmental=0.05))
        edges.extend(_both(2, 3))
    elif scenario_id == "missing_intermediate":
        edges.extend(_both(0, 1))
        edges.extend(_both(2, 3))
    elif scenario_id == "single_bottleneck":
        edges.extend(_both(0, 1))
        edges.extend(_both(1, 2, barrier=0.05))
        edges.extend(_both(2, 3))
    elif scenario_id == "rare_long_jump":
        edges.extend(_both(0, 1))
        edges.extend(_both(2, 3))
        edges.extend(_both(0, 3, geographic=0.02))
    elif scenario_id == "local_extinction":
        for a, b in ((0, 1), (1, 2), (2, 3)):
            edges.extend(_both(a, b))
        return _make(
            scenario_id,
            node_ids,
            coordinates,
            environment,
            area,
            edges,
            current_occurrence=(True, True, True, False),
            historical_reached=(True, True, True, True),
        )
    elif scenario_id == "unsurveyed_intermediate":
        for a, b in ((0, 1), (1, 2), (2, 3)):
            edges.extend(_both(a, b))
        return _make(
            scenario_id,
            node_ids,
            coordinates,
            environment,
            area,
            edges,
            surveyed_mask=(True, True, False, True),
            current_occurrence=(True, False, False, False),
            historical_reached=(True, True, True, True),
        )
    else:
        raise ValueError(f"unknown synthetic scenario_id: {scenario_id}")

    return _make(
        scenario_id,
        node_ids,
        coordinates,
        environment,
        area,
        edges,
        current_occurrence=(True, False, False, False),
        historical_reached=(True, True, True, True),
    )
