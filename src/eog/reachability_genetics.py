"""Leakage-safe distance contracts for prospective genetic validation of EOG-R.

The functions here derive reachability distances from a *frozen* dynamic transition
operator. Genetic observations are deliberately absent from every constructor.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .dynamic_island_reachability import (
    DynamicTransitionOperator,
    summarize_first_passage,
)


@dataclass(frozen=True)
class ReachabilityDistanceResult:
    node_ids: tuple[str, ...]
    directional_support: np.ndarray
    directional_distance: np.ndarray
    symmetric_distance: np.ndarray
    max_steps: int
    support_floor: float
    symmetrization: str
    operator_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class GeneticValidationDistanceBundle:
    """Frozen IBD/IBE/EOG distance inputs with no genetic response data attached."""

    node_ids: tuple[str, ...]
    geographic_distance: np.ndarray
    environmental_distance: np.ndarray
    reachability_distance: np.ndarray
    reachability_directional_distance: np.ndarray
    reachability_method: str
    reachability_fingerprint: str
    fingerprint: str


def _matrix_payload(matrix: np.ndarray) -> list[list[float]]:
    return np.asarray(matrix, dtype=float).tolist()


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def pairwise_reachability_distances(
    operator: DynamicTransitionOperator,
    sampled_node_ids: Sequence[str] | None = None,
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    symmetrization: str,
) -> ReachabilityDistanceResult:
    """Derive directional and symmetric EOG-R isolation distances.

    Directional distance is ``-log(first_passage_support)`` within the declared
    propagation horizon. Unreached pairs are capped at ``-log(support_floor)`` rather
    than treated as infinite so downstream models remain numerically explicit.

    ``symmetrization`` must be declared as either ``"mean_log"`` (arithmetic mean of
    the two directional log distances) or ``"max_log"`` (the more isolated direction).
    No default is provided because this choice must be frozen before genetic outcomes
    are inspected.
    """

    if not isinstance(max_steps, (int, np.integer)) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not np.isfinite(support_floor) or not (0.0 < support_floor < 1.0):
        raise ValueError("support_floor must lie strictly between 0 and 1")
    if symmetrization not in {"mean_log", "max_log"}:
        raise ValueError("symmetrization must be 'mean_log' or 'max_log'")

    ids = operator.node_ids if sampled_node_ids is None else tuple(str(x) for x in sampled_node_ids)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("sampled_node_ids must contain at least two unique IDs")
    if any(node_id not in operator.node_ids for node_id in ids):
        raise ValueError("all sampled_node_ids must occur in the operator")

    n = len(ids)
    support = np.zeros((n, n), dtype=float)
    np.fill_diagonal(support, 1.0)
    for i, source_id in enumerate(ids):
        for j, target_id in enumerate(ids):
            if i == j:
                continue
            summary = summarize_first_passage(
                operator,
                [source_id],
                target_id,
                max_steps=max_steps,
            )
            support[i, j] = summary.horizon_support

    directional = -np.log(np.maximum(support, support_floor))
    np.fill_diagonal(directional, 0.0)
    if symmetrization == "mean_log":
        symmetric = 0.5 * (directional + directional.T)
    else:
        symmetric = np.maximum(directional, directional.T)
    np.fill_diagonal(symmetric, 0.0)

    payload = {
        "node_ids": list(ids),
        "directional_support": _matrix_payload(support),
        "directional_distance": _matrix_payload(directional),
        "symmetric_distance": _matrix_payload(symmetric),
        "max_steps": int(max_steps),
        "support_floor": float(support_floor),
        "symmetrization": symmetrization,
        "operator_fingerprint": operator.fingerprint,
    }
    return ReachabilityDistanceResult(
        node_ids=ids,
        directional_support=support,
        directional_distance=directional,
        symmetric_distance=symmetric,
        max_steps=int(max_steps),
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


def build_genetic_validation_distance_bundle(
    geographic_distance: np.ndarray,
    environmental_distance: np.ndarray,
    reachability: ReachabilityDistanceResult,
) -> GeneticValidationDistanceBundle:
    """Freeze IBD, IBE and EOG-R distances before attaching a genetic response.

    The function accepts only distance objects and therefore cannot tune the EOG-R
    network to FST, allele frequencies, migration surfaces, or phylogeographic labels.
    """

    ids = reachability.node_ids
    n = len(ids)
    d_geo = _validate_symmetric_distance(geographic_distance, n, "geographic_distance")
    d_env = _validate_symmetric_distance(environmental_distance, n, "environmental_distance")
    d_eog = _validate_symmetric_distance(reachability.symmetric_distance, n, "reachability_distance")

    method = (
        f"negative-log first-passage support; horizon={reachability.max_steps}; "
        f"floor={reachability.support_floor:g}; symmetrization={reachability.symmetrization}"
    )
    payload = {
        "node_ids": list(ids),
        "geographic_distance": _matrix_payload(d_geo),
        "environmental_distance": _matrix_payload(d_env),
        "reachability_distance": _matrix_payload(d_eog),
        "reachability_directional_distance": _matrix_payload(reachability.directional_distance),
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
