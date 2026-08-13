"""Hyperparameter-free symmetric genetic-connectivity summary from exact EOG-R support.

The directional EOG-R support matrix is retained for migration-direction hypotheses.
For symmetric genetic differentiation such as pairwise FST, reciprocal eventual support
is combined in support space by arithmetic mean. This reflects total reciprocal exchange
support and remains finite when one direction is supported.

Pairs with zero support in both directions are not encoded by an arbitrary tiny floor.
They receive an explicit disconnection indicator, while their continuous distance is
capped at the largest finite connected-pair distance. The discontinuity is therefore a
separate estimand rather than a tunable numeric constant.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .dynamic_island_reachability import DynamicTransitionOperator
from .eventual_reachability_genetics import eventual_first_passage_support_matrix


@dataclass(frozen=True)
class EventualGeneticConnectivity:
    node_ids: tuple[str, ...]
    directional_support: np.ndarray
    symmetric_exchange_support: np.ndarray
    continuous_distance: np.ndarray
    disconnected: np.ndarray
    disconnected_distance_cap: float
    operator_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class EventualGeneticValidationBundle:
    node_ids: tuple[str, ...]
    geographic_distance: np.ndarray
    environmental_distance: np.ndarray
    eog_continuous_distance: np.ndarray
    eog_disconnected: np.ndarray
    directional_support: np.ndarray
    symmetric_exchange_support: np.ndarray
    method: str
    connectivity_fingerprint: str
    fingerprint: str


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def infer_eventual_genetic_connectivity(
    operator: DynamicTransitionOperator,
    sampled_node_ids: Sequence[str] | None = None,
) -> EventualGeneticConnectivity:
    """Return exact-eventual symmetric exchange distance plus disconnection status.

    Paths may use all nodes in the frozen operator even if only a subset of populations
    has genetic samples. No genetic response, horizon, support floor, or fitted
    symmetrisation parameter is accepted by this function.
    """

    ids, directional = eventual_first_passage_support_matrix(operator, sampled_node_ids)
    symmetric_support = 0.5 * (directional + directional.T)
    np.fill_diagonal(symmetric_support, 1.0)
    disconnected = symmetric_support <= 0.0
    np.fill_diagonal(disconnected, False)

    continuous = np.zeros_like(symmetric_support, dtype=float)
    positive = symmetric_support > 0.0
    continuous[positive] = -np.log(symmetric_support[positive])
    np.fill_diagonal(continuous, 0.0)

    off_diagonal = ~np.eye(len(ids), dtype=bool)
    finite_connected = off_diagonal & ~disconnected
    cap = float(np.max(continuous[finite_connected])) if np.any(finite_connected) else 0.0
    continuous[disconnected] = cap

    if not np.isfinite(continuous).all() or np.any(continuous < 0.0):
        raise RuntimeError("eventual genetic connectivity distance is invalid")
    if not np.allclose(continuous, continuous.T, rtol=0.0, atol=1e-12):
        raise RuntimeError("eventual genetic connectivity distance must be symmetric")

    payload = {
        "node_ids": list(ids),
        "directional_support": directional.tolist(),
        "symmetric_exchange_support": symmetric_support.tolist(),
        "continuous_distance": continuous.tolist(),
        "disconnected": disconnected.astype(int).tolist(),
        "disconnected_distance_cap": cap,
        "operator_fingerprint": operator.fingerprint,
        "method": (
            "exact eventual first-passage support; reciprocal arithmetic-mean support; "
            "explicit zero-exchange indicator; disconnected continuous distance capped "
            "at maximum finite connected-pair distance"
        ),
    }
    return EventualGeneticConnectivity(
        node_ids=ids,
        directional_support=directional,
        symmetric_exchange_support=symmetric_support,
        continuous_distance=continuous,
        disconnected=disconnected,
        disconnected_distance_cap=cap,
        operator_fingerprint=operator.fingerprint,
        fingerprint=_sha256(payload),
    )


def _validate_distance(values: np.ndarray, n: int, label: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.shape != (n, n) or not np.isfinite(matrix).all():
        raise ValueError(f"{label} must be a finite square matrix aligned to node_ids")
    if np.any(matrix < 0.0):
        raise ValueError(f"{label} must be non-negative")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError(f"{label} must be symmetric")
    if not np.allclose(np.diag(matrix), 0.0, rtol=0.0, atol=1e-12):
        raise ValueError(f"{label} diagonal must be zero")
    return matrix


def build_eventual_genetic_validation_bundle(
    geographic_distance: np.ndarray,
    environmental_distance: np.ndarray,
    connectivity: EventualGeneticConnectivity,
) -> EventualGeneticValidationBundle:
    """Freeze IBD/IBE/EOG predictors before attaching any genetic response."""

    ids = connectivity.node_ids
    n = len(ids)
    d_geo = _validate_distance(geographic_distance, n, "geographic_distance")
    d_env = _validate_distance(environmental_distance, n, "environmental_distance")
    d_eog = _validate_distance(
        connectivity.continuous_distance, n, "eog_continuous_distance"
    )
    disconnected = np.asarray(connectivity.disconnected, dtype=bool)
    if disconnected.shape != (n, n) or not np.array_equal(disconnected, disconnected.T):
        raise ValueError("eog_disconnected must be a symmetric matrix")
    if np.any(np.diag(disconnected)):
        raise ValueError("eog_disconnected diagonal must be false")

    method = (
        "exact eventual first-passage EOG-R; reciprocal arithmetic-mean exchange support; "
        "continuous -log support for connected pairs; explicit symmetric disconnection "
        "indicator; no propagation horizon or numerical support-floor parameter"
    )
    payload = {
        "node_ids": list(ids),
        "geographic_distance": d_geo.tolist(),
        "environmental_distance": d_env.tolist(),
        "eog_continuous_distance": d_eog.tolist(),
        "eog_disconnected": disconnected.astype(int).tolist(),
        "directional_support": connectivity.directional_support.tolist(),
        "symmetric_exchange_support": connectivity.symmetric_exchange_support.tolist(),
        "method": method,
        "connectivity_fingerprint": connectivity.fingerprint,
    }
    return EventualGeneticValidationBundle(
        node_ids=ids,
        geographic_distance=d_geo.copy(),
        environmental_distance=d_env.copy(),
        eog_continuous_distance=d_eog.copy(),
        eog_disconnected=disconnected.copy(),
        directional_support=connectivity.directional_support.copy(),
        symmetric_exchange_support=connectivity.symmetric_exchange_support.copy(),
        method=method,
        connectivity_fingerprint=connectivity.fingerprint,
        fingerprint=_sha256(payload),
    )
