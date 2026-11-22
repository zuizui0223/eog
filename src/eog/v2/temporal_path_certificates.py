"""Time-coherent finite-world route and waypoint audit.

A temporal route uses one frozen world for *all* intervals. No source mass
reinjection, implicit waiting, world swapping, or per-interval union is allowed.
This is raw-positive-support graph logic, not the EOG-WF mass-threshold forecast.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .temporal_reachability import TemporalFlowSet, TemporalWorld


TimedState = tuple[str, str]
Edge = tuple[str, str]


def _fingerprint(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _time_path(
    masks: Sequence[np.ndarray],
    node_ids: tuple[str, ...],
    labels: tuple[str, ...],
    source: int,
    target: int,
    horizon: int,
    *,
    blocked_node: int | None = None,
    blocked_state: tuple[int, int] | None = None,
) -> tuple[TimedState, ...] | None:
    """Earliest-arrival witness in a time-expanded DAG, allowing spatial revisits.

    Exactly one directed transition occurs per interval before arrival.
    There are no implicit waiting/self edges; a return to an earlier node
    in a later interval is permitted. Among same-time witnesses choose
    the lexicographically smallest node-index sequence.
    """
    if blocked_node == source or blocked_state == (0, source):
        return None
    frontier: dict[int, tuple[int, ...]] = {source: (source,)}
    if source == target:
        return ((labels[0], node_ids[source]),)
    for step in range(horizon):
        later: dict[int, tuple[int, ...]] = {}
        for node, path in sorted(frontier.items()):
            for candidate in np.flatnonzero(masks[step][node]):
                successor = int(candidate)
                if successor == blocked_node or (step + 1, successor) == blocked_state:
                    continue
                proposal = (*path, successor)
                if successor not in later or proposal < later[successor]:
                    later[successor] = proposal
        if target in later:
            return tuple(
                (labels[i], node_ids[at_node])
                for i, at_node in enumerate(later[target])
            )
        frontier = later
        if not frontier:
            break
    return None


@dataclass(frozen=True)
class TemporalPathCertificate:
    """Structural, finite-universe and time-indexed route certificate."""

    source_id: str
    target_id: str
    horizon_index: int
    horizon_label: str
    edge_support_floor: float
    world_ids: tuple[str, ...]
    shortest_time_path_by_world: tuple[
        tuple[str, tuple[TimedState, ...] | None], ...
    ]
    mandatory_waypoints_by_world: tuple[tuple[str, tuple[str, ...]], ...]
    mandatory_timed_states_by_world: tuple[
        tuple[str, tuple[TimedState, ...]], ...
    ]
    any_world_reachable: bool
    every_world_reachable: bool
    common_time_path: tuple[TimedState, ...] | None
    common_time_path_exists: bool
    necessary_waypoints_in_every_world: tuple[str, ...]
    necessary_timed_states_in_every_world: tuple[TimedState, ...]
    necessary_waypoints_in_some_worlds: tuple[str, ...]
    shared_edges_by_interval: tuple[tuple[Edge, ...], ...]
    mass_based_target_status: str
    structural_mass_status_agreement: bool
    coverage_certificate: str
    flow_fingerprint: str
    world_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


def audit_temporal_path_quantifiers(
    flow: TemporalFlowSet,
    worlds: Sequence[TemporalWorld],
    *,
    source_id: str,
    target_id: str,
    horizon_index: int | None = None,
    edge_support_floor: float = 0.0,
) -> TemporalPathCertificate:
    """Distinguish temporal accessibility, common routes and necessary states.

    The already-declared TemporalFlowSet is the identity/provenance lock.
    All its worlds must be supplied unchanged, with the same time and node
    indices; no post-outcome selection or alternative-world edge pooling.

    "Reached by horizon" means positive path support at *some* time up to
    the cutoff (cumulative first arrival), not necessarily remaining at
    the destination at the cutoff. Waiting is forbidden unless an explicit
    edge is declared by a future process contract (current operators do
    not permit self edges).

    This audit uses raw edge support > edge_support_floor, unlike the
    mass-based support_tolerance in build_temporal_flow_set. Therefore
    structural and numerical reachability can disagree; the result
    reports that disagreement instead of silently certifying agreement.
    """
    declared = tuple(sorted(tuple(worlds), key=lambda w: w.world_id))
    if not declared or len({w.world_id for w in declared}) != len(declared):
        raise ValueError("worlds must be a nonempty sequence of unique temporal IDs")
    definitions = tuple((w.world_id, w.fingerprint) for w in declared)
    if definitions != flow.world_fingerprints or tuple(w.world_id for w in declared) != flow.world_ids:
        raise ValueError("world IDs/fingerprints differ from frozen temporal flow")
    node_ids, labels = flow.node_ids, flow.time_labels
    if any(w.node_ids != node_ids or w.time_labels != labels for w in declared):
        raise ValueError("world node/time definitions must match temporal flow")

    floor = float(edge_support_floor)
    if not np.isfinite(floor) or floor < 0.0 or floor >= 1.0:
        raise ValueError("edge_support_floor must be finite and in [0, 1)")
    h = len(labels) - 1 if horizon_index is None else horizon_index
    if isinstance(h, bool) or not isinstance(h, int) or not 0 <= h < len(labels):
        raise ValueError("horizon_index must be an integer within the time labels")

    source_id, target_id = str(source_id), str(target_id)
    if source_id not in node_ids or target_id not in node_ids or source_id == target_id:
        raise ValueError("source and target must be distinct declared node IDs")
    source, target = node_ids.index(source_id), node_ids.index(target_id)
    for world in declared:
        if world.source_weight_mapping.get(source_id, 0.0) <= 0.0:
            raise ValueError(
                "selected source must have positive declared mass in every temporal world"
            )

    n_nodes = len(node_ids)
    waypoint_indices = tuple(i for i in range(n_nodes) if i not in (source, target))
    timed_candidates = tuple(
        (step, i)
        for step in range(1, h)
        for i in waypoint_indices
    )
    path_by_world: list[tuple[str, tuple[TimedState, ...] | None]] = []
    mandatory_by_world: list[tuple[str, tuple[str, ...]]] = []
    timed_mandatory_by_world: list[tuple[str, tuple[TimedState, ...]]] = []
    masks_by_world: list[tuple[np.ndarray, ...]] = []

    for world in declared:
        masks: list[np.ndarray] = []
        for operator in world.operators[:h]:
            raw = np.asarray(operator.raw_support, dtype=float)
            if raw.shape != (n_nodes, n_nodes) or not np.isfinite(raw).all():
                raise ValueError("operator raw support must be a finite square matrix")
            active = raw > floor
            np.fill_diagonal(active, False)
            masks.append(active)
        fixed_masks = tuple(masks)
        masks_by_world.append(fixed_masks)
        witness = _time_path(fixed_masks, node_ids, labels, source, target, h)
        path_by_world.append((world.world_id, witness))
        if witness is None:
            mandatory_by_world.append((world.world_id, ()))
            timed_mandatory_by_world.append((world.world_id, ()))
            continue
        mandatory = tuple(
            node_ids[index]
            for index in waypoint_indices
            if _time_path(
                fixed_masks, node_ids, labels, source, target, h,
                blocked_node=index,
            ) is None
        )
        time_mandatory = tuple(
            (labels[step], node_ids[index])
            for step, index in timed_candidates
            if _time_path(
                fixed_masks, node_ids, labels, source, target, h,
                blocked_state=(step, index),
            ) is None
        )
        mandatory_by_world.append((world.world_id, mandatory))
        timed_mandatory_by_world.append((world.world_id, time_mandatory))

    common_masks = tuple(
        np.logical_and.reduce([masks[step] for masks in masks_by_world])
        for step in range(h)
    )
    common_witness = _time_path(
        common_masks, node_ids, labels, source, target, h
    )
    some_reached = any(p is not None for _, p in path_by_world)
    all_reached = all(p is not None for _, p in path_by_world)
    all_waypoint_sets = [set(nodes) for _, nodes in mandatory_by_world]
    all_timed_sets = [set(states) for _, states in timed_mandatory_by_world]
    if all_reached:
        universally_mandatory = tuple(
            node_ids[index]
            for index in waypoint_indices
            if all(node_ids[index] in nodes for nodes in all_waypoint_sets)
        )
        universal_states = tuple(
            (labels[step], node_ids[index])
            for step, index in timed_candidates
            if all((labels[step], node_ids[index]) in states for states in all_timed_sets)
        )
    else:
        universally_mandatory, universal_states = (), ()

    some_waypoints_set = set().union(*all_waypoint_sets)
    some_waypoints = tuple(
        node_ids[index]
        for index in waypoint_indices if node_ids[index] in some_waypoints_set
    )
    shared_edges = tuple(
        tuple(
            (node_ids[i], node_ids[j])
            for i in range(n_nodes) for j in range(n_nodes)
            if common_masks[step][i, j]
        )
        for step in range(h)
    )
    if target_id in flow.reachable_in_all_by_time[h]:
        mass_status = "reachable_in_all"
    elif target_id in flow.contingent_by_time[h]:
        mass_status = "contingent"
    else:
        mass_status = "robustly_unreachable"
    structural_status = (
        "reachable_in_all" if all_reached
        else "contingent" if some_reached
        else "robustly_unreachable"
    )
    certificate = "exhaustive_declared_temporal_world_paths"
    payload = {
        "source_id": source_id,
        "target_id": target_id,
        "horizon_index": h,
        "horizon_label": labels[h],
        "edge_support_floor": floor,
        "world_fingerprints": [list(row) for row in definitions],
        "path_by_world": [
            [w, None if path is None else [list(t) for t in path]]
            for w, path in path_by_world
        ],
        "mandatory_by_world": [[w, list(nodes)] for w, nodes in mandatory_by_world],
        "timed_mandatory_by_world": [
            [w, [list(t) for t in states]] for w, states in timed_mandatory_by_world
        ],
        "common_time_path": None if common_witness is None else [list(t) for t in common_witness],
        "necessary_waypoints_in_every_world": list(universally_mandatory),
        "necessary_timed_states_in_every_world": [list(x) for x in universal_states],
        "shared_edges_by_interval": [
            [list(edge) for edge in edges] for edges in shared_edges
        ],
        "mass_based_target_status": mass_status,
        "structural_mass_status_agreement": structural_status == mass_status,
        "flow_fingerprint": flow.fingerprint,
        "coverage_certificate": certificate,
    }
    return TemporalPathCertificate(
        source_id=source_id,
        target_id=target_id,
        horizon_index=h,
        horizon_label=labels[h],
        edge_support_floor=floor,
        world_ids=flow.world_ids,
        shortest_time_path_by_world=tuple(path_by_world),
        mandatory_waypoints_by_world=tuple(mandatory_by_world),
        mandatory_timed_states_by_world=tuple(timed_mandatory_by_world),
        any_world_reachable=some_reached,
        every_world_reachable=all_reached,
        common_time_path=common_witness,
        common_time_path_exists=common_witness is not None,
        necessary_waypoints_in_every_world=universally_mandatory,
        necessary_timed_states_in_every_world=universal_states,
        necessary_waypoints_in_some_worlds=some_waypoints,
        shared_edges_by_interval=shared_edges,
        mass_based_target_status=mass_status,
        structural_mass_status_agreement=structural_status == mass_status,
        coverage_certificate=certificate,
        flow_fingerprint=flow.fingerprint,
        world_fingerprints=definitions,
        fingerprint=_fingerprint(payload),
    )
