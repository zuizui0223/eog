"""Dynamic source-conditioned reachability on directed island or habitat graphs.

The quantities in this module are assumption-conditioned support diagnostics. They are
not calibrated movement, colonisation, occupancy, migration, or demographic
probabilities unless an external calibration justifies that interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class DynamicReachabilityEdge:
    """One directed transition with explicitly separated support components.

    Every component is constrained to ``[0, 1]`` and the raw transition support is
    their product. ``target_capture_support`` can encode a predeclared target-size or
    interception effect. Establishment/persistence belongs to a separate node-level
    layer and is deliberately not folded into this edge.
    """

    source: int
    target: int
    geographic_support: float
    environmental_support: float = 1.0
    barrier_support: float = 1.0
    directional_support: float = 1.0
    target_capture_support: float = 1.0

    def __post_init__(self) -> None:
        if self.source < 0 or self.target < 0 or self.source == self.target:
            raise ValueError("edge endpoints must be distinct non-negative indices")
        values = (
            self.geographic_support,
            self.environmental_support,
            self.barrier_support,
            self.directional_support,
            self.target_capture_support,
        )
        if not all(np.isfinite(values)) or any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError("all edge support components must be finite and lie in [0, 1]")

    @property
    def raw_support(self) -> float:
        return float(
            self.geographic_support
            * self.environmental_support
            * self.barrier_support
            * self.directional_support
            * self.target_capture_support
        )


@dataclass(frozen=True)
class DynamicTransitionOperator:
    """Auditable sub-stochastic operator and its explicit failure channel."""

    node_ids: tuple[str, ...]
    raw_support: np.ndarray
    transition: np.ndarray
    loss_support: np.ndarray
    fingerprint: str


@dataclass(frozen=True)
class DynamicReachabilityResult:
    """Finite-horizon propagation summaries.

    ``mass_by_step[t, j]`` is relative reachability support at node ``j`` after
    exactly ``t`` propagation steps. ``integrated_edge_flux`` sums directed support
    flux across all propagation steps before the final horizon. ``source_attribution``
    is based on finite-horizon integrated node support and therefore describes the
    declared propagation process, not historical ancestry.
    """

    node_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_weights: np.ndarray
    mass_by_step: np.ndarray
    total_mass_by_step: np.ndarray
    lost_mass_by_step: np.ndarray
    integrated_node_support: np.ndarray
    integrated_edge_flux: np.ndarray
    first_arrival_step: np.ndarray
    source_attribution: np.ndarray
    operator_fingerprint: str


@dataclass(frozen=True)
class FirstPassageSummary:
    """Relative first-passage support to one declared target within a finite horizon."""

    target_id: str
    source_ids: tuple[str, ...]
    step_support: np.ndarray
    cumulative_support: np.ndarray
    horizon_support: float
    first_positive_step: int | None
    conditional_mean_step: float | None
    source_attribution: np.ndarray
    operator_fingerprint: str


def _as_loss_support(values: float | Sequence[float], n_nodes: int) -> np.ndarray:
    if np.isscalar(values):
        result = np.full(n_nodes, float(values), dtype=float)
    else:
        result = np.asarray(values, dtype=float)
        if result.shape != (n_nodes,):
            raise ValueError("loss_support must be a scalar or one value per node")
    if not np.isfinite(result).all() or np.any(result <= 0.0):
        raise ValueError("loss_support values must be finite and strictly positive")
    return result


def _fingerprint_payload(
    node_ids: tuple[str, ...],
    raw_support: np.ndarray,
    transition: np.ndarray,
    loss_support: np.ndarray,
) -> str:
    payload = {
        "node_ids": list(node_ids),
        "raw_support": raw_support.tolist(),
        "transition": transition.tolist(),
        "loss_support": loss_support.tolist(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_dynamic_transition_operator(
    node_ids: Sequence[str],
    edges: Sequence[DynamicReachabilityEdge],
    *,
    loss_support: float | Sequence[float] = 1.0,
) -> DynamicTransitionOperator:
    """Build a directed sub-stochastic transition operator.

    Edge-component products are treated as raw transition support. For node ``i``,
    the operator uses an explicit competing failure channel ``loss_support[i]``::

        Q[i, j] = W[i, j] / (loss_support[i] + sum_k W[i, k])

    Hence every row sum is strictly below one whenever ``loss_support`` is positive.
    Weak or sparse outgoing support therefore loses more propagation mass rather than
    being renormalised into guaranteed eventual arrival.
    """

    ids = tuple(str(value) for value in node_ids)
    if len(ids) < 2 or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("node_ids must contain at least two unique non-empty IDs")
    n_nodes = len(ids)
    loss = _as_loss_support(loss_support, n_nodes)
    raw = np.zeros((n_nodes, n_nodes), dtype=float)
    seen: set[tuple[int, int]] = set()
    for edge in edges:
        if edge.source >= n_nodes or edge.target >= n_nodes:
            raise ValueError("edge endpoint exceeds node count")
        key = (edge.source, edge.target)
        if key in seen:
            raise ValueError("duplicate directed reachability edge")
        seen.add(key)
        raw[key] = edge.raw_support

    row_support = np.sum(raw, axis=1)
    transition = raw / (loss + row_support)[:, None]
    row_sums = np.sum(transition, axis=1)
    if np.any(row_sums >= 1.0):
        raise RuntimeError("dynamic reachability operator must remain sub-stochastic")

    return DynamicTransitionOperator(
        node_ids=ids,
        raw_support=raw,
        transition=transition,
        loss_support=loss,
        fingerprint=_fingerprint_payload(ids, raw, transition, loss),
    )


def _resolve_sources(
    operator: DynamicTransitionOperator,
    source_weights: Mapping[str, float] | Sequence[str],
) -> tuple[np.ndarray, tuple[str, ...], np.ndarray]:
    index = {node_id: i for i, node_id in enumerate(operator.node_ids)}
    if isinstance(source_weights, Mapping):
        items = [(str(key), float(value)) for key, value in source_weights.items()]
    else:
        items = [(str(key), 1.0) for key in source_weights]
    if not items:
        raise ValueError("at least one source is required")
    if len({key for key, _ in items}) != len(items):
        raise ValueError("source IDs must be unique")
    if any(key not in index for key, _ in items):
        raise ValueError("all source IDs must occur in node_ids")
    weights = np.asarray([value for _, value in items], dtype=float)
    if not np.isfinite(weights).all() or np.any(weights < 0.0) or float(np.sum(weights)) <= 0.0:
        raise ValueError("source weights must be finite, non-negative, and sum to > 0")
    weights = weights / np.sum(weights)
    source_indices = np.asarray([index[key] for key, _ in items], dtype=int)
    source_ids = tuple(key for key, _ in items)
    return source_indices, source_ids, weights


def propagate_dynamic_reachability(
    operator: DynamicTransitionOperator,
    source_weights: Mapping[str, float] | Sequence[str],
    *,
    max_steps: int,
    arrival_tolerance: float = 1e-15,
) -> DynamicReachabilityResult:
    """Propagate relative reachability support from declared sources.

    ``max_steps`` is a propagation depth, not a time unit, unless separately
    calibrated. No source mass is reinjected after step zero.
    """

    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(arrival_tolerance) or arrival_tolerance < 0.0:
        raise ValueError("arrival_tolerance must be finite and non-negative")

    source_indices, source_ids, weights = _resolve_sources(operator, source_weights)
    n_sources = len(source_ids)
    n_nodes = len(operator.node_ids)
    q = operator.transition

    by_source = np.zeros((n_sources, n_nodes), dtype=float)
    by_source[np.arange(n_sources), source_indices] = weights
    mass_by_step = np.zeros((max_steps + 1, n_nodes), dtype=float)
    total_mass_by_step = np.zeros(max_steps + 1, dtype=float)
    lost_mass_by_step = np.zeros(max_steps, dtype=float)
    integrated_by_source = np.zeros((n_sources, n_nodes), dtype=float)
    integrated_edge_flux = np.zeros((n_nodes, n_nodes), dtype=float)

    for step in range(max_steps + 1):
        total = np.sum(by_source, axis=0)
        mass_by_step[step] = total
        total_mass_by_step[step] = float(np.sum(total))
        integrated_by_source += by_source
        if step == max_steps:
            break
        integrated_edge_flux += total[:, None] * q
        next_by_source = by_source @ q
        lost_mass_by_step[step] = float(np.sum(by_source) - np.sum(next_by_source))
        by_source = next_by_source

    first_arrival = np.full(n_nodes, -1, dtype=int)
    for node in range(n_nodes):
        hits = np.flatnonzero(mass_by_step[:, node] > arrival_tolerance)
        if hits.size:
            first_arrival[node] = int(hits[0])

    integrated_node_support = np.sum(mass_by_step, axis=0)
    source_attribution = np.zeros((n_sources, n_nodes), dtype=float)
    denominators = np.sum(integrated_by_source, axis=0)
    supported = denominators > 0.0
    source_attribution[:, supported] = integrated_by_source[:, supported] / denominators[supported]

    if np.any(np.diff(total_mass_by_step) > 1e-12):
        raise RuntimeError("total propagation mass increased under a sub-stochastic operator")

    return DynamicReachabilityResult(
        node_ids=operator.node_ids,
        source_ids=source_ids,
        source_weights=weights,
        mass_by_step=mass_by_step,
        total_mass_by_step=total_mass_by_step,
        lost_mass_by_step=lost_mass_by_step,
        integrated_node_support=integrated_node_support,
        integrated_edge_flux=integrated_edge_flux,
        first_arrival_step=first_arrival,
        source_attribution=source_attribution,
        operator_fingerprint=operator.fingerprint,
    )


def summarize_first_passage(
    operator: DynamicTransitionOperator,
    source_weights: Mapping[str, float] | Sequence[str],
    target_id: str,
    *,
    max_steps: int,
    support_tolerance: float = 1e-15,
) -> FirstPassageSummary:
    """Summarise first-passage support to a single target.

    Mass is absorbed when it first reaches the target, so repeated visits do not
    inflate ``horizon_support``. Under the sub-stochastic operator the result lies in
    ``[0, 1]`` when the initial source mass sums to one. It remains a model support
    quantity unless the transition operator has been externally calibrated.
    """

    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(support_tolerance) or support_tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")
    try:
        target = operator.node_ids.index(str(target_id))
    except ValueError as exc:
        raise ValueError("target_id must occur in node_ids") from exc

    source_indices, source_ids, weights = _resolve_sources(operator, source_weights)
    n_sources = len(source_ids)
    n_nodes = len(operator.node_ids)
    q = operator.transition
    active = np.zeros((n_sources, n_nodes), dtype=float)
    active[np.arange(n_sources), source_indices] = weights
    hits = np.zeros((n_sources, max_steps + 1), dtype=float)

    initially_at_target = source_indices == target
    hits[initially_at_target, 0] = weights[initially_at_target]
    active[:, target] = 0.0

    for step in range(1, max_steps + 1):
        hits[:, step] = active @ q[:, target]
        active = active @ q
        active[:, target] = 0.0

    step_support = np.sum(hits, axis=0)
    cumulative = np.cumsum(step_support)
    horizon = float(cumulative[-1])
    if horizon > 1.0 + 1e-12:
        raise RuntimeError("first-passage support exceeded initial source mass")
    positive = np.flatnonzero(step_support > support_tolerance)
    first_positive = None if positive.size == 0 else int(positive[0])
    if horizon > support_tolerance:
        mean_step = float(np.dot(np.arange(max_steps + 1, dtype=float), step_support) / horizon)
        per_source = np.sum(hits, axis=1)
        attribution = per_source / np.sum(per_source)
    else:
        mean_step = None
        attribution = np.zeros(n_sources, dtype=float)

    return FirstPassageSummary(
        target_id=operator.node_ids[target],
        source_ids=source_ids,
        step_support=step_support,
        cumulative_support=cumulative,
        horizon_support=horizon,
        first_positive_step=first_positive,
        conditional_mean_step=mean_step,
        source_attribution=attribution,
        operator_fingerprint=operator.fingerprint,
    )
