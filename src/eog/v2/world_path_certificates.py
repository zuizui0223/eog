"""Finite-world path-quantifier audit for declared EOG transition graphs.

Distinguishes 'for all worlds, there exists a path' from 'there exists a
path shared by all worlds', plus world-specific versus globally unavoidable
intermediate nodes. The graph uses raw transition support above a declared
edge floor. This is NOT the mass-based first-passage threshold used by EOG-WF.

This is structural possibility under declared models, not movement history,
biological corridor truth, or an estimate of dispersal probability.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .world_reconstruction import FiniteWorld, FiniteWorldReconstruction


Edge = tuple[str, str]


def _digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _shortest_path(
    active: np.ndarray,
    node_ids: tuple[str, ...],
    source: int,
    target: int,
    max_steps: int,
    *,
    excluded_node: int | None = None,
) -> tuple[str, ...] | None:
    """Deterministic shortest directed path within the finite step cap."""
    if excluded_node in (source, target):
        return None
    queue: deque[tuple[int, ...]] = deque([(source,)])
    visited = {source}
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == target:
            return tuple(node_ids[index] for index in path)
        if len(path) - 1 >= max_steps:
            continue
        for next_index in np.flatnonzero(active[current]):
            neighbour = int(next_index)
            if neighbour == excluded_node or neighbour in visited:
                continue
            visited.add(neighbour)
            queue.append((*path, neighbour))
    return None


@dataclass(frozen=True)
class WorldPathCertificate:
    """Exact structural path properties in a finite compatible world set."""

    source_id: str
    target_id: str
    max_steps: int
    edge_support_floor: float
    world_ids: tuple[str, ...]
    shortest_path_by_world: tuple[tuple[str, tuple[str, ...] | None], ...]
    mandatory_intermediates_by_world: tuple[tuple[str, tuple[str, ...]], ...]
    any_world_reachable: bool
    every_world_reachable: bool
    common_path: tuple[str, ...] | None
    common_path_exists: bool
    necessary_in_every_world: tuple[str, ...]
    necessary_in_some_reachable_worlds: tuple[str, ...]
    shared_active_edges: tuple[Edge, ...]
    coverage_certificate: str
    reconstruction_fingerprint: str
    world_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


def audit_world_path_quantifiers(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
    *,
    source_id: str,
    target_id: str,
    edge_support_floor: float = 0.0,
) -> WorldPathCertificate:
    """Audit world-coherent routes and unavoidable nodes without splicing.

    Every-world reachability permits a different path in each compatible
    world. Common-path existence requires ONE edge sequence feasible in
    every compatible world. The latter implies the former, not vice versa.

    A node is necessary in every world when deleting it prevents reaching
    the target from the selected source in ALL compatible worlds. This
    strong claim is withheld when any world cannot reach the target.

    The raw-edge support floor is not EOG's mass-based arrival tolerance.
    These finite-graph statements are conditional on the declared universe,
    selected fixed source, edge floor, and step cap.
    """
    ordered = tuple(sorted(tuple(worlds), key=lambda w: w.world_id))
    if not ordered:
        raise ValueError("at least one world must be supplied")
    if len({w.world_id for w in ordered}) != len(ordered):
        raise ValueError("world IDs must be unique")
    if tuple((w.world_id, w.fingerprint) for w in ordered) != reconstruction.world_fingerprints:
        raise ValueError("world IDs/fingerprints differ from frozen reconstruction")
    if not reconstruction.compatible_world_ids:
        raise ValueError("no compatible world; path quantifiers are undefined")
    node_ids = ordered[0].operator.node_ids
    if any(w.operator.node_ids != node_ids for w in ordered[1:]):
        raise ValueError("all worlds must use the same ordered node universe")
    floor = float(edge_support_floor)
    if not np.isfinite(floor) or floor < 0.0 or floor >= 1.0:
        raise ValueError("edge_support_floor must lie in [0, 1)")
    if isinstance(reconstruction.max_steps, bool) or reconstruction.max_steps < 1:
        raise ValueError("reconstruction.max_steps must be positive")

    source_id, target_id = str(source_id), str(target_id)
    if source_id not in node_ids or target_id not in node_ids or source_id == target_id:
        raise ValueError("source and target must be distinct declared nodes")
    source = node_ids.index(source_id)
    target = node_ids.index(target_id)
    world_by_id = {w.world_id: w for w in ordered}
    members = tuple(world_by_id[w_id] for w_id in reconstruction.compatible_world_ids)

    paths: list[tuple[str, tuple[str, ...] | None]] = []
    necessities: list[tuple[str, tuple[str, ...]]] = []
    masks: list[np.ndarray] = []
    for world in members:
        weights = world.source_weight_mapping
        if source_id not in weights or weights[source_id] <= 0.0:
            raise ValueError(
                "selected source must have positive weight in every compatible world"
            )
        raw = np.asarray(world.operator.raw_support, dtype=float)
        if raw.shape != (len(node_ids), len(node_ids)) or not np.isfinite(raw).all():
            raise ValueError("each operator must have finite square raw support")
        active = raw > floor
        np.fill_diagonal(active, False)
        masks.append(active)
        route = _shortest_path(active, node_ids, source, target, reconstruction.max_steps)
        paths.append((world.world_id, route))
        if route is None:
            necessities.append((world.world_id, ()))
        else:
            mandatory = tuple(
                node_id for index, node_id in enumerate(node_ids)
                if index not in (source, target)
                and _shortest_path(
                    active, node_ids, source, target, reconstruction.max_steps,
                    excluded_node=index,
                ) is None
            )
            necessities.append((world.world_id, mandatory))

    common_mask = np.logical_and.reduce(masks)
    common_route = _shortest_path(
        common_mask, node_ids, source, target, reconstruction.max_steps
    )
    any_reachable = any(path is not None for _, path in paths)
    all_reachable = all(path is not None for _, path in paths)
    if all_reachable:
        mandatory_sets = [set(nodes) for _, nodes in necessities]
        necessary_every = tuple(
            node_id for node_id in node_ids
            if node_id in set.intersection(*mandatory_sets)
        )
    else:
        necessary_every = ()

    necessary_some_set = set().union(*(set(nodes) for _, nodes in necessities))
    necessary_some = tuple(node_id for node_id in node_ids if node_id in necessary_some_set)
    common_edges = tuple(
        (node_ids[i], node_ids[j])
        for i in range(len(node_ids))
        for j in range(len(node_ids))
        if bool(common_mask[i, j])
    )
    certificate = "exhaustive_declared_compatible_world_structural_paths"
    fingerprints = tuple((world.world_id, world.fingerprint) for world in members)
    payload = {
        "source_id": source_id, "target_id": target_id,
        "max_steps": reconstruction.max_steps, "edge_support_floor": floor,
        "world_fingerprints": [list(row) for row in fingerprints],
        "shortest_path_by_world": [
            [wid, None if path is None else list(path)] for wid, path in paths
        ],
        "mandatory_intermediates_by_world": [
            [wid, list(nodes)] for wid, nodes in necessities
        ],
        "every_world_reachable": all_reachable,
        "any_world_reachable": any_reachable,
        "common_path": None if common_route is None else list(common_route),
        "necessary_in_every_world": list(necessary_every),
        "necessary_in_some_reachable_worlds": list(necessary_some),
        "shared_active_edges": [list(edge) for edge in common_edges],
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "coverage_certificate": certificate,
    }
    return WorldPathCertificate(
        source_id=source_id,
        target_id=target_id,
        max_steps=reconstruction.max_steps,
        edge_support_floor=floor,
        world_ids=tuple(w.world_id for w in members),
        shortest_path_by_world=tuple(paths),
        mandatory_intermediates_by_world=tuple(necessities),
        any_world_reachable=any_reachable,
        every_world_reachable=all_reachable,
        common_path=common_route,
        common_path_exists=common_route is not None,
        necessary_in_every_world=necessary_every,
        necessary_in_some_reachable_worlds=necessary_some,
        shared_active_edges=common_edges,
        coverage_certificate=certificate,
        reconstruction_fingerprint=reconstruction.fingerprint,
        world_fingerprints=fingerprints,
        fingerprint=_digest(payload),
    )
