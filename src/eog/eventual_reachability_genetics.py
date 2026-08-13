"""Exact eventual first-passage distances for prospective EOG-R genetic validation.

Finite propagation depth remains the appropriate object for colonisation-wave and
survey questions. Neutral genetic structure integrates connectivity over a much longer
and usually unknown time horizon, so this module removes the arbitrary finite-step
choice by summing all first-passage paths exactly under the frozen sub-stochastic
operator.

The resulting quantities remain assumption-conditioned support diagnostics. They are
not migration probabilities or demographic parameters without external calibration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .dynamic_island_reachability import DynamicTransitionOperator
from .reachability_genetics import GeneticValidationDistanceBundle


@dataclass(frozen=True)
class EventualReachabilityDistanceResult:
    node_ids: tuple[str, ...]
    directional_support: np.ndarray
    directional_distance: np.ndarray
    symmetric_distance: np.ndarray
    zero_support: np.ndarray
    support_floor: float
    symmetrization: str
    operator_fingerprint: str
    fingerprint: str


def _matrix_payload(matrix: np.ndarray) -> list[list[float]]:
    return np.asarray(matrix, dtype=float).tolist()


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _eventual_support_to_target(
    operator: DynamicTransitionOperator,
    target: int,
) -> np.ndarray:
    """Solve total first-passage support to one target from every source node."""

    q = np.asarray(operator.transition, dtype=float)
    n = q.shape[0]
    if target < 0 or target >= n:
        raise ValueError("target index outside operator")
    keep = np.asarray([index for index in range(n) if index != target], dtype=int)
    result = np.zeros(n, dtype=float)
    result[target] = 1.0
    if keep.size == 0:
        return result

    sub = q[np.ix_(keep, keep)]
    direct = q[keep, target]
    system = np.eye(len(keep), dtype=float) - sub
    try:
        solved = np.linalg.solve(system, direct)
    except np.linalg.LinAlgError as exc:
        raise RuntimeError("eventual first-passage linear system is singular") from exc
    if not np.isfinite(solved).all():
        raise RuntimeError("eventual first-passage solution is non-finite")
    if np.any(solved < -1e-12) or np.any(solved > 1.0 + 1e-10):
        raise RuntimeError("eventual first-passage support lies outside [0, 1]")
    result[keep] = np.clip(solved, 0.0, 1.0)
    return result


def eventual_first_passage_support_matrix(
    operator: DynamicTransitionOperator,
    sampled_node_ids: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], np.ndarray]:
    """Return exact all-path first-passage support among sampled nodes.

    Paths may pass through unsampled nodes in the frozen operator. Sampling therefore
    restricts only the reported source/target pairs and does not silently delete
    intermediate islands.
    """

    ids = (
        operator.node_ids
        if sampled_node_ids is None
        else tuple(str(value) for value in sampled_node_ids)
    )
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("sampled_node_ids must contain at least two unique IDs")
    lookup = {node_id: index for index, node_id in enumerate(operator.node_ids)}
    if any(node_id not in lookup for node_id in ids):
        raise ValueError("all sampled_node_ids must occur in the operator")
    indices = np.asarray([lookup[node_id] for node_id in ids], dtype=int)

    full = np.zeros((len(operator.node_ids), len(operator.node_ids)), dtype=float)
    for target in range(len(operator.node_ids)):
        full[:, target] = _eventual_support_to_target(operator, target)
    support = full[np.ix_(indices, indices)]
    np.fill_diagonal(support, 1.0)
    return ids, support


def pairwise_eventual_reachability_distances(
    operator: DynamicTransitionOperator,
    sampled_node_ids: Sequence[str] | None = None,
    *,
    support_floor: float = 1e-12,
    symmetrization: str,
) -> EventualReachabilityDistanceResult:
    """Derive directional and symmetric horizon-free EOG-R isolation distances.

    Directional distance is ``-log(eventual first-passage support)``. Exact zero-support
    pairs are retained in ``zero_support`` and capped numerically at the explicitly
    declared ``support_floor`` for downstream finite-valued models.

    Symmetrisation remains explicit:

    - ``mean_log``: negative log of the geometric mean of reciprocal supports;
    - ``max_log``: retain the more isolated reciprocal direction;
    - ``mean_support``: negative log of the arithmetic mean of reciprocal supports.

    ``mean_support`` is included specifically because one-way connectivity can still
    exchange genes; unlike log-space rules it remains finite when exactly one direction
    has positive support.
    """

    if not np.isfinite(support_floor) or not (0.0 < support_floor < 1.0):
        raise ValueError("support_floor must lie strictly between 0 and 1")
    allowed = {"mean_log", "max_log", "mean_support"}
    if symmetrization not in allowed:
        raise ValueError(
            "symmetrization must be 'mean_log', 'max_log', or 'mean_support'"
        )

    ids, support = eventual_first_passage_support_matrix(operator, sampled_node_ids)
    zero_support = support <= 0.0
    np.fill_diagonal(zero_support, False)
    directional = -np.log(np.maximum(support, support_floor))
    np.fill_diagonal(directional, 0.0)
    if symmetrization == "mean_log":
        symmetric = 0.5 * (directional + directional.T)
    elif symmetrization == "max_log":
        symmetric = np.maximum(directional, directional.T)
    else:
        mean_support = 0.5 * (support + support.T)
        symmetric = -np.log(np.maximum(mean_support, support_floor))
    np.fill_diagonal(symmetric, 0.0)

    payload = {
        "node_ids": list(ids),
        "directional_support": _matrix_payload(support),
        "directional_distance": _matrix_payload(directional),
        "symmetric_distance": _matrix_payload(symmetric),
        "zero_support": zero_support.astype(int).tolist(),
        "support_floor": float(support_floor),
        "symmetrization": symmetrization,
        "horizon_policy": "exact_eventual_first_passage_under_frozen_substochastic_operator",
        "operator_fingerprint": operator.fingerprint,
    }
    return EventualReachabilityDistanceResult(
        node_ids=ids,
        directional_support=support,
        directional_distance=directional,
        symmetric_distance=symmetric,
        zero_support=zero_support,
        support_floor=float(support_floor),
        symmetrization=symmetrization,
        operator_fingerprint=operator.fingerprint,
        fingerprint=_sha256(payload),
    )


def _validate_symmetric_distance(values: np.ndarray, n: int, label: str) -> np.ndarray:
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


def build_eventual_genetic_validation_distance_bundle(
    geographic_distance: np.ndarray,
    environmental_distance: np.ndarray,
    reachability: EventualReachabilityDistanceResult,
) -> GeneticValidationDistanceBundle:
    """Freeze IBD, IBE and exact-eventual EOG-R distances without genetic outcomes."""

    ids = reachability.node_ids
    n = len(ids)
    d_geo = _validate_symmetric_distance(geographic_distance, n, "geographic_distance")
    d_env = _validate_symmetric_distance(environmental_distance, n, "environmental_distance")
    d_eog = _validate_symmetric_distance(
        reachability.symmetric_distance, n, "reachability_distance"
    )
    method = (
        "negative-log exact eventual first-passage support under frozen sub-stochastic "
        f"operator; floor={reachability.support_floor:g}; "
        f"symmetrization={reachability.symmetrization}"
    )
    payload = {
        "node_ids": list(ids),
        "geographic_distance": _matrix_payload(d_geo),
        "environmental_distance": _matrix_payload(d_env),
        "reachability_distance": _matrix_payload(d_eog),
        "reachability_directional_distance": _matrix_payload(
            reachability.directional_distance
        ),
        "zero_support": reachability.zero_support.astype(int).tolist(),
        "reachability_method": method,
        "reachability_fingerprint": reachability.fingerprint,
    }
    return GeneticValidationDistanceBundle(
        node_ids=ids,
        geographic_distance=d_geo.copy(),
        environmental_distance=d_env.copy(),
        reachability_distance=d_eog.copy(),
        reachability_directional_distance=reachability.directional_distance.copy(),
        reachability_method=method,
        reachability_fingerprint=reachability.fingerprint,
        fingerprint=_sha256(payload),
    )
