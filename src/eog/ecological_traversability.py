"""Prospective ecological-traversability primitives for EOG v2.

The objects in this module separate endpoint environmental similarity from pathwise
environmental continuity and intermediate viability. They are assumption-conditioned
support diagnostics, not historical-route, dispersal, colonisation, migration, or
occupancy probabilities.

Occurrence configurations are used here only to define a reproducible descriptive
scale in environmental-state space. Pairwise occurrence spacing is *not* interpreted
as an observed transition or movement event.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Sequence

import numpy as np

from .dynamic_island_reachability import DynamicReachabilityEdge


DispersalMode = Literal["continuous", "long_jump"]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_state_matrix(values: np.ndarray | Sequence[Sequence[float]], label: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError(f"{label} must be a two-dimensional matrix with at least two rows")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{label} must contain only finite values")
    return matrix


@dataclass(frozen=True)
class OccurrenceEnvironmentalScale:
    """Descriptive environmental-state spacing scale from observed occurrences.

    ``nearest_neighbor_distances`` are environmental Euclidean distances from every
    observed state to its nearest *other* observed state. ``transition_scale`` is a
    declared quantile of those distances. The object supplies a reproducible scale for
    later transition hypotheses; it does not assert that nearest occurrences exchanged
    migrants or represent consecutive historical states.
    """

    quantile: float
    nearest_neighbor_distances: tuple[float, ...]
    transition_scale: float
    fingerprint: str


def fit_occurrence_environmental_scale(
    occurrence_states: np.ndarray | Sequence[Sequence[float]],
    *,
    quantile: float = 0.90,
) -> OccurrenceEnvironmentalScale:
    """Fit an order-invariant descriptive scale from occurrence environmental states."""

    states = _finite_state_matrix(occurrence_states, "occurrence_states")
    if not np.isfinite(quantile) or not 0.0 < float(quantile) <= 1.0:
        raise ValueError("quantile must lie in (0, 1]")

    delta = states[:, None, :] - states[None, :, :]
    distances = np.linalg.norm(delta, axis=2)
    np.fill_diagonal(distances, np.inf)
    nearest = np.min(distances, axis=1)
    scale = float(np.quantile(nearest, float(quantile)))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError(
            "occurrence states do not identify a positive environmental spacing scale"
        )

    ordered_nearest = tuple(float(value) for value in np.sort(nearest))
    payload = {
        "quantile": float(quantile),
        "nearest_neighbor_distances": list(ordered_nearest),
        "transition_scale": scale,
    }
    return OccurrenceEnvironmentalScale(
        quantile=float(quantile),
        nearest_neighbor_distances=ordered_nearest,
        transition_scale=scale,
        fingerprint=_canonical_sha256(payload),
    )


def environmental_transition_support(distance: float, *, scale: float) -> float:
    """Map a non-negative environmental-state transition distance to relative support."""

    if not np.isfinite(distance) or distance < 0.0:
        raise ValueError("distance must be finite and non-negative")
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("scale must be finite and positive")
    return float(math.exp(-float(distance) / float(scale)))


@dataclass(frozen=True)
class EcologicalTransitionEdge:
    """One directed transition with ecological continuity kept auditable.

    ``transit_viability`` is an explicitly declared support in ``[0, 1]`` for the
    ecological state that must be occupied during continuous propagation. For a
    ``long_jump`` edge it remains recorded but is not multiplied into transition
    support, because the hypothesis is that the unsampled/nonviable intermediate
    landscape can be bypassed. Rarity of long jumps should instead be encoded in the
    geographic or directional support supplied for that edge.
    """

    source: int
    target: int
    geographic_support: float
    environmental_distance: float
    transit_viability: float
    barrier_support: float = 1.0
    directional_support: float = 1.0
    target_capture_support: float = 1.0
    dispersal_mode: DispersalMode = "continuous"

    def __post_init__(self) -> None:
        if self.source < 0 or self.target < 0 or self.source == self.target:
            raise ValueError("edge endpoints must be distinct non-negative indices")
        supports = (
            self.geographic_support,
            self.transit_viability,
            self.barrier_support,
            self.directional_support,
            self.target_capture_support,
        )
        if not all(np.isfinite(supports)) or any(value < 0.0 or value > 1.0 for value in supports):
            raise ValueError("edge support components must be finite and lie in [0, 1]")
        if not np.isfinite(self.environmental_distance) or self.environmental_distance < 0.0:
            raise ValueError("environmental_distance must be finite and non-negative")
        if self.dispersal_mode not in {"continuous", "long_jump"}:
            raise ValueError("dispersal_mode must be 'continuous' or 'long_jump'")

    def environmental_support(self, *, scale: float) -> float:
        return environmental_transition_support(self.environmental_distance, scale=scale)

    def effective_environmental_support(self, *, scale: float) -> float:
        support = self.environmental_support(scale=scale)
        if self.dispersal_mode == "continuous":
            support *= self.transit_viability
        return float(support)

    def to_dynamic_edge(self, *, scale: float) -> DynamicReachabilityEdge:
        """Convert to the existing v2 dynamic operator without changing frozen v2 edges."""

        return DynamicReachabilityEdge(
            source=self.source,
            target=self.target,
            geographic_support=self.geographic_support,
            environmental_support=self.effective_environmental_support(scale=scale),
            barrier_support=self.barrier_support,
            directional_support=self.directional_support,
            target_capture_support=self.target_capture_support,
        )


@dataclass(frozen=True)
class TraversabilityTransitionBundle:
    """Separated ecological edges plus their dynamic-operator representation."""

    environmental_scale: float
    scale_source_fingerprint: str | None
    edges: tuple[EcologicalTransitionEdge, ...]
    dynamic_edges: tuple[DynamicReachabilityEdge, ...]
    fingerprint: str


def build_traversability_transition_bundle(
    edges: Sequence[EcologicalTransitionEdge],
    *,
    environmental_scale: float | OccurrenceEnvironmentalScale,
) -> TraversabilityTransitionBundle:
    """Freeze ecological transition assumptions before building an EOG-R operator."""

    ecological_edges = tuple(edges)
    if not ecological_edges:
        raise ValueError("at least one ecological transition edge is required")
    if isinstance(environmental_scale, OccurrenceEnvironmentalScale):
        scale = environmental_scale.transition_scale
        scale_source = environmental_scale.fingerprint
    else:
        scale = float(environmental_scale)
        scale_source = None
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("environmental_scale must be finite and positive")

    dynamic_edges = tuple(edge.to_dynamic_edge(scale=scale) for edge in ecological_edges)
    payload = {
        "environmental_scale": scale,
        "scale_source_fingerprint": scale_source,
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "geographic_support": edge.geographic_support,
                "environmental_distance": edge.environmental_distance,
                "transit_viability": edge.transit_viability,
                "barrier_support": edge.barrier_support,
                "directional_support": edge.directional_support,
                "target_capture_support": edge.target_capture_support,
                "dispersal_mode": edge.dispersal_mode,
                "environmental_support": edge.environmental_support(scale=scale),
                "effective_environmental_support": edge.effective_environmental_support(scale=scale),
            }
            for edge in ecological_edges
        ],
    }
    return TraversabilityTransitionBundle(
        environmental_scale=scale,
        scale_source_fingerprint=scale_source,
        edges=ecological_edges,
        dynamic_edges=dynamic_edges,
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class PathTraversabilitySummary:
    """Endpoint-versus-path ecological discontinuity for one declared route."""

    path: tuple[int, ...]
    endpoint_environmental_distance: float
    cumulative_environmental_crossing: float
    environmental_bottleneck: float
    minimum_intermediate_viability: float | None
    niche_desert_penalty: float
    long_jump_edge_count: int
    fingerprint: str


def summarize_path_traversability(
    environmental_states: np.ndarray | Sequence[Sequence[float]],
    viability_support: Sequence[float] | np.ndarray,
    path: Sequence[int],
    *,
    dispersal_modes: Sequence[DispersalMode] | None = None,
    viability_floor: float = 1e-12,
) -> PathTraversabilitySummary:
    """Summarize pathwise environmental crossing separately from endpoint IBE.

    ``viability_support`` is evaluated only for explicit intermediate nodes in the
    declared path. A direct long-jump edge therefore bypasses any unsampled states that
    are not represented as nodes. ``niche_desert_penalty`` is the sum of negative log
    support over explicit intermediate nodes and remains a descriptive path diagnostic.
    """

    states = _finite_state_matrix(environmental_states, "environmental_states")
    viability = np.asarray(viability_support, dtype=float)
    if viability.shape != (len(states),) or not np.isfinite(viability).all():
        raise ValueError("viability_support must be finite and aligned to environmental_states")
    if np.any(viability < 0.0) or np.any(viability > 1.0):
        raise ValueError("viability_support must lie in [0, 1]")

    route = tuple(int(value) for value in path)
    if len(route) < 2 or any(value < 0 or value >= len(states) for value in route):
        raise ValueError("path must contain at least two valid node indices")
    if any(a == b for a, b in zip(route, route[1:])):
        raise ValueError("path cannot contain self transitions")

    if dispersal_modes is None:
        modes: tuple[DispersalMode, ...] = tuple("continuous" for _ in range(len(route) - 1))
    else:
        modes = tuple(dispersal_modes)
        if len(modes) != len(route) - 1:
            raise ValueError("dispersal_modes must contain one value per path edge")
        if any(mode not in {"continuous", "long_jump"} for mode in modes):
            raise ValueError("dispersal_modes values must be 'continuous' or 'long_jump'")

    transitions = np.asarray(
        [np.linalg.norm(states[a] - states[b]) for a, b in zip(route, route[1:])],
        dtype=float,
    )
    endpoint = float(np.linalg.norm(states[route[0]] - states[route[-1]]))
    intermediate = np.asarray(route[1:-1], dtype=int)
    if intermediate.size:
        intermediate_viability = viability[intermediate]
        minimum_viability: float | None = float(np.min(intermediate_viability))
        if not np.isfinite(viability_floor) or not 0.0 < viability_floor < 1.0:
            raise ValueError("viability_floor must lie strictly between 0 and 1")
        niche_penalty = float(np.sum(-np.log(np.maximum(intermediate_viability, viability_floor))))
    else:
        minimum_viability = None
        niche_penalty = 0.0

    payload = {
        "path": list(route),
        "endpoint_environmental_distance": endpoint,
        "cumulative_environmental_crossing": float(np.sum(transitions)),
        "environmental_bottleneck": float(np.max(transitions)),
        "minimum_intermediate_viability": minimum_viability,
        "niche_desert_penalty": niche_penalty,
        "dispersal_modes": list(modes),
        "long_jump_edge_count": int(sum(mode == "long_jump" for mode in modes)),
    }
    return PathTraversabilitySummary(
        path=route,
        endpoint_environmental_distance=endpoint,
        cumulative_environmental_crossing=float(np.sum(transitions)),
        environmental_bottleneck=float(np.max(transitions)),
        minimum_intermediate_viability=minimum_viability,
        niche_desert_penalty=niche_penalty,
        long_jump_edge_count=int(sum(mode == "long_jump" for mode in modes)),
        fingerprint=_canonical_sha256(payload),
    )
