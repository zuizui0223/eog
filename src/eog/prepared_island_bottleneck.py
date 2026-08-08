"""Prepared minimax bottleneck evaluation for the frozen A-Islands graphs.

Graph geometry is species-independent within an evaluation fold. This module prepares
those graphs once and then evaluates species-specific training-presence anchor sets.
It is a computational acceleration of the already-frozen bottleneck diagnostic.
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
    _multi_source_minimax,
    _training_edge_threshold,
    default_aislands_reachability_scenarios,
)


@dataclass(frozen=True)
class PreparedIslandBottleneck:
    node_ids: tuple[str, ...]
    geographic_distance_km: np.ndarray
    scenario_ids: tuple[str, ...]
    radii_km: tuple[float, ...]
    adjacencies: tuple[list[list[tuple[int, float]]], ...]


def prepare_island_bottleneck(
    node_ids: Sequence[str],
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    environmental_values: np.ndarray,
    training_mask: Sequence[bool],
    scenarios: Sequence[IslandReachabilityScenario] | None = None,
) -> PreparedIslandBottleneck:
    ids = tuple(str(value) for value in node_ids)
    lat = np.asarray(latitudes, dtype=float)
    lon = np.asarray(longitudes, dtype=float)
    env = np.asarray(environmental_values, dtype=float)
    training = np.asarray(training_mask, dtype=bool)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("node_ids must contain at least two unique IDs")
    if lat.ndim != 1 or lon.ndim != 1 or lat.shape != lon.shape or len(lat) != len(ids):
        raise ValueError("coordinates must be aligned one-dimensional vectors")
    if env.ndim != 2 or env.shape[0] != len(ids) or not np.isfinite(env).all():
        raise ValueError("environmental_values must be a finite node-by-feature matrix")
    if training.shape != lat.shape or np.sum(training) < 2:
        raise ValueError("training_mask must align and contain at least two training islands")

    declared = tuple(scenarios or default_aislands_reachability_scenarios())
    geographic = _haversine_matrix(lat, lon)
    environmental = _environmental_matrix(env, training)
    graphs = []
    for scenario in declared:
        threshold = None
        if scenario.environmental_edge_quantile is not None:
            threshold = _training_edge_threshold(
                geographic, environmental, training,
                scenario.max_geographic_km, scenario.environmental_edge_quantile,
            )
        graphs.append(_adjacency(
            geographic, environmental,
            radius=scenario.max_geographic_km,
            environmental_threshold=threshold,
        ))
    return PreparedIslandBottleneck(
        node_ids=ids,
        geographic_distance_km=geographic,
        scenario_ids=tuple(s.scenario_id for s in declared),
        radii_km=tuple(float(s.max_geographic_km) for s in declared),
        adjacencies=tuple(graphs),
    )


def evaluate_prepared_bottleneck(
    prepared: PreparedIslandBottleneck,
    anchor_mask: Sequence[bool],
) -> tuple[np.ndarray, np.ndarray]:
    """Return nearest-anchor distance and frozen median normalized bottleneck."""
    anchors = np.asarray(anchor_mask, dtype=bool)
    n = len(prepared.node_ids)
    if anchors.shape != (n,) or not np.any(anchors):
        raise ValueError("anchor_mask must align and contain at least one anchor")
    nearest = np.min(prepared.geographic_distance_km[:, anchors], axis=1)
    bottlenecks = []
    for graph, radius in zip(prepared.adjacencies, prepared.radii_km):
        _, normalized = _multi_source_minimax(graph, anchors, radius)
        bottlenecks.append(normalized)
    matrix = np.vstack(bottlenecks)
    with np.errstate(invalid="ignore"):
        median = np.nanmedian(matrix, axis=0)
    median[~np.any(np.isfinite(matrix), axis=0)] = np.nan
    return nearest, median
