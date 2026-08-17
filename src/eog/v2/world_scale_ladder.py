"""Response-blind structural scale ladders for prospective EOG-WF world design.

This module does not infer a biological dispersal distance and does not inspect
species occurrences or responses.  It converts a declared metric-distance matrix
into a nested family of analyst-choice graph scales by asking for the *smallest*
distance threshold at which the graph reaches prospectively declared structural
coverage regimes.

Varying graph thresholds, minimum spanning trees, single-linkage connectivity and
percolation/critical-connectivity ideas are established prior art.  EOG uses that
machinery only as a pre-response world-universe construction discipline: a candidate
universe can contain local, regional and spanning structural worlds instead of
letting every world inherit one arbitrary local site-spacing scale.

No universal coverage fractions are embedded here.  Callers must declare the target
fractions before response access and record why those structural regimes are relevant
to the intended forecast scale.  Thresholds derived here remain analyst-choice scales
unless independently calibrated as biological process parameters.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


_DISTANCE_TOLERANCE = 1e-12


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fraction(value: float, label: str) -> float:
    result = float(value)
    if not np.isfinite(result) or not 0.0 < result <= 1.0:
        raise ValueError(f"{label} must lie in (0, 1]")
    return result


@dataclass(frozen=True)
class StructuralScaleLadderDeclaration:
    """Prospectively declared structural regimes for one metric axis."""

    axis_id: str
    target_largest_component_fractions: tuple[float, ...]

    def __post_init__(self) -> None:
        axis = str(self.axis_id).strip()
        if not axis:
            raise ValueError("axis_id must be non-empty")
        targets = tuple(
            _fraction(value, "target_largest_component_fractions")
            for value in self.target_largest_component_fractions
        )
        if not targets:
            raise ValueError("at least one structural scale target is required")
        if tuple(sorted(set(targets))) != targets:
            raise ValueError(
                "target_largest_component_fractions must be unique and strictly increasing"
            )
        object.__setattr__(self, "axis_id", axis)
        object.__setattr__(self, "target_largest_component_fractions", targets)

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "axis_id": self.axis_id,
                "target_largest_component_fractions": list(
                    self.target_largest_component_fractions
                ),
            }
        )


@dataclass(frozen=True)
class StructuralScaleLevel:
    level_id: str
    target_largest_component_fraction: float
    distance_threshold: float
    achieved_largest_component_fraction: float
    weak_component_count: int
    isolated_node_fraction: float
    directed_edge_count: int
    fingerprint: str


@dataclass(frozen=True)
class StructuralScaleLadder:
    node_ids: tuple[str, ...]
    axis_id: str
    declaration_fingerprint: str
    distance_matrix_fingerprint: str
    levels: tuple[StructuralScaleLevel, ...]
    fingerprint: str

    @property
    def thresholds(self) -> tuple[float, ...]:
        return tuple(level.distance_threshold for level in self.levels)

    @property
    def level_ids(self) -> tuple[str, ...]:
        return tuple(level.level_id for level in self.levels)


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = np.arange(n, dtype=int)
        self.size = np.ones(n, dtype=int)
        self.component_count = n
        self.largest = 1

    def find(self, x: int) -> int:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.component_count -= 1
        self.largest = max(self.largest, int(self.size[ra]))


def _validated_ids(node_ids: Sequence[str]) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in node_ids)
    if not ids or any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("node_ids must contain unique non-empty IDs")
    return ids


def _validated_distance_matrix(values: np.ndarray, n: int) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.shape != (n, n):
        raise ValueError(f"distance matrix must have shape {(n, n)}")
    if not np.isfinite(matrix).all() or np.any(matrix < 0.0):
        raise ValueError("distance matrix must be finite and non-negative")
    if not np.allclose(matrix, matrix.T, atol=1e-12, rtol=1e-12):
        raise ValueError("distance matrix must be symmetric")
    if not np.allclose(np.diag(matrix), 0.0, atol=1e-12, rtol=0.0):
        raise ValueError("distance-matrix diagonal must be zero")
    result = matrix.copy()
    np.fill_diagonal(result, 0.0)
    return result


def _matrix_fingerprint(node_ids: tuple[str, ...], matrix: np.ndarray) -> str:
    return _canonical_sha256(
        {
            "node_ids": list(node_ids),
            "distance_matrix": matrix.tolist(),
        }
    )


def _threshold_adjacency(matrix: np.ndarray, threshold: float) -> np.ndarray:
    adjacency = matrix <= float(threshold) + _DISTANCE_TOLERANCE
    np.fill_diagonal(adjacency, False)
    return adjacency


def _component_summary(adjacency: np.ndarray) -> tuple[int, int, float]:
    n = adjacency.shape[0]
    seen = np.zeros(n, dtype=bool)
    component_sizes: list[int] = []
    for start in range(n):
        if seen[start]:
            continue
        stack = [start]
        seen[start] = True
        size = 0
        while stack:
            node = stack.pop()
            size += 1
            for nxt in np.flatnonzero(adjacency[node]):
                nxt = int(nxt)
                if not seen[nxt]:
                    seen[nxt] = True
                    stack.append(nxt)
        component_sizes.append(size)
    degree = np.sum(adjacency, axis=1)
    return (
        len(component_sizes),
        int(max(component_sizes)),
        float(np.mean(degree == 0)),
    )


def build_structural_scale_ladder(
    node_ids: Sequence[str],
    distance_matrix: np.ndarray,
    declaration: StructuralScaleLadderDeclaration,
) -> StructuralScaleLadder:
    """Build the minimal nested threshold ladder satisfying declared coverage regimes.

    For each target largest-component fraction, the returned threshold is the smallest
    observed pairwise distance at which the threshold graph reaches that target.  Edges
    within the same absolute numerical distance tolerance are admitted together before
    a target is evaluated.  The exact same tolerance is used when threshold adjacencies
    are reconstructed, so an edge used by the union-find scan can never disappear from
    the frozen level.  The resulting thresholds are non-decreasing and the corresponding
    edge sets are nested.
    """

    ids = _validated_ids(node_ids)
    matrix = _validated_distance_matrix(distance_matrix, len(ids))
    n = len(ids)

    rows, cols = np.triu_indices(n, k=1)
    distances = matrix[rows, cols]
    order = np.lexsort((cols, rows, distances))
    rows = rows[order]
    cols = cols[order]
    distances = distances[order]

    uf = _UnionFind(n)
    targets = declaration.target_largest_component_fractions
    thresholds: list[float | None] = [None] * len(targets)
    target_index = 0

    # The empty-edge graph already has largest component fraction 1/n.
    while target_index < len(targets) and (1.0 / n) >= targets[target_index] - 1e-15:
        thresholds[target_index] = 0.0
        target_index += 1

    edge_index = 0
    while edge_index < len(distances) and target_index < len(targets):
        threshold = float(distances[edge_index])
        group_end = edge_index + 1
        while (
            group_end < len(distances)
            and float(distances[group_end]) <= threshold + _DISTANCE_TOLERANCE
        ):
            group_end += 1
        for idx in range(edge_index, group_end):
            uf.union(int(rows[idx]), int(cols[idx]))
        achieved = uf.largest / n
        while target_index < len(targets) and achieved >= targets[target_index] - 1e-15:
            thresholds[target_index] = threshold
            target_index += 1
        edge_index = group_end

    if any(value is None for value in thresholds):
        raise RuntimeError("finite complete distance graph failed to realize a declared target")

    levels: list[StructuralScaleLevel] = []
    previous_threshold = -np.inf
    for index, (target, threshold_value) in enumerate(zip(targets, thresholds, strict=True)):
        threshold = float(threshold_value)
        if threshold + _DISTANCE_TOLERANCE < previous_threshold:
            raise RuntimeError("structural scale thresholds must be non-decreasing")
        previous_threshold = threshold
        adjacency = _threshold_adjacency(matrix, threshold)
        component_count, largest_size, isolated_fraction = _component_summary(adjacency)
        achieved_fraction = largest_size / n
        if achieved_fraction + _DISTANCE_TOLERANCE < target:
            raise RuntimeError("constructed scale level does not satisfy its declared target")
        level_id = f"{declaration.axis_id}_lcc{int(round(target * 1000)):03d}"
        payload = {
            "level_id": level_id,
            "target_largest_component_fraction": target,
            "distance_threshold": threshold,
            "achieved_largest_component_fraction": achieved_fraction,
            "weak_component_count": component_count,
            "isolated_node_fraction": isolated_fraction,
            "directed_edge_count": int(np.sum(adjacency)),
        }
        levels.append(StructuralScaleLevel(**payload, fingerprint=_canonical_sha256(payload)))

    matrix_fingerprint = _matrix_fingerprint(ids, matrix)
    payload = {
        "node_ids": list(ids),
        "axis_id": declaration.axis_id,
        "declaration_fingerprint": declaration.fingerprint,
        "distance_matrix_fingerprint": matrix_fingerprint,
        "levels": [(level.level_id, level.fingerprint) for level in levels],
    }
    return StructuralScaleLadder(
        node_ids=ids,
        axis_id=declaration.axis_id,
        declaration_fingerprint=declaration.fingerprint,
        distance_matrix_fingerprint=matrix_fingerprint,
        levels=tuple(levels),
        fingerprint=_canonical_sha256(payload),
    )


def structural_scale_adjacencies(
    ladder: StructuralScaleLadder,
    distance_matrix: np.ndarray,
) -> dict[str, np.ndarray]:
    """Reconstruct nested adjacency matrices for a frozen structural scale ladder."""

    matrix = _validated_distance_matrix(distance_matrix, len(ladder.node_ids))
    if _matrix_fingerprint(ladder.node_ids, matrix) != ladder.distance_matrix_fingerprint:
        raise ValueError("distance matrix or node order differs from the frozen ladder")
    return {
        level.level_id: _threshold_adjacency(matrix, level.distance_threshold)
        for level in ladder.levels
    }


def compose_intersection_worlds(
    primary_worlds: Mapping[str, np.ndarray],
    secondary_worlds: Mapping[str, np.ndarray],
    *,
    include_primary_only: bool = True,
) -> dict[str, np.ndarray]:
    """Compose two response-blind structural axes without hiding their identities.

    The operation is deliberately simple intersection of admitted edges.  It is world
    enumeration infrastructure, not a claim that either axis is a biological tolerance
    function.  Primary-only worlds can be retained so that restrictive secondary-axis
    intersections do not force the entire universe into one fragmented structural
    regime.
    """

    if not primary_worlds:
        raise ValueError("primary_worlds must not be empty")
    first = np.asarray(next(iter(primary_worlds.values())))
    if first.ndim != 2 or first.shape[0] != first.shape[1]:
        raise ValueError("world adjacency matrices must be square")
    n = first.shape[0]

    def normalized(mapping: Mapping[str, np.ndarray], label: str) -> dict[str, np.ndarray]:
        result: dict[str, np.ndarray] = {}
        for world_id in sorted(mapping):
            name = str(world_id).strip()
            if not name:
                raise ValueError(f"{label} world IDs must be non-empty")
            values = np.asarray(mapping[world_id], dtype=bool)
            if values.shape != (n, n):
                raise ValueError(f"{label} world {name!r} has incompatible shape")
            values = values.copy()
            np.fill_diagonal(values, False)
            result[name] = values
        return result

    primary = normalized(primary_worlds, "primary")
    secondary = normalized(secondary_worlds, "secondary")
    result: dict[str, np.ndarray] = {}
    if include_primary_only:
        for primary_id, adjacency in primary.items():
            result[f"primary::{primary_id}"] = adjacency.copy()
    for primary_id, primary_adjacency in primary.items():
        for secondary_id, secondary_adjacency in secondary.items():
            result[f"primary::{primary_id}|secondary::{secondary_id}"] = (
                primary_adjacency & secondary_adjacency
            )
    return result
