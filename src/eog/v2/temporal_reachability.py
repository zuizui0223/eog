"""Time-varying finite-world reachability for the active EOG mainline.

This module adds the smallest temporal layer needed to turn a static finite world into
an ordered sequence of already-declared transition operators.  It does not fit time,
calibrate transition support, infer historical dates, or create a new process model.

Each temporal world preserves one operator per declared transition interval.  Source
mass is injected only at the initial state and is never re-injected.  The world-set
summary retains every world trajectory, reports exact-time support envelopes, and
classifies cumulative reachability by declared time as reachable in all worlds,
contingent, or robustly unreachable over the exhaustively enumerated temporal world
set.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from ..dynamic_island_reachability import DynamicTransitionOperator, propagate_dynamic_reachability


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_nonnegative(value: float, label: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class TemporalWorld:
    """One declared time-ordered transition world.

    ``time_labels`` label state snapshots and therefore contain one more entry than
    ``operators``.  They are ordered labels only; no calendar-time or equal-duration
    interpretation is implied.
    """

    world_id: str
    time_labels: tuple[str, ...]
    operators: tuple[DynamicTransitionOperator, ...]
    source_ids: tuple[str, ...]
    source_weights: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        world_id = str(self.world_id).strip()
        if not world_id:
            raise ValueError("world_id must be non-empty")
        object.__setattr__(self, "world_id", world_id)

        labels = tuple(str(value).strip() for value in self.time_labels)
        if len(labels) < 2 or any(not label for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("time_labels must contain at least two unique non-empty labels")
        object.__setattr__(self, "time_labels", labels)

        operators = tuple(self.operators)
        if not operators or len(labels) != len(operators) + 1:
            raise ValueError("time_labels must contain exactly one more entry than operators")
        node_ids = operators[0].node_ids
        if any(operator.node_ids != node_ids for operator in operators[1:]):
            raise ValueError("all temporal operators must share the same node IDs and order")
        object.__setattr__(self, "operators", operators)

        sources = tuple(str(value).strip() for value in self.source_ids)
        if not sources or any(not value for value in sources) or len(set(sources)) != len(sources):
            raise ValueError("source_ids must contain unique non-empty node IDs")
        missing = set(sources).difference(node_ids)
        if missing:
            raise ValueError(f"source_ids are outside the temporal node universe: {sorted(missing)}")
        ordered_sources = tuple(node_id for node_id in node_ids if node_id in set(sources))
        object.__setattr__(self, "source_ids", ordered_sources)

        if self.source_weights is None:
            weights = np.full(len(ordered_sources), 1.0 / len(ordered_sources), dtype=float)
        else:
            declared = np.asarray(self.source_weights, dtype=float)
            if declared.shape != (len(ordered_sources),):
                raise ValueError("source_weights must contain one value per source")
            if not np.isfinite(declared).all() or np.any(declared < 0.0) or float(np.sum(declared)) <= 0.0:
                raise ValueError("source_weights must be finite, non-negative, and sum to > 0")
            weights = declared / np.sum(declared)
        object.__setattr__(self, "source_weights", tuple(float(value) for value in weights))

    @property
    def node_ids(self) -> tuple[str, ...]:
        return self.operators[0].node_ids

    @property
    def source_weight_mapping(self) -> dict[str, float]:
        return dict(zip(self.source_ids, self.source_weights, strict=True))

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "world_id": self.world_id,
                "time_labels": list(self.time_labels),
                "operator_fingerprints": [operator.fingerprint for operator in self.operators],
                "source_ids": list(self.source_ids),
                "source_weights": list(self.source_weights),
            }
        )


@dataclass(frozen=True)
class _TemporalWorldResult:
    world_id: str
    node_ids: tuple[str, ...]
    time_labels: tuple[str, ...]
    mass_by_time: np.ndarray
    reached_by_time: np.ndarray
    lost_mass_by_step: np.ndarray
    edge_flux_by_step: np.ndarray
    first_arrival_step: np.ndarray
    world_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class TemporalFlowSet:
    """Exact finite set of time-varying world trajectories and reachability envelopes."""

    node_ids: tuple[str, ...]
    time_labels: tuple[str, ...]
    world_ids: tuple[str, ...]
    mass_by_world: tuple[np.ndarray, ...]
    reached_by_world: tuple[np.ndarray, ...]
    mass_lower_envelope: np.ndarray
    mass_upper_envelope: np.ndarray
    reachable_in_all_by_time: tuple[tuple[str, ...], ...]
    contingent_by_time: tuple[tuple[str, ...], ...]
    robustly_unreachable_by_time: tuple[tuple[str, ...], ...]
    lost_mass_by_world: tuple[np.ndarray, ...]
    first_arrival_by_world: tuple[np.ndarray, ...]
    coverage_certificate: str
    support_tolerance: float
    world_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


def _propagate_temporal_world(world: TemporalWorld, *, support_tolerance: float) -> _TemporalWorldResult:
    tolerance = _finite_nonnegative(support_tolerance, "support_tolerance")
    bootstrap = propagate_dynamic_reachability(
        world.operators[0],
        world.source_weight_mapping,
        max_steps=1,
        arrival_tolerance=tolerance,
    )
    initial = np.asarray(bootstrap.mass_by_step[0], dtype=float)
    n_steps = len(world.operators)
    n_nodes = len(world.node_ids)
    mass = np.zeros((n_steps + 1, n_nodes), dtype=float)
    mass[0] = initial
    lost = np.zeros(n_steps, dtype=float)
    edge_flux = np.zeros((n_steps, n_nodes, n_nodes), dtype=float)

    for step, operator in enumerate(world.operators):
        current = mass[step]
        edge_flux[step] = current[:, None] * operator.transition
        following = current @ operator.transition
        lost[step] = float(np.sum(current) - np.sum(following))
        mass[step + 1] = following

    positive_exact = mass > tolerance
    reached = np.maximum.accumulate(positive_exact, axis=0)
    first_arrival = np.full(n_nodes, -1, dtype=int)
    for node in range(n_nodes):
        hits = np.flatnonzero(positive_exact[:, node])
        if hits.size:
            first_arrival[node] = int(hits[0])

    payload = {
        "world_fingerprint": world.fingerprint,
        "mass_by_time": mass.tolist(),
        "reached_by_time": reached.tolist(),
        "lost_mass_by_step": lost.tolist(),
        "edge_flux_by_step": edge_flux.tolist(),
        "first_arrival_step": first_arrival.tolist(),
        "support_tolerance": tolerance,
    }
    return _TemporalWorldResult(
        world_id=world.world_id,
        node_ids=world.node_ids,
        time_labels=world.time_labels,
        mass_by_time=mass,
        reached_by_time=reached,
        lost_mass_by_step=lost,
        edge_flux_by_step=edge_flux,
        first_arrival_step=first_arrival,
        world_fingerprint=world.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def build_temporal_flow_set(
    worlds: Sequence[TemporalWorld],
    *,
    support_tolerance: float = 1e-15,
) -> TemporalFlowSet:
    """Propagate an exhaustively declared finite set of time-varying worlds.

    The function assumes the supplied worlds are the temporal world universe to be
    compared.  It does not infer their compatibility from later observations.  All
    worlds must share node IDs, time labels and initial source IDs so that differences
    in the output represent transition-world uncertainty rather than a changing anchor
    definition.

    Reachability classes are cumulative-by-time: once a node has positive support in a
    world, that world counts it as reached at later declared times even if exact-time
    mass subsequently leaves the node.  Exact-time support is retained separately in
    ``mass_by_world`` and the lower/upper mass envelopes.
    """

    declared = tuple(worlds)
    if not declared:
        raise ValueError("at least one temporal world is required")
    ids = [world.world_id for world in declared]
    if len(set(ids)) != len(ids):
        raise ValueError("temporal world IDs must be unique")
    ordered = tuple(sorted(declared, key=lambda world: world.world_id))
    node_ids = ordered[0].node_ids
    labels = ordered[0].time_labels
    sources = ordered[0].source_ids
    if any(world.node_ids != node_ids for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same node IDs and order")
    if any(world.time_labels != labels for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same ordered time labels")
    if any(world.source_ids != sources for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same source IDs")

    tolerance = _finite_nonnegative(support_tolerance, "support_tolerance")
    members = tuple(
        _propagate_temporal_world(world, support_tolerance=tolerance)
        for world in ordered
    )
    mass_stack = np.stack([member.mass_by_time for member in members], axis=0)
    reached_stack = np.stack([member.reached_by_time for member in members], axis=0)
    mass_lower = np.min(mass_stack, axis=0)
    mass_upper = np.max(mass_stack, axis=0)

    universal_by_time: list[tuple[str, ...]] = []
    contingent_by_time: list[tuple[str, ...]] = []
    unreachable_by_time: list[tuple[str, ...]] = []
    for time_index in range(len(labels)):
        at_time = reached_stack[:, time_index, :]
        universal_by_time.append(
            tuple(node_id for node_id, values in zip(node_ids, at_time.T, strict=True) if np.all(values))
        )
        contingent_by_time.append(
            tuple(
                node_id
                for node_id, values in zip(node_ids, at_time.T, strict=True)
                if np.any(values) and not np.all(values)
            )
        )
        unreachable_by_time.append(
            tuple(node_id for node_id, values in zip(node_ids, at_time.T, strict=True) if not np.any(values))
        )

    certificate = "exhaustive_declared_temporal_world_set"
    payload = {
        "world_members": [
            {
                "world_id": member.world_id,
                "world_fingerprint": member.world_fingerprint,
                "result_fingerprint": member.fingerprint,
            }
            for member in members
        ],
        "reachable_in_all_by_time": [list(values) for values in universal_by_time],
        "contingent_by_time": [list(values) for values in contingent_by_time],
        "robustly_unreachable_by_time": [list(values) for values in unreachable_by_time],
        "support_tolerance": tolerance,
        "coverage_certificate": certificate,
    }
    return TemporalFlowSet(
        node_ids=node_ids,
        time_labels=labels,
        world_ids=tuple(member.world_id for member in members),
        mass_by_world=tuple(member.mass_by_time for member in members),
        reached_by_world=tuple(member.reached_by_time for member in members),
        mass_lower_envelope=mass_lower,
        mass_upper_envelope=mass_upper,
        reachable_in_all_by_time=tuple(universal_by_time),
        contingent_by_time=tuple(contingent_by_time),
        robustly_unreachable_by_time=tuple(unreachable_by_time),
        lost_mass_by_world=tuple(member.lost_mass_by_step for member in members),
        first_arrival_by_world=tuple(member.first_arrival_step for member in members),
        coverage_certificate=certificate,
        support_tolerance=tolerance,
        world_fingerprints=tuple((world.world_id, world.fingerprint) for world in ordered),
        fingerprint=_canonical_sha256(payload),
    )
