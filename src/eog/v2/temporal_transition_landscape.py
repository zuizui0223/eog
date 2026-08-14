"""Finite-world transition-landscape summaries for the active EOG mainline.

This module summarizes the *declared transition networks* that underlie temporal
reachability. It does not infer occupancy, movement history, or calibrated event
probabilities. For every declared transition interval it classifies directed edges as
active in all worlds, active in only some worlds, or inactive in every world, then
reports opening/closure events between adjacent intervals.

The distinction is intentionally structural:

- robust edge: positive raw transition support in every declared temporal world;
- contingent edge: positive support in at least one but not all worlds;
- inactive edge: zero support in every declared world.

All claims are restricted to the exhaustively supplied finite temporal world set.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .temporal_reachability import TemporalWorld


Edge = tuple[str, str]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_worlds(worlds: Sequence[TemporalWorld]) -> tuple[TemporalWorld, ...]:
    declared = tuple(worlds)
    if not declared:
        raise ValueError("at least one temporal world is required")
    ids = [world.world_id for world in declared]
    if len(set(ids)) != len(ids):
        raise ValueError("temporal world IDs must be unique")
    ordered = tuple(sorted(declared, key=lambda world: world.world_id))
    first = ordered[0]
    if any(world.node_ids != first.node_ids for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same node IDs and order")
    if any(world.time_labels != first.time_labels for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same ordered time labels")
    if any(world.source_ids != first.source_ids for world in ordered[1:]):
        raise ValueError("all temporal worlds must share the same source IDs")
    return ordered


def _edge_tuple(node_ids: tuple[str, ...], source: int, target: int) -> Edge:
    return (node_ids[source], node_ids[target])


@dataclass(frozen=True)
class TemporalTransitionLandscape:
    """Finite-world envelope of time-varying directed transition structure."""

    node_ids: tuple[str, ...]
    time_labels: tuple[str, ...]
    world_ids: tuple[str, ...]
    robust_edges_by_interval: tuple[tuple[Edge, ...], ...]
    contingent_edges_by_interval: tuple[tuple[Edge, ...], ...]
    inactive_edges_by_interval: tuple[tuple[Edge, ...], ...]
    possible_openings_by_interval: tuple[tuple[Edge, ...], ...]
    possible_closures_by_interval: tuple[tuple[Edge, ...], ...]
    robust_openings_by_interval: tuple[tuple[Edge, ...], ...]
    robust_closures_by_interval: tuple[tuple[Edge, ...], ...]
    support_lower_by_interval: tuple[np.ndarray, ...]
    support_upper_by_interval: tuple[np.ndarray, ...]
    support_tolerance: float
    coverage_certificate: str
    world_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


@dataclass(frozen=True)
class TemporalTransitionUniverseUpdate:
    """Monotone change after expanding an exhaustively declared temporal world set."""

    before_world_ids: tuple[str, ...]
    after_world_ids: tuple[str, ...]
    added_world_ids: tuple[str, ...]
    lost_robust_edges_by_interval: tuple[tuple[Edge, ...], ...]
    gained_possible_edges_by_interval: tuple[tuple[Edge, ...], ...]
    lost_inactive_edges_by_interval: tuple[tuple[Edge, ...], ...]
    robust_monotonicity_holds: bool
    possible_monotonicity_holds: bool
    exclusion_monotonicity_holds: bool
    before_fingerprint: str
    after_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def summarize_temporal_transition_landscape(
    worlds: Sequence[TemporalWorld],
    *,
    support_tolerance: float = 1e-15,
) -> TemporalTransitionLandscape:
    """Summarize robust/contingent transition edges and their opening/closure events.

    ``possible_*`` events track whether an edge is active in at least one world.
    ``robust_*`` events track whether it is active in every declared world. The first
    interval has no predecessor, so all four event collections are empty there.

    The support envelopes use each operator's *raw* transition support. Positive but
    very small support remains possible unless it is at or below ``support_tolerance``;
    this function therefore does not convert low support into impossibility.
    """

    tolerance = float(support_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")

    ordered = _validate_worlds(worlds)
    node_ids = ordered[0].node_ids
    time_labels = ordered[0].time_labels
    n_intervals = len(time_labels) - 1
    n_nodes = len(node_ids)

    robust_by_interval: list[tuple[Edge, ...]] = []
    contingent_by_interval: list[tuple[Edge, ...]] = []
    inactive_by_interval: list[tuple[Edge, ...]] = []
    lower_by_interval: list[np.ndarray] = []
    upper_by_interval: list[np.ndarray] = []

    possible_masks: list[np.ndarray] = []
    robust_masks: list[np.ndarray] = []

    for interval in range(n_intervals):
        stack = np.stack(
            [np.asarray(world.operators[interval].raw_support, dtype=float) for world in ordered],
            axis=0,
        )
        lower = np.min(stack, axis=0)
        upper = np.max(stack, axis=0)
        robust_mask = np.all(stack > tolerance, axis=0)
        possible_mask = np.any(stack > tolerance, axis=0)
        contingent_mask = possible_mask & ~robust_mask
        inactive_mask = ~possible_mask

        # Self transitions are not ecological edges in the current operator contract.
        diagonal = np.eye(n_nodes, dtype=bool)
        robust_mask = robust_mask & ~diagonal
        possible_mask = possible_mask & ~diagonal
        contingent_mask = contingent_mask & ~diagonal
        inactive_mask = inactive_mask & ~diagonal

        def edges_from(mask: np.ndarray) -> tuple[Edge, ...]:
            rows, cols = np.nonzero(mask)
            return tuple(
                sorted(_edge_tuple(node_ids, int(i), int(j)) for i, j in zip(rows, cols, strict=True))
            )

        robust_by_interval.append(edges_from(robust_mask))
        contingent_by_interval.append(edges_from(contingent_mask))
        inactive_by_interval.append(edges_from(inactive_mask))
        lower_by_interval.append(lower)
        upper_by_interval.append(upper)
        possible_masks.append(possible_mask)
        robust_masks.append(robust_mask)

    possible_openings: list[tuple[Edge, ...]] = [()]
    possible_closures: list[tuple[Edge, ...]] = [()]
    robust_openings: list[tuple[Edge, ...]] = [()]
    robust_closures: list[tuple[Edge, ...]] = [()]

    def event_edges(mask: np.ndarray) -> tuple[Edge, ...]:
        rows, cols = np.nonzero(mask)
        return tuple(
            sorted(_edge_tuple(node_ids, int(i), int(j)) for i, j in zip(rows, cols, strict=True))
        )

    for interval in range(1, n_intervals):
        previous_possible = possible_masks[interval - 1]
        current_possible = possible_masks[interval]
        previous_robust = robust_masks[interval - 1]
        current_robust = robust_masks[interval]

        possible_openings.append(event_edges(current_possible & ~previous_possible))
        possible_closures.append(event_edges(previous_possible & ~current_possible))
        robust_openings.append(event_edges(current_robust & ~previous_robust))
        robust_closures.append(event_edges(previous_robust & ~current_robust))

    certificate = "exhaustive_declared_temporal_transition_world_set"
    payload = {
        "world_fingerprints": [(world.world_id, world.fingerprint) for world in ordered],
        "robust_edges_by_interval": [[list(edge) for edge in values] for values in robust_by_interval],
        "contingent_edges_by_interval": [
            [list(edge) for edge in values] for values in contingent_by_interval
        ],
        "inactive_edges_by_interval": [[list(edge) for edge in values] for values in inactive_by_interval],
        "possible_openings_by_interval": [
            [list(edge) for edge in values] for values in possible_openings
        ],
        "possible_closures_by_interval": [
            [list(edge) for edge in values] for values in possible_closures
        ],
        "robust_openings_by_interval": [[list(edge) for edge in values] for values in robust_openings],
        "robust_closures_by_interval": [[list(edge) for edge in values] for values in robust_closures],
        "support_tolerance": tolerance,
        "coverage_certificate": certificate,
    }

    return TemporalTransitionLandscape(
        node_ids=node_ids,
        time_labels=time_labels,
        world_ids=tuple(world.world_id for world in ordered),
        robust_edges_by_interval=tuple(robust_by_interval),
        contingent_edges_by_interval=tuple(contingent_by_interval),
        inactive_edges_by_interval=tuple(inactive_by_interval),
        possible_openings_by_interval=tuple(possible_openings),
        possible_closures_by_interval=tuple(possible_closures),
        robust_openings_by_interval=tuple(robust_openings),
        robust_closures_by_interval=tuple(robust_closures),
        support_lower_by_interval=tuple(lower_by_interval),
        support_upper_by_interval=tuple(upper_by_interval),
        support_tolerance=tolerance,
        coverage_certificate=certificate,
        world_fingerprints=tuple((world.world_id, world.fingerprint) for world in ordered),
        fingerprint=_canonical_sha256(payload),
    )


def compare_temporal_transition_universes(
    before: TemporalTransitionLandscape,
    after: TemporalTransitionLandscape,
) -> TemporalTransitionUniverseUpdate:
    """Compare nested finite world universes under the complexity-monotonicity rule.

    The ``before`` world set must be an exact fingerprint-preserving subset of
    ``after``. Under world-set expansion:

    - robust edges may only be lost, never gained;
    - possible edges may only be gained, never lost;
    - inactive-in-all-worlds edges may only be lost, never gained.

    These are finite-set logical consequences, not empirical performance claims.
    """

    if before.node_ids != after.node_ids or before.time_labels != after.time_labels:
        raise ValueError("transition landscapes must share node IDs and time labels")
    if before.support_tolerance != after.support_tolerance:
        raise ValueError("transition landscapes must share support_tolerance")

    before_worlds = dict(before.world_fingerprints)
    after_worlds = dict(after.world_fingerprints)
    if not set(before_worlds).issubset(after_worlds):
        raise ValueError("before world universe must be a subset of after world universe")
    for world_id, fingerprint in before_worlds.items():
        if after_worlds[world_id] != fingerprint:
            raise ValueError("shared world IDs must preserve identical fingerprints")

    lost_robust: list[tuple[Edge, ...]] = []
    gained_possible: list[tuple[Edge, ...]] = []
    lost_inactive: list[tuple[Edge, ...]] = []
    robust_ok = True
    possible_ok = True
    exclusion_ok = True

    for interval in range(len(before.robust_edges_by_interval)):
        before_robust = set(before.robust_edges_by_interval[interval])
        after_robust = set(after.robust_edges_by_interval[interval])
        before_possible = before_robust | set(before.contingent_edges_by_interval[interval])
        after_possible = after_robust | set(after.contingent_edges_by_interval[interval])
        before_inactive = set(before.inactive_edges_by_interval[interval])
        after_inactive = set(after.inactive_edges_by_interval[interval])

        robust_ok = robust_ok and after_robust.issubset(before_robust)
        possible_ok = possible_ok and before_possible.issubset(after_possible)
        exclusion_ok = exclusion_ok and after_inactive.issubset(before_inactive)

        lost_robust.append(tuple(sorted(before_robust - after_robust)))
        gained_possible.append(tuple(sorted(after_possible - before_possible)))
        lost_inactive.append(tuple(sorted(before_inactive - after_inactive)))

    if not (robust_ok and possible_ok and exclusion_ok):
        raise RuntimeError("world-universe expansion violated transition monotonicity")

    added_world_ids = tuple(sorted(set(after_worlds) - set(before_worlds)))
    certificate = "exact_nested_temporal_transition_world_universes"
    payload = {
        "before_fingerprint": before.fingerprint,
        "after_fingerprint": after.fingerprint,
        "added_world_ids": list(added_world_ids),
        "lost_robust_edges_by_interval": [
            [list(edge) for edge in values] for values in lost_robust
        ],
        "gained_possible_edges_by_interval": [
            [list(edge) for edge in values] for values in gained_possible
        ],
        "lost_inactive_edges_by_interval": [
            [list(edge) for edge in values] for values in lost_inactive
        ],
        "coverage_certificate": certificate,
    }

    return TemporalTransitionUniverseUpdate(
        before_world_ids=before.world_ids,
        after_world_ids=after.world_ids,
        added_world_ids=added_world_ids,
        lost_robust_edges_by_interval=tuple(lost_robust),
        gained_possible_edges_by_interval=tuple(gained_possible),
        lost_inactive_edges_by_interval=tuple(lost_inactive),
        robust_monotonicity_holds=robust_ok,
        possible_monotonicity_holds=possible_ok,
        exclusion_monotonicity_holds=exclusion_ok,
        before_fingerprint=before.fingerprint,
        after_fingerprint=after.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )
