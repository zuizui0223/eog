"""Occurrence-anchored structural reachability on a frozen island network.

The diagnostics in this module are assumption-dependent graph summaries. They are not
occupancy, dispersal or colonisation probabilities and do not reconstruct a historical
route. Held-out labels are never required to construct a graph or a reachability score.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Sequence

import numpy as np

from .comparative import fit_robust_reference, transform_with_reference


EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class IslandReachabilityScenario:
    scenario_id: str
    max_geographic_km: float
    environmental_edge_quantile: float | None = None

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if not np.isfinite(self.max_geographic_km) or self.max_geographic_km <= 0:
            raise ValueError("max_geographic_km must be finite and positive")
        if self.environmental_edge_quantile is not None and not (
            0.0 < self.environmental_edge_quantile < 1.0
        ):
            raise ValueError("environmental_edge_quantile must lie in (0, 1)")


@dataclass(frozen=True)
class IslandReachabilityScenarioResult:
    scenario_id: str
    max_geographic_km: float
    environmental_edge_quantile: float | None
    environmental_threshold: float | None
    reachable: np.ndarray
    normalized_geographic_bottleneck: np.ndarray


@dataclass(frozen=True)
class IslandReachabilityResult:
    node_ids: tuple[str, ...]
    nearest_anchor_distance_km: np.ndarray
    connected_frequency: np.ndarray
    geography_only_connected_frequency: np.ndarray
    environmentally_constrained_connected_frequency: np.ndarray
    median_normalized_geographic_bottleneck: np.ndarray
    scenarios: tuple[IslandReachabilityScenarioResult, ...]


def default_aislands_reachability_scenarios() -> tuple[IslandReachabilityScenario, ...]:
    """Return the frozen 12-scenario A-Islands structural assumption ensemble."""
    scenarios: list[IslandReachabilityScenario] = []
    for radius in (25.0, 50.0, 125.0, 250.0):
        scenarios.extend(
            [
                IslandReachabilityScenario(f"g{int(radius)}_env_none", radius, None),
                IslandReachabilityScenario(f"g{int(radius)}_env_q90", radius, 0.90),
                IslandReachabilityScenario(f"g{int(radius)}_env_q75", radius, 0.75),
            ]
        )
    return tuple(scenarios)


def _as_vector(values: Sequence[float], label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 2 or not np.isfinite(array).all():
        raise ValueError(f"{label} must be a finite one-dimensional vector with >=2 rows")
    return array


def _haversine_matrix(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    lat = np.radians(latitudes)[:, None]
    lon = np.radians(longitudes)[:, None]
    dlat = lat - lat.T
    dlon = lon - lon.T
    value = np.sin(dlat / 2.0) ** 2 + np.cos(lat) * np.cos(lat.T) * np.sin(dlon / 2.0) ** 2
    matrix = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.minimum(1.0, np.sqrt(value)))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def _environmental_matrix(values: np.ndarray, training_mask: np.ndarray) -> np.ndarray:
    reference = fit_robust_reference(
        values[training_mask],
        provenance="A-Islands training islands only; species labels not used for scaling",
    )
    transformed = transform_with_reference(values, reference)
    delta = transformed[:, None, :] - transformed[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _training_edge_threshold(
    geographic: np.ndarray,
    environmental: np.ndarray,
    training_mask: np.ndarray,
    radius: float,
    quantile: float,
) -> float:
    training_indices = np.flatnonzero(training_mask)
    sub_geo = geographic[np.ix_(training_indices, training_indices)]
    sub_env = environmental[np.ix_(training_indices, training_indices)]
    upper = np.triu_indices(len(training_indices), k=1)
    values = sub_env[upper]
    allowed = sub_geo[upper] <= radius
    values = values[allowed & np.isfinite(values)]
    if values.size == 0:
        raise ValueError(
            f"no training-training geographic edges exist within {radius:g} km for environmental threshold"
        )
    return float(np.quantile(values, quantile))


def _adjacency(
    geographic: np.ndarray,
    environmental: np.ndarray,
    *,
    radius: float,
    environmental_threshold: float | None,
) -> list[list[tuple[int, float]]]:
    n = geographic.shape[0]
    result: list[list[tuple[int, float]]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            geo = float(geographic[i, j])
            if geo > radius:
                continue
            if environmental_threshold is not None and environmental[i, j] > environmental_threshold:
                continue
            result[i].append((j, geo))
            result[j].append((i, geo))
    return result


def _multi_source_minimax(
    adjacency: list[list[tuple[int, float]]],
    anchor_mask: np.ndarray,
    radius: float,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(adjacency)
    bottleneck = np.full(n, np.inf, dtype=float)
    queue: list[tuple[float, int]] = []
    for index in np.flatnonzero(anchor_mask):
        bottleneck[index] = 0.0
        heapq.heappush(queue, (0.0, int(index)))
    while queue:
        current, node = heapq.heappop(queue)
        if current != bottleneck[node]:
            continue
        for neighbour, edge_geo in adjacency[node]:
            candidate = max(current, edge_geo)
            if candidate < bottleneck[neighbour]:
                bottleneck[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    reachable = np.isfinite(bottleneck)
    normalized = np.where(reachable, bottleneck / radius, np.nan)
    return reachable, normalized


def nearest_anchor_distance_km(
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    anchor_mask: Sequence[bool],
) -> np.ndarray:
    lat = _as_vector(latitudes, "latitudes")
    lon = _as_vector(longitudes, "longitudes")
    if lat.shape != lon.shape:
        raise ValueError("latitude and longitude vectors must align")
    anchors = np.asarray(anchor_mask, dtype=bool)
    if anchors.shape != lat.shape or not np.any(anchors):
        raise ValueError("anchor_mask must align and contain at least one anchor")
    geographic = _haversine_matrix(lat, lon)
    return np.min(geographic[:, anchors], axis=1)


def evaluate_island_reachability(
    node_ids: Sequence[str],
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    environmental_values: np.ndarray,
    training_mask: Sequence[bool],
    anchor_mask: Sequence[bool],
    scenarios: Sequence[IslandReachabilityScenario] | None = None,
) -> IslandReachabilityResult:
    """Evaluate all nodes against training-presence anchors across frozen scenarios.

    All islands remain potential structural stepping-stone nodes regardless of their
    species label. This deliberately represents potential island-chain structure, not a
    reconstructed occupied pathway. The environmental reference and quantile cutoffs are
    derived from training-island predictors only; held-out labels never enter them.
    """
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
    anchors = np.asarray(anchor_mask, dtype=bool)
    if training.shape != lat.shape or anchors.shape != lat.shape:
        raise ValueError("training_mask and anchor_mask must align with nodes")
    if np.sum(training) < 2:
        raise ValueError("at least two training islands are required")
    if not np.any(anchors):
        raise ValueError("at least one training-presence anchor is required")
    if np.any(anchors & ~training):
        raise ValueError("all occurrence anchors must be training islands")

    declared = tuple(scenarios or default_aislands_reachability_scenarios())
    if not declared or len({scenario.scenario_id for scenario in declared}) != len(declared):
        raise ValueError("reachability scenarios must be non-empty with unique IDs")

    geographic = _haversine_matrix(lat, lon)
    environmental = _environmental_matrix(env, training)
    nearest = np.min(geographic[:, anchors], axis=1)
    scenario_results: list[IslandReachabilityScenarioResult] = []

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
        reachable, bottleneck = _multi_source_minimax(
            graph,
            anchors,
            scenario.max_geographic_km,
        )
        scenario_results.append(
            IslandReachabilityScenarioResult(
                scenario_id=scenario.scenario_id,
                max_geographic_km=scenario.max_geographic_km,
                environmental_edge_quantile=scenario.environmental_edge_quantile,
                environmental_threshold=threshold,
                reachable=reachable,
                normalized_geographic_bottleneck=bottleneck,
            )
        )

    reach_matrix = np.vstack([result.reachable for result in scenario_results]).astype(float)
    geo_indices = [
        i for i, result in enumerate(scenario_results)
        if result.environmental_edge_quantile is None
    ]
    env_indices = [
        i for i, result in enumerate(scenario_results)
        if result.environmental_edge_quantile is not None
    ]
    bottleneck_matrix = np.vstack(
        [result.normalized_geographic_bottleneck for result in scenario_results]
    )
    with np.errstate(invalid="ignore"):
        median_bottleneck = np.nanmedian(bottleneck_matrix, axis=0)
    never_connected = ~np.any(np.isfinite(bottleneck_matrix), axis=0)
    median_bottleneck[never_connected] = np.nan

    return IslandReachabilityResult(
        node_ids=ids,
        nearest_anchor_distance_km=nearest,
        connected_frequency=np.mean(reach_matrix, axis=0),
        geography_only_connected_frequency=np.mean(reach_matrix[geo_indices], axis=0),
        environmentally_constrained_connected_frequency=np.mean(reach_matrix[env_indices], axis=0),
        median_normalized_geographic_bottleneck=median_bottleneck,
        scenarios=tuple(scenario_results),
    )
