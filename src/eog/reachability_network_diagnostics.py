"""Graph-native flow and bridge diagnostics for dynamic island reachability.

These summaries describe the declared EOG-R propagation operator. They do not prove
historical routes or demographic connectivity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .dynamic_island_reachability import (
    DynamicReachabilityResult,
    DynamicTransitionOperator,
    summarize_first_passage,
)


@dataclass(frozen=True)
class NetworkFluxDiagnostics:
    node_ids: tuple[str, ...]
    integrated_edge_flux: np.ndarray
    edge_flux_fraction: np.ndarray
    incoming_flux: np.ndarray
    outgoing_flux: np.ndarray
    active_outdegree: np.ndarray
    outgoing_flux_entropy: np.ndarray
    operator_fingerprint: str


@dataclass(frozen=True)
class BridgeNodeImportanceResult:
    node_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    target_id: str
    baseline_first_passage_support: float
    blocked_first_passage_support: np.ndarray
    relative_support_loss: np.ndarray
    max_steps: int
    operator_fingerprint: str


def summarize_network_flux(
    result: DynamicReachabilityResult,
    *,
    flux_tolerance: float = 1e-15,
) -> NetworkFluxDiagnostics:
    """Summarise finite-horizon edge flow and normalized outgoing flux entropy.

    Entropy is zero for nodes with fewer than two active outgoing edges. Otherwise it
    is normalized by ``log(active_outdegree)`` and lies in ``[0, 1]``. It is a
    flow-diversification diagnostic, not a count of historical dispersal routes.
    """

    if not np.isfinite(flux_tolerance) or flux_tolerance < 0.0:
        raise ValueError("flux_tolerance must be finite and non-negative")
    flux = np.asarray(result.integrated_edge_flux, dtype=float)
    n = len(result.node_ids)
    if flux.shape != (n, n) or not np.isfinite(flux).all() or np.any(flux < 0.0):
        raise ValueError("integrated edge flux must be a finite non-negative square matrix")

    total = float(np.sum(flux))
    fractions = np.zeros_like(flux) if total <= 0.0 else flux / total
    outgoing = np.sum(flux, axis=1)
    incoming = np.sum(flux, axis=0)
    active_outdegree = np.sum(flux > flux_tolerance, axis=1).astype(int)
    entropy = np.zeros(n, dtype=float)
    for node in range(n):
        active = flux[node] > flux_tolerance
        degree = int(np.sum(active))
        if degree < 2 or outgoing[node] <= 0.0:
            continue
        probabilities = flux[node, active] / outgoing[node]
        raw = float(-np.sum(probabilities * np.log(probabilities)))
        entropy[node] = raw / float(np.log(degree))

    return NetworkFluxDiagnostics(
        node_ids=result.node_ids,
        integrated_edge_flux=flux.copy(),
        edge_flux_fraction=fractions,
        incoming_flux=incoming,
        outgoing_flux=outgoing,
        active_outdegree=active_outdegree,
        outgoing_flux_entropy=entropy,
        operator_fingerprint=result.operator_fingerprint,
    )


def _resolve_initial_mass(
    operator: DynamicTransitionOperator,
    source_weights: Mapping[str, float] | Sequence[str],
) -> tuple[np.ndarray, tuple[str, ...]]:
    index = {node_id: i for i, node_id in enumerate(operator.node_ids)}
    if isinstance(source_weights, Mapping):
        items = [(str(key), float(value)) for key, value in source_weights.items()]
    else:
        items = [(str(key), 1.0) for key in source_weights]
    if not items or len({key for key, _ in items}) != len(items):
        raise ValueError("source IDs must be non-empty and unique")
    if any(key not in index for key, _ in items):
        raise ValueError("all source IDs must occur in node_ids")
    weights = np.asarray([value for _, value in items], dtype=float)
    if not np.isfinite(weights).all() or np.any(weights < 0.0) or float(np.sum(weights)) <= 0.0:
        raise ValueError("source weights must be finite, non-negative, and sum to > 0")
    weights = weights / np.sum(weights)
    mass = np.zeros(len(operator.node_ids), dtype=float)
    for (node_id, _), weight in zip(items, weights):
        mass[index[node_id]] = weight
    return mass, tuple(node_id for node_id, _ in items)


def _first_passage_support_with_transition(
    transition: np.ndarray,
    initial_mass: np.ndarray,
    target: int,
    max_steps: int,
) -> float:
    active = np.asarray(initial_mass, dtype=float).copy()
    hit = float(active[target])
    active[target] = 0.0
    for _ in range(max_steps):
        hit += float(active @ transition[:, target])
        active = active @ transition
        active[target] = 0.0
    return float(hit)


def evaluate_bridge_node_importance(
    operator: DynamicTransitionOperator,
    source_weights: Mapping[str, float] | Sequence[str],
    target_id: str,
    *,
    max_steps: int,
    support_tolerance: float = 1e-15,
) -> BridgeNodeImportanceResult:
    """Measure target first-passage loss when each intermediate node is unavailable.

    Node removal is evaluated on the **frozen transition operator** by zeroing all
    transitions into and out of the blocked node without renormalizing remaining
    edges. Propagation mass that would have used the blocked node is therefore lost.
    This preserves the declared absolute transition support and avoids making alternate
    routes artificially stronger after a node is removed.
    """

    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(support_tolerance) or support_tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")
    if str(target_id) not in operator.node_ids:
        raise ValueError("target_id must occur in node_ids")

    target = operator.node_ids.index(str(target_id))
    initial_mass, source_ids = _resolve_initial_mass(operator, source_weights)
    baseline = summarize_first_passage(
        operator,
        source_weights,
        target_id,
        max_steps=max_steps,
        support_tolerance=support_tolerance,
    ).horizon_support

    n = len(operator.node_ids)
    blocked_support = np.full(n, np.nan, dtype=float)
    relative_loss = np.full(n, np.nan, dtype=float)
    source_indices = {operator.node_ids.index(source_id) for source_id in source_ids}
    for node in range(n):
        if node == target or node in source_indices:
            continue
        blocked = operator.transition.copy()
        blocked[node, :] = 0.0
        blocked[:, node] = 0.0
        support = _first_passage_support_with_transition(
            blocked,
            initial_mass,
            target,
            int(max_steps),
        )
        blocked_support[node] = support
        if baseline > support_tolerance:
            relative_loss[node] = float(np.clip((baseline - support) / baseline, 0.0, 1.0))
        else:
            relative_loss[node] = 0.0

    return BridgeNodeImportanceResult(
        node_ids=operator.node_ids,
        source_ids=source_ids,
        target_id=operator.node_ids[target],
        baseline_first_passage_support=float(baseline),
        blocked_first_passage_support=blocked_support,
        relative_support_loss=relative_loss,
        max_steps=int(max_steps),
        operator_fingerprint=operator.fingerprint,
    )
