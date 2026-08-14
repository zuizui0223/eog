"""Positive-observation reconstruction for finite temporal EOG worlds.

This module treats time-stamped positive occurrences as necessary reachability
constraints on an already-declared finite set of :class:`TemporalWorld` objects.  It
does not infer absence from non-detection, does not model persistence, and does not
turn ordered time labels into calibrated calendar time.

An observation ``(node_id, time_label)`` is compatible with a temporal world when that
node has received positive reachability support at or before the declared time.  The
use of cumulative ``reached by time`` rather than exact-time mass is deliberate: in the
absence of a persistence/occupancy model, the temporal layer can certify a necessary
reachability condition but cannot claim that propagated mass represents presence at the
observation time.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .temporal_reachability import TemporalWorld, build_temporal_flow_set


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


def _canonical_observations(
    node_ids: tuple[str, ...],
    time_labels: tuple[str, ...],
    observations: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    declared = tuple((str(node).strip(), str(time).strip()) for node, time in observations)
    if not declared:
        raise ValueError("at least one time-stamped positive occurrence is required")
    if any(not node or not time for node, time in declared):
        raise ValueError("time-stamped occurrence node/time labels must be non-empty")
    if len(set(declared)) != len(declared):
        raise ValueError("time-stamped positive occurrences must be unique")

    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    time_index = {time_label: i for i, time_label in enumerate(time_labels)}
    missing_nodes = sorted({node for node, _ in declared if node not in node_index})
    if missing_nodes:
        raise ValueError(f"observations contain nodes outside the temporal world universe: {missing_nodes}")
    missing_times = sorted({time for _, time in declared if time not in time_index})
    if missing_times:
        raise ValueError(f"observations contain undeclared time labels: {missing_times}")

    return tuple(sorted(declared, key=lambda row: (time_index[row[1]], node_index[row[0]])))


@dataclass(frozen=True)
class TemporalWorldReconstruction:
    """Exact finite inverse set under time-stamped positive reachability constraints."""

    observations: tuple[tuple[str, str], ...]
    compatible_world_ids: tuple[str, ...]
    incompatible_world_ids: tuple[str, ...]
    unsupported_observations_by_world: tuple[
        tuple[str, tuple[tuple[str, str], ...]], ...
    ]
    world_fingerprints: tuple[tuple[str, str], ...]
    compatible_fraction: float
    identifiable: bool
    support_tolerance: float
    coverage_certificate: str
    fingerprint: str


@dataclass(frozen=True)
class TemporalReconstructionUpdate:
    """Contraction of a frozen temporal-world set after added positive evidence."""

    before_observations: tuple[tuple[str, str], ...]
    after_observations: tuple[tuple[str, str], ...]
    retained_world_ids: tuple[str, ...]
    eliminated_world_ids: tuple[str, ...]
    contraction_fraction: float
    became_identifiable: bool
    before_fingerprint: str
    after_fingerprint: str
    fingerprint: str


def reconstruct_temporal_worlds(
    worlds: Sequence[TemporalWorld],
    observations: Sequence[tuple[str, str]],
    *,
    support_tolerance: float = 1e-15,
) -> TemporalWorldReconstruction:
    """Return temporal worlds satisfying every declared positive occurrence constraint.

    Compatibility is a necessary *reachability-by-time* condition. A node that was
    reached at an earlier step remains compatible with a later positive observation
    even when exact-time propagated mass has subsequently left that node. Persistence
    requires a separate ecological model and is intentionally not invented here.
    """

    tolerance = _finite_nonnegative(support_tolerance, "support_tolerance")
    flow_set = build_temporal_flow_set(worlds, support_tolerance=tolerance)
    canonical = _canonical_observations(flow_set.node_ids, flow_set.time_labels, observations)
    node_index = {node_id: i for i, node_id in enumerate(flow_set.node_ids)}
    time_index = {time_label: i for i, time_label in enumerate(flow_set.time_labels)}

    unsupported_rows: list[tuple[str, tuple[tuple[str, str], ...]]] = []
    compatible: list[str] = []
    incompatible: list[str] = []
    for world_id, reached in zip(flow_set.world_ids, flow_set.reached_by_world, strict=True):
        unsupported = tuple(
            observation
            for observation in canonical
            if not bool(reached[time_index[observation[1]], node_index[observation[0]]])
        )
        unsupported_rows.append((world_id, unsupported))
        if unsupported:
            incompatible.append(world_id)
        else:
            compatible.append(world_id)

    certificate = "exhaustive_declared_temporal_world_set_positive_observations"
    payload = {
        "observations": [list(row) for row in canonical],
        "world_fingerprints": [list(row) for row in flow_set.world_fingerprints],
        "unsupported_observations_by_world": [
            [world_id, [list(row) for row in unsupported]]
            for world_id, unsupported in unsupported_rows
        ],
        "support_tolerance": tolerance,
        "coverage_certificate": certificate,
    }
    return TemporalWorldReconstruction(
        observations=canonical,
        compatible_world_ids=tuple(compatible),
        incompatible_world_ids=tuple(incompatible),
        unsupported_observations_by_world=tuple(unsupported_rows),
        world_fingerprints=flow_set.world_fingerprints,
        compatible_fraction=float(len(compatible) / len(flow_set.world_ids)),
        identifiable=len(compatible) == 1,
        support_tolerance=tolerance,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )


def compare_temporal_reconstructions(
    before: TemporalWorldReconstruction,
    after: TemporalWorldReconstruction,
) -> TemporalReconstructionUpdate:
    """Quantify compatible-world contraction after adding positive temporal evidence."""

    if before.world_fingerprints != after.world_fingerprints:
        raise ValueError("temporal reconstructions must use the same frozen world universe")
    if before.support_tolerance != after.support_tolerance:
        raise ValueError("temporal reconstructions must use the same support tolerance")
    if not set(before.observations).issubset(after.observations):
        raise ValueError("after observations must include every before observation")

    before_worlds = set(before.compatible_world_ids)
    after_worlds = set(after.compatible_world_ids)
    if not after_worlds.issubset(before_worlds):
        raise RuntimeError("adding positive occurrence constraints must not create compatible worlds")

    retained = tuple(world_id for world_id in before.compatible_world_ids if world_id in after_worlds)
    eliminated = tuple(world_id for world_id in before.compatible_world_ids if world_id not in after_worlds)
    contraction = 0.0 if not before.compatible_world_ids else float(
        len(eliminated) / len(before.compatible_world_ids)
    )
    payload = {
        "before_fingerprint": before.fingerprint,
        "after_fingerprint": after.fingerprint,
        "retained_world_ids": list(retained),
        "eliminated_world_ids": list(eliminated),
        "contraction_fraction": contraction,
    }
    return TemporalReconstructionUpdate(
        before_observations=before.observations,
        after_observations=after.observations,
        retained_world_ids=retained,
        eliminated_world_ids=eliminated,
        contraction_fraction=contraction,
        became_identifiable=(not before.identifiable and after.identifiable),
        before_fingerprint=before.fingerprint,
        after_fingerprint=after.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
