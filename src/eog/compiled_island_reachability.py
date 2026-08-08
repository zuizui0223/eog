"""Compiled A-Islands reachability graphs for multi-species execution.

A spatial fold fixes the node coordinates, climate values, training-island mask and the
predeclared scenario family. Those objects do not depend on focal-species labels, so the
12 scenario connected components can be compiled once per fold. A species then only
changes the training-presence anchor mask. This is a computational optimization of the
frozen reachability definition, not a different ecological model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .island_reachability import (
    IslandReachabilityScenario,
    _as_vector,
    _environmental_matrix,
    _haversine_matrix,
    _training_edge_threshold,
    default_aislands_reachability_scenarios,
)


@dataclass(frozen=True)
class CompiledScenarioComponents:
    scenario_id: str
    max_geographic_km: float
    environmental_edge_quantile: float | None
    environmental_threshold: float | None
    component_labels: np.ndarray


@dataclass(frozen=True)
class CompiledIslandReachabilityFold:
    node_ids: tuple[str, ...]
    training_mask: np.ndarray
    geographic_distance_km: np.ndarray
    scenarios: tuple[CompiledScenarioComponents, ...]


@dataclass(frozen=True)
class CompiledAnchorReachability:
    nearest_anchor_distance_km: np.ndarray
    connected_frequency: np.ndarray
    geography_only_connected_frequency: np.ndarray
    environmentally_constrained_connected_frequency: np.ndarray
    scenario_reachable: np.ndarray


def _component_labels(
    geographic: np.ndarray,
    environmental: np.ndarray,
    *,
    radius: float,
    environmental_threshold: float | None,
) -> np.ndarray:
    n = geographic.shape[0]
    parent = np.arange(n, dtype=np.int64)
    rank = np.zeros(n, dtype=np.int16)

    def find(index: int) -> int:
        root = index
        while parent[root] != root:
            root = int(parent[root])
        while parent[index] != index:
            previous = int(parent[index])
            parent[index] = root
            index = previous
        return root

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return
        if rank[root_left] < rank[root_right]:
            parent[root_left] = root_right
        elif rank[root_left] > rank[root_right]:
            parent[root_right] = root_left
        else:
            parent[root_right] = root_left
            rank[root_left] += 1

    allowed = geographic <= radius
    if environmental_threshold is not None:
        allowed &= environmental <= environmental_threshold
    np.fill_diagonal(allowed, False)
    rows, cols = np.where(np.triu(allowed, k=1))
    for left, right in zip(rows.tolist(), cols.tolist()):
        union(int(left), int(right))

    roots = np.asarray([find(index) for index in range(n)], dtype=np.int64)
    _, labels = np.unique(roots, return_inverse=True)
    return labels.astype(np.int32, copy=False)


def compile_island_reachability_fold(
    node_ids: Sequence[str],
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    environmental_values: np.ndarray,
    training_mask: Sequence[bool],
    scenarios: Sequence[IslandReachabilityScenario] | None = None,
) -> CompiledIslandReachabilityFold:
    """Compile species-independent scenario components for one frozen spatial fold."""
    ids = tuple(str(value) for value in node_ids)
    if len(ids) < 2 or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("node_ids must contain at least two unique non-empty IDs")
    lat = _as_vector(latitudes, "latitudes")
    lon = _as_vector(longitudes, "longitudes")
    if len(ids) != len(lat) or lat.shape != lon.shape:
        raise ValueError("node IDs and coordinates must align")
    if np.any((lat < -90) | (lat > 90)) or np.any((lon < -180) | (lon > 180)):
        raise ValueError("coordinates outside latitude/longitude bounds")

    env = np.asarray(environmental_values, dtype=float)
    if env.ndim != 2 or env.shape[0] != len(ids) or env.shape[1] < 1 or not np.isfinite(env).all():
        raise ValueError("environmental_values must be a finite node-by-feature matrix")
    training = np.asarray(training_mask, dtype=bool)
    if training.shape != lat.shape or np.sum(training) < 2:
        raise ValueError("training_mask must align and contain at least two training islands")

    declared = tuple(scenarios or default_aislands_reachability_scenarios())
    if not declared or len({scenario.scenario_id for scenario in declared}) != len(declared):
        raise ValueError("reachability scenarios must be non-empty with unique IDs")

    geographic = _haversine_matrix(lat, lon)
    environmental = _environmental_matrix(env, training)
    compiled: list[CompiledScenarioComponents] = []
    for scenario in declared:
        threshold = None
        if scenario.environmental_edge_quantile is not None:
            threshold = _training_edge_threshold(
                geographic,
                environmental,
                training,
                scenario.max_geographic_km,
                scenario.environmental_edge_quantile,
            )
        labels = _component_labels(
            geographic,
            environmental,
            radius=scenario.max_geographic_km,
            environmental_threshold=threshold,
        )
        compiled.append(
            CompiledScenarioComponents(
                scenario_id=scenario.scenario_id,
                max_geographic_km=scenario.max_geographic_km,
                environmental_edge_quantile=scenario.environmental_edge_quantile,
                environmental_threshold=threshold,
                component_labels=labels,
            )
        )

    return CompiledIslandReachabilityFold(
        node_ids=ids,
        training_mask=training.copy(),
        geographic_distance_km=geographic,
        scenarios=tuple(compiled),
    )


def evaluate_compiled_anchor_reachability(
    compiled: CompiledIslandReachabilityFold,
    anchor_mask: Sequence[bool],
) -> CompiledAnchorReachability:
    """Evaluate one focal species by changing only its training-presence anchors."""
    anchors = np.asarray(anchor_mask, dtype=bool)
    if anchors.shape != compiled.training_mask.shape:
        raise ValueError("anchor_mask must align with the compiled node universe")
    if not np.any(anchors):
        raise ValueError("at least one training-presence anchor is required")
    if np.any(anchors & ~compiled.training_mask):
        raise ValueError("all occurrence anchors must be training islands")

    reachable_rows: list[np.ndarray] = []
    geography_rows: list[np.ndarray] = []
    environmental_rows: list[np.ndarray] = []
    for scenario in compiled.scenarios:
        labels = scenario.component_labels
        anchor_components = np.unique(labels[anchors])
        reachable = np.isin(labels, anchor_components)
        reachable_rows.append(reachable)
        if scenario.environmental_edge_quantile is None:
            geography_rows.append(reachable)
        else:
            environmental_rows.append(reachable)

    scenario_reachable = np.vstack(reachable_rows).astype(float)
    geography = np.vstack(geography_rows).astype(float)
    environmental = np.vstack(environmental_rows).astype(float)
    nearest = np.min(compiled.geographic_distance_km[:, anchors], axis=1)
    return CompiledAnchorReachability(
        nearest_anchor_distance_km=nearest,
        connected_frequency=np.mean(scenario_reachable, axis=0),
        geography_only_connected_frequency=np.mean(geography, axis=0),
        environmentally_constrained_connected_frequency=np.mean(environmental, axis=0),
        scenario_reachable=scenario_reachable.astype(bool),
    )
