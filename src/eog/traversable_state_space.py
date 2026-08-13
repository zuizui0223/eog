"""Pathwise traversability of ecological state space between declared populations.

This module implements the upstream layer that EOG v2's transition operator does not
provide. v2 accepts an exogenous per-edge ``environmental_support`` and never requires an
intermediate node to be habitable, so a route through a state the species cannot occupy is
indistinguishable from a route through viable stepping stones. Here node viability and
edge environmental cost are kept as separate objects, and continuous propagation is kept
separate from long-distance jumps rather than being merged into one cost.

Three families of quantity are reported separately and must not be pooled:

- **endpoint** isolation: geographic distance (IBD) and endpoint environmental distance
  (IBE), which depend only on the two populations;
- **pathwise** discontinuity: the minimax environmental step and cumulative environmental
  transition along admissible routes, which depend on what lies between them;
- **transit viability**: the maximin intermediate viability and cumulative niche cost,
  which detect a niche desert that no endpoint comparison can see.

Two populations can share almost identical endpoint niches and still be separated because
every admissible route crosses one large environmental step or one uninhabitable node.
Detecting that case is the purpose of this module.

Scientific boundary: outputs are assumption-dependent graph summaries conditional on a
declared transition hypothesis. They are not colonisation, dispersal or migration
probabilities, not calendar time, and not a reconstructed historical route. A `supported`
status means the declared hypothesis can generate the observed configuration, never that it
did. Held-out labels never enter graph construction, viability or hypothesis declaration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import heapq
import json
import math
from typing import Mapping, Sequence

import numpy as np

EARTH_RADIUS_KM = 6371.0088

#: Node observation states. A blank region is not evidence of absence, so `unsurveyed` is
#: never merged into `surveyed_absent`; see `docs/eog_design_charter.md` section 4.
NODE_STATES = (
    "current_occurrence",
    "historical_occurrence",
    "surveyed_absent",
    "unsurveyed",
)

#: Transition hypothesis kinds. Continuous propagation requires habitable intermediates;
#: a long jump deliberately does not. They are never collapsed into one cost.
HYPOTHESIS_KINDS = ("continuous", "stepping_stone", "long_jump")

#: Reported inference outcomes. `incompatible` is a statement about the declared
#: hypothesis, not about the species.
STATUSES = ("supported", "weakly_supported", "incompatible", "unresolved")


class TraversabilityError(ValueError):
    """Raised when a declared traversability problem is not evaluable."""


@dataclass(frozen=True)
class TransitionHypothesis:
    """One declared rule for which transitions are possible for this species.

    `requires_transit_viability` is the distinction that separates continuous propagation
    from a rare long-distance jump: a continuous hypothesis demands that every intermediate
    node be habitable, while a jump hypothesis permits crossing a niche desert and is
    instead limited by `max_edge_geographic_km`.
    """

    hypothesis_id: str
    kind: str
    max_edge_geographic_km: float
    requires_transit_viability: bool = True
    minimum_transit_viability: float = 0.0
    max_environmental_step: float | None = None
    weak_support_viability: float | None = None
    directed: bool = False

    def __post_init__(self) -> None:
        if not self.hypothesis_id.strip():
            raise TraversabilityError("hypothesis_id must be non-empty")
        if self.kind not in HYPOTHESIS_KINDS:
            raise TraversabilityError(f"kind must be one of {HYPOTHESIS_KINDS}")
        if not np.isfinite(self.max_edge_geographic_km) or self.max_edge_geographic_km <= 0:
            raise TraversabilityError("max_edge_geographic_km must be finite and positive")
        if not 0.0 <= self.minimum_transit_viability <= 1.0:
            raise TraversabilityError("minimum_transit_viability must lie in [0, 1]")
        if self.max_environmental_step is not None and (
            not np.isfinite(self.max_environmental_step) or self.max_environmental_step <= 0
        ):
            raise TraversabilityError("max_environmental_step must be finite and positive")
        if self.weak_support_viability is not None and not 0.0 <= self.weak_support_viability <= 1.0:
            raise TraversabilityError("weak_support_viability must lie in [0, 1]")
        if self.kind == "long_jump" and self.requires_transit_viability:
            raise TraversabilityError(
                "a long_jump hypothesis must not require transit viability; that is what "
                "distinguishes it from continuous propagation"
            )


@dataclass(frozen=True)
class PathwiseIsolation:
    """Separated endpoint, pathwise and transit-viability summaries for one pair."""

    hypothesis_id: str
    hypothesis_kind: str
    source_id: str
    target_id: str
    status: str
    # Endpoint-only quantities; identical across hypotheses.
    geographic_distance_km: float
    endpoint_environmental_distance: float
    # Pathwise quantities under this hypothesis.
    reachable: bool
    reachable_through_surveyed_only: bool
    minimax_environmental_step: float | None
    cumulative_environmental_cost: float | None
    maximin_transit_viability: float | None
    cumulative_niche_cost: float | None
    limiting_edge: tuple[str, str] | None
    limiting_node: str | None


@dataclass(frozen=True)
class TraversabilityResult:
    node_ids: tuple[str, ...]
    hypotheses: tuple[str, ...]
    rows: tuple[PathwiseIsolation, ...]
    fingerprint: str


def _haversine_matrix(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    lat = np.radians(latitudes)[:, None]
    lon = np.radians(longitudes)[:, None]
    dlat = lat - lat.T
    dlon = lon - lon.T
    value = np.sin(dlat / 2.0) ** 2 + np.cos(lat) * np.cos(lat.T) * np.sin(dlon / 2.0) ** 2
    matrix = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.minimum(1.0, np.sqrt(value)))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def _environmental_matrix(values: np.ndarray) -> np.ndarray:
    delta = values[:, None, :] - values[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def _admissible_edges(
    geographic: np.ndarray,
    environmental: np.ndarray,
    hypothesis: TransitionHypothesis,
) -> list[list[int]]:
    """Edges permitted by the hypothesis, before any node-viability restriction."""
    n = geographic.shape[0]
    adjacency: list[list[int]] = [[] for _ in range(n)]
    limit = hypothesis.max_environmental_step
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if geographic[i, j] > hypothesis.max_edge_geographic_km:
                continue
            if limit is not None and environmental[i, j] > limit:
                continue
            adjacency[i].append(j)
    return adjacency


def _can_transit(
    node: int,
    source: int,
    viability: np.ndarray,
    hypothesis: TransitionHypothesis,
    *,
    surveyed_only: bool,
    states: Sequence[str],
) -> bool:
    """Whether a route may pass *through* this node.

    The source is always transitable: it holds the occurrence that defines the route. The
    target is never tested here, because arriving somewhere and establishing there are
    different estimands (`R` versus `P`).
    """
    if node == source:
        return True
    if hypothesis.requires_transit_viability and viability[node] < hypothesis.minimum_transit_viability:
        return False
    if surveyed_only and states[node] == "unsurveyed":
        return False
    return True


def _minimax_environmental_step(
    adjacency: list[list[int]],
    environmental: np.ndarray,
    source: int,
    viability: np.ndarray,
    hypothesis: TransitionHypothesis,
    states: Sequence[str],
    *,
    surveyed_only: bool,
) -> tuple[np.ndarray, list[int | None]]:
    """Minimum over routes of the maximum single environmental step.

    This is the pathwise counterpart of IBE: it answers "what is the largest niche jump
    this route cannot avoid?" rather than "how different are the two endpoints?".
    """
    n = len(adjacency)
    best = np.full(n, math.inf, dtype=float)
    predecessor: list[int | None] = [None] * n
    best[source] = 0.0
    queue: list[tuple[float, int]] = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current > best[node]:
            continue
        if not _can_transit(node, source, viability, hypothesis, surveyed_only=surveyed_only, states=states):
            continue
        for neighbour in adjacency[node]:
            candidate = max(current, float(environmental[node, neighbour]))
            if candidate < best[neighbour]:
                best[neighbour] = candidate
                predecessor[neighbour] = node
                heapq.heappush(queue, (candidate, neighbour))
    return best, predecessor


def _maximin_transit_viability(
    adjacency: list[list[int]],
    source: int,
    viability: np.ndarray,
    hypothesis: TransitionHypothesis,
    states: Sequence[str],
    *,
    surveyed_only: bool,
) -> tuple[np.ndarray, list[int | None]]:
    """Maximum over routes of the minimum viability among *intermediate* nodes.

    A low value means every route is forced through a state the species can barely occupy:
    a niche desert. Endpoint viability is excluded so that this stays a statement about the
    crossing, not about either population.
    """
    n = len(adjacency)
    best = np.full(n, -math.inf, dtype=float)
    floor_node: list[int | None] = [None] * n
    best[source] = math.inf
    queue: list[tuple[float, int]] = [(-math.inf, source)]
    while queue:
        negated, node = heapq.heappop(queue)
        current = -negated
        if current < best[node]:
            continue
        if not _can_transit(node, source, viability, hypothesis, surveyed_only=surveyed_only, states=states):
            continue
        # Leaving `node` means transiting it, unless it is the source itself.
        through = current if node == source else min(current, float(viability[node]))
        limiting = floor_node[node] if (node == source or current <= viability[node]) else node
        for neighbour in adjacency[node]:
            if through > best[neighbour]:
                best[neighbour] = through
                floor_node[neighbour] = limiting
                heapq.heappush(queue, (-through, neighbour))
    return best, floor_node


def _min_cumulative(
    adjacency: list[list[int]],
    source: int,
    viability: np.ndarray,
    hypothesis: TransitionHypothesis,
    states: Sequence[str],
    edge_cost: np.ndarray | None,
    node_cost: np.ndarray | None,
    *,
    surveyed_only: bool,
) -> np.ndarray:
    """Minimum additive route cost over edges, node transits, or both."""
    n = len(adjacency)
    best = np.full(n, math.inf, dtype=float)
    best[source] = 0.0
    queue: list[tuple[float, int]] = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current > best[node]:
            continue
        if not _can_transit(node, source, viability, hypothesis, surveyed_only=surveyed_only, states=states):
            continue
        transit = 0.0 if (node == source or node_cost is None) else float(node_cost[node])
        for neighbour in adjacency[node]:
            step = 0.0 if edge_cost is None else float(edge_cost[node, neighbour])
            candidate = current + transit + step
            if candidate < best[neighbour]:
                best[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    return best


def _trace_limiting_edge(
    predecessor: Sequence[int | None],
    environmental: np.ndarray,
    source: int,
    target: int,
) -> tuple[int, int] | None:
    """Recover the single edge that sets the minimax environmental step."""
    node = target
    worst: tuple[int, int] | None = None
    worst_value = -math.inf
    guard = 0
    while node != source and predecessor[node] is not None:
        previous = predecessor[node]
        assert previous is not None
        value = float(environmental[previous, node])
        if value > worst_value:
            worst_value = value
            worst = (previous, node)
        node = previous
        guard += 1
        if guard > len(predecessor):  # pragma: no cover - defensive
            raise TraversabilityError("predecessor chain did not terminate")
    return worst


def _finite_or_none(value: float) -> float | None:
    return None if not math.isfinite(value) else float(value)


def evaluate_traversability(
    node_ids: Sequence[str],
    latitudes: Sequence[float],
    longitudes: Sequence[float],
    environmental_values: np.ndarray,
    viability: Sequence[float],
    node_states: Mapping[str, str],
    pairs: Sequence[tuple[str, str]],
    hypotheses: Sequence[TransitionHypothesis],
    *,
    niche_epsilon: float = 1e-3,
) -> TraversabilityResult:
    """Evaluate declared population pairs under each declared transition hypothesis.

    `environmental_values` must already be expressed in a shared frozen reference; this
    function does not fit a scaling, because a scaling fitted here would silently change
    what "one environmental step" means between analyses.

    Every declared hypothesis is evaluated and retained. No hypothesis is selected by an
    outcome, and no score is calibrated against observed occupancy.
    """
    ids = tuple(str(value) for value in node_ids)
    n = len(ids)
    if n < 2 or len(set(ids)) != n or any(not value.strip() for value in ids):
        raise TraversabilityError("node_ids must contain at least two unique non-empty IDs")

    lat = np.asarray(latitudes, dtype=float)
    lon = np.asarray(longitudes, dtype=float)
    if lat.shape != (n,) or lon.shape != (n,) or not np.isfinite(lat).all() or not np.isfinite(lon).all():
        raise TraversabilityError("latitudes and longitudes must be finite and align with nodes")
    if np.any((lat < -90) | (lat > 90)) or np.any((lon < -180) | (lon > 180)):
        raise TraversabilityError("coordinates outside latitude/longitude bounds")

    env = np.asarray(environmental_values, dtype=float)
    if env.ndim != 2 or env.shape[0] != n or env.shape[1] < 1 or not np.isfinite(env).all():
        raise TraversabilityError("environmental_values must be a finite node-by-feature matrix")

    via = np.asarray(viability, dtype=float)
    if via.shape != (n,) or not np.isfinite(via).all() or np.any(via < 0.0) or np.any(via > 1.0):
        raise TraversabilityError("viability must be a finite per-node vector in [0, 1]")

    if set(node_states) != set(ids):
        raise TraversabilityError("node_states must declare exactly one state per node")
    states = tuple(str(node_states[node]) for node in ids)
    unknown = sorted({state for state in states if state not in NODE_STATES})
    if unknown:
        raise TraversabilityError(f"unknown node states {unknown}; allowed states are {NODE_STATES}")

    declared = tuple(hypotheses)
    if not declared or len({item.hypothesis_id for item in declared}) != len(declared):
        raise TraversabilityError("hypotheses must be non-empty with unique IDs")
    if not niche_epsilon > 0.0:
        raise TraversabilityError("niche_epsilon must be positive")

    index = {node: position for position, node in enumerate(ids)}
    declared_pairs = tuple((str(a), str(b)) for a, b in pairs)
    if not declared_pairs:
        raise TraversabilityError("at least one population pair is required")
    for a, b in declared_pairs:
        if a not in index or b not in index:
            raise TraversabilityError(f"pair ({a}, {b}) references an unknown node")
        if a == b:
            raise TraversabilityError("population pairs must be distinct")

    geographic = _haversine_matrix(lat, lon)
    environmental = _environmental_matrix(env)
    # Scaled so that a fully viable node costs exactly zero; Dijkstra requires the
    # accumulated transit cost to stay non-negative.
    niche_cost = -np.log(np.clip(via, 0.0, 1.0) * (1.0 - niche_epsilon) + niche_epsilon)

    rows: list[PathwiseIsolation] = []
    for hypothesis in declared:
        adjacency = _admissible_edges(geographic, environmental, hypothesis)
        if not hypothesis.directed:
            # An undirected declaration must not become directional by construction.
            symmetric: list[set[int]] = [set(targets) for targets in adjacency]
            for i, targets in enumerate(adjacency):
                for j in targets:
                    symmetric[j].add(i)
            adjacency = [sorted(targets) for targets in symmetric]

        cache: dict[int, dict[str, object]] = {}
        for source_id, target_id in declared_pairs:
            source = index[source_id]
            target = index[target_id]
            if source not in cache:
                step, predecessor = _minimax_environmental_step(
                    adjacency, environmental, source, via, hypothesis, states, surveyed_only=False
                )
                step_surveyed, _ = _minimax_environmental_step(
                    adjacency, environmental, source, via, hypothesis, states, surveyed_only=True
                )
                floor, floor_node = _maximin_transit_viability(
                    adjacency, source, via, hypothesis, states, surveyed_only=False
                )
                cumulative_env = _min_cumulative(
                    adjacency, source, via, hypothesis, states, environmental, None, surveyed_only=False
                )
                cumulative_niche = _min_cumulative(
                    adjacency, source, via, hypothesis, states, None, niche_cost, surveyed_only=False
                )
                cache[source] = {
                    "step": step,
                    "predecessor": predecessor,
                    "step_surveyed": step_surveyed,
                    "floor": floor,
                    "floor_node": floor_node,
                    "cumulative_env": cumulative_env,
                    "cumulative_niche": cumulative_niche,
                }
            solved = cache[source]
            step = solved["step"]  # type: ignore[assignment]
            reachable = bool(math.isfinite(step[target]))
            reachable_surveyed = bool(math.isfinite(solved["step_surveyed"][target]))  # type: ignore[index]
            floor_value = solved["floor"][target]  # type: ignore[index]
            limiting_node_index = solved["floor_node"][target]  # type: ignore[index]

            if not reachable:
                status = "incompatible"
            elif not reachable_surveyed:
                # Every admissible route depends on a node that was never surveyed, so the
                # connection can be neither supported nor excluded from occurrence data.
                status = "unresolved"
            elif (
                hypothesis.weak_support_viability is not None
                and math.isfinite(floor_value)
                and floor_value < hypothesis.weak_support_viability
            ):
                status = "weakly_supported"
            else:
                status = "supported"

            limiting_edge = None
            if reachable:
                traced = _trace_limiting_edge(solved["predecessor"], environmental, source, target)  # type: ignore[arg-type]
                if traced is not None:
                    limiting_edge = (ids[traced[0]], ids[traced[1]])

            rows.append(
                PathwiseIsolation(
                    hypothesis_id=hypothesis.hypothesis_id,
                    hypothesis_kind=hypothesis.kind,
                    source_id=source_id,
                    target_id=target_id,
                    status=status,
                    geographic_distance_km=float(geographic[source, target]),
                    endpoint_environmental_distance=float(environmental[source, target]),
                    reachable=reachable,
                    reachable_through_surveyed_only=reachable_surveyed,
                    minimax_environmental_step=_finite_or_none(step[target]),
                    cumulative_environmental_cost=_finite_or_none(solved["cumulative_env"][target]),  # type: ignore[index]
                    maximin_transit_viability=_finite_or_none(floor_value),
                    cumulative_niche_cost=_finite_or_none(solved["cumulative_niche"][target]),  # type: ignore[index]
                    limiting_edge=limiting_edge,
                    limiting_node=None if limiting_node_index is None else ids[limiting_node_index],
                )
            )

    payload = {
        "node_ids": list(ids),
        "node_states": list(states),
        "viability": [float(value) for value in via],
        "pairs": [list(pair) for pair in declared_pairs],
        "niche_epsilon": float(niche_epsilon),
        "hypotheses": [
            {
                "hypothesis_id": item.hypothesis_id,
                "kind": item.kind,
                "max_edge_geographic_km": item.max_edge_geographic_km,
                "requires_transit_viability": item.requires_transit_viability,
                "minimum_transit_viability": item.minimum_transit_viability,
                "max_environmental_step": item.max_environmental_step,
                "weak_support_viability": item.weak_support_viability,
                "directed": item.directed,
            }
            for item in declared
        ],
        "rows": [
            {
                key: (list(value) if isinstance(value, tuple) else value)
                for key, value in row.__dict__.items()
            }
            for row in rows
        ],
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return TraversabilityResult(
        node_ids=ids,
        hypotheses=tuple(item.hypothesis_id for item in declared),
        rows=tuple(rows),
        fingerprint=fingerprint,
    )
