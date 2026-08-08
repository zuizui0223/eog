"""Prepared connectivity for repeated anchor sets on a frozen island graph.

This is a computational acceleration of :mod:`eog.island_reachability` for the
A-Islands benchmark. Geographic/environmental geometry and scenario components depend
on the evaluation fold, not on the focal species. Preparing them once per fold avoids
rebuilding the same 12 graphs for every taxon. It does not change graph edges,
thresholds, anchors, or the connected-frequency estimand.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .island_reachability import (
    IslandReachabilityScenario,
    _adjacency,
    _environmental_matrix,
    _haversine_matrix,
    _training_edge_threshold,
    default_aislands_reachability_scenarios,
)


@dataclass(frozen=True)
class PreparedIslandConnectivity:
    node_ids: tuple[str, ...]
    geographic_distance_km: np.ndarray
    scenario_ids: tuple[str, ...]
    component_labels: tuple[np.ndarray, ...]


@dataclass(frozen=True)
class PreparedConnectivityResult:
    nearest_anchor_distance_km: np.ndarray
    connected_frequency: np.ndarray
    geography_only_connected_frequency: np.ndarray
    environmentally_constrained_connected_frequency: np.ndarray


def _components(adjacency: list[list[tuple[int, float]]]) -> np.ndarray:
    labels = np.full(len(adjacency), -1, dtype=int)
    component = 0
    for start in range(len(adjacency)):
        if labels[start] >= 0:
            continue
        stack = [start]
        labels[start] = component
        while stack:
            node = stack.pop()
            for neighbour, _ in adjacency[node]:
                if labels[neighbour] < 0:
                    labels[neighbour] = component
                    stack.append(neighbour)
        component += 1
    return labels


def prepare_island_connectivity(
    node_ids: Sequence[str],
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    environmental_values: np.ndarray,
    training_mask: Sequence[bool],
    scenarios: Sequence[IslandReachabilityScenario] | None = None,
) -> PreparedIslandConnectivity:
    """Prepare the frozen scenario graphs for one evaluation fold.

    Environmental scaling and edge thresholds are derived exactly as in
    ``evaluate_island_reachability``: from training-island predictor values only.
    Species labels are not used in preparation.
    """
    ids = tuple(str(value) for value in node_ids)
    lat = np.asarray(latitudes, dtype=float)
    lon = np.asarray(longitudes, dtype=float)
    env = np.asarray(environmental_values, dtype=float)
    training = np.asarray(training_mask, dtype=bool)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("node_ids must contain at least two unique IDs")
    if lat.ndim != 1 or lon.ndim != 1 or lat.shape != lon.shape or len(lat) != len(ids):
        raise ValueError("coordinates must be aligned one-dimensional vectors")
    if not np.isfinite(lat).all() or not np.isfinite(lon).all():
        raise ValueError("coordinates must be finite")
    if env.ndim != 2 or env.shape[0] != len(ids) or env.shape[1] < 1 or not np.isfinite(env).all():
        raise ValueError("environmental_values must be a finite node-by-feature matrix")
    if training.shape != lat.shape or np.sum(training) < 2:
        raise ValueError("training_mask must align and contain at least two training islands")

    declared = tuple(scenarios or default_aislands_reachability_scenarios())
    if not declared or len({scenario.scenario_id for scenario in declared}) != len(declared):
        raise ValueError("reachability scenarios must be non-empty with unique IDs")

    geographic = _haversine_matrix(lat, lon)
    environmental = _environmental_matrix(env, training)
    labels: list[np.ndarray] = []
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
        graph = _adjacency(
            geographic,
            environmental,
            radius=scenario.max_geographic_km,
            environmental_threshold=threshold,
        )
        labels.append(_components(graph))

    return PreparedIslandConnectivity(
        node_ids=ids,
        geographic_distance_km=geographic,
        scenario_ids=tuple(scenario.scenario_id for scenario in declared),
        component_labels=tuple(labels),
    )


def evaluate_prepared_connectivity(
    prepared: PreparedIslandConnectivity,
    anchor_mask: Sequence[bool],
) -> PreparedConnectivityResult:
    """Evaluate a species' training-presence anchors on prepared fold geometry."""
    anchors = np.asarray(anchor_mask, dtype=bool)
    n = len(prepared.node_ids)
    if anchors.shape != (n,) or not np.any(anchors):
        raise ValueError("anchor_mask must align and contain at least one anchor")

    nearest = np.min(prepared.geographic_distance_km[:, anchors], axis=1)
    reach = np.zeros((len(prepared.component_labels), n), dtype=float)
    for index, labels in enumerate(prepared.component_labels):
        anchor_components = np.unique(labels[anchors])
        reach[index] = np.isin(labels, anchor_components)

    geo_indices = [i for i, scenario_id in enumerate(prepared.scenario_ids) if scenario_id.endswith("env_none")]
    env_indices = [i for i, scenario_id in enumerate(prepared.scenario_ids) if not scenario_id.endswith("env_none")]
    if not geo_indices or not env_indices:
        raise ValueError("prepared scenarios must contain geography-only and environmental cases")

    return PreparedConnectivityResult(
        nearest_anchor_distance_km=nearest,
        connected_frequency=np.mean(reach, axis=0),
        geography_only_connected_frequency=np.mean(reach[geo_indices], axis=0),
        environmentally_constrained_connected_frequency=np.mean(reach[env_indices], axis=0),
    )
