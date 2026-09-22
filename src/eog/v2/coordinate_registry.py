"""Prospective coordinate-registry audits for dataset-neutral EOG adapters.

A repeated node may appear in multiple deployments or survey rows with slightly
different coordinates. This module separates a response-independent tolerance audit
from the downstream scientific geometry. Any tolerance and representative-coordinate
policy must be declared before response access.

No coordinate is silently snapped or averaged: aggregation occurs only through the
explicit representative_policy in CoordinateRegistryPolicy.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from statistics import median
from typing import Literal, Sequence


RepresentativePolicy = Literal["first", "mean", "median"]


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _finite(value: object, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


@dataclass(frozen=True)
class CoordinateObservation:
    node_id: str
    x: float
    y: float

    def __post_init__(self) -> None:
        node = _text(self.node_id, "node_id")
        x = _finite(self.x, "x")
        y = _finite(self.y, "y")
        object.__setattr__(self, "node_id", node)
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)


@dataclass(frozen=True)
class CoordinateRegistryPolicy:
    tolerance: float
    units: str
    representative_policy: RepresentativePolicy

    def __post_init__(self) -> None:
        tolerance = _finite(self.tolerance, "tolerance")
        if tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        units = _text(self.units, "units")
        if self.representative_policy not in {"first", "mean", "median"}:
            raise ValueError("representative_policy must be first, mean, or median")
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "units", units)

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "schema": "eog.coordinate_registry_policy.v1",
                "tolerance": float(self.tolerance),
                "units": self.units,
                "representative_policy": self.representative_policy,
            }
        )


@dataclass(frozen=True)
class NodeCoordinateAudit:
    node_id: str
    observation_count: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    x_span: float
    y_span: float
    representative_x: float
    representative_y: float
    status: str
    fingerprint: str


@dataclass(frozen=True)
class CoordinateRegistryAudit:
    nodes: tuple[NodeCoordinateAudit, ...]
    policy_fingerprint: str
    exact_node_count: int
    tolerance_used_node_count: int
    maximum_x_span: float
    maximum_y_span: float
    status: str
    fingerprint: str

    @property
    def coordinates(self) -> dict[str, tuple[float, float]]:
        return {
            node.node_id: (node.representative_x, node.representative_y)
            for node in self.nodes
        }


def _representative(
    values: Sequence[CoordinateObservation],
    policy: RepresentativePolicy,
) -> tuple[float, float]:
    if policy == "first":
        return float(values[0].x), float(values[0].y)
    xs = [float(value.x) for value in values]
    ys = [float(value.y) for value in values]
    if policy == "mean":
        return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))
    return float(median(xs)), float(median(ys))


def audit_coordinate_registry(
    observations: Sequence[CoordinateObservation],
    policy: CoordinateRegistryPolicy,
) -> CoordinateRegistryAudit:
    """Validate within-node coordinate stability under one frozen tolerance policy.

    Tolerance is applied to the full within-node span on each axis, not to successive
    row-to-row changes. This prevents a chain of individually small drifts from escaping
    the declared bound.
    """

    values = tuple(observations)
    if not values:
        raise ValueError("observations must not be empty")

    grouped: dict[str, list[CoordinateObservation]] = {}
    for observation in values:
        if not isinstance(observation, CoordinateObservation):
            raise TypeError("observations must contain CoordinateObservation values")
        grouped.setdefault(observation.node_id, []).append(observation)

    node_audits: list[NodeCoordinateAudit] = []
    for node_id in sorted(grouped):
        node_values = grouped[node_id]
        xs = [float(value.x) for value in node_values]
        ys = [float(value.y) for value in node_values]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_span = float(x_max - x_min)
        y_span = float(y_max - y_min)
        if x_span > policy.tolerance or y_span > policy.tolerance:
            raise ValueError(
                f"coordinate drift exceeds frozen tolerance for node {node_id!r}: "
                f"x_span={x_span}, y_span={y_span}, tolerance={policy.tolerance} "
                f"{policy.units}"
            )

        representative_x, representative_y = _representative(
            node_values, policy.representative_policy
        )
        status = "exact" if x_span == 0.0 and y_span == 0.0 else "within_tolerance"
        payload = {
            "node_id": node_id,
            "observation_count": len(node_values),
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
            "x_span": x_span,
            "y_span": y_span,
            "representative_x": representative_x,
            "representative_y": representative_y,
            "status": status,
            "policy_fingerprint": policy.fingerprint,
        }
        node_audits.append(
            NodeCoordinateAudit(
                node_id=node_id,
                observation_count=len(node_values),
                x_min=float(x_min),
                x_max=float(x_max),
                y_min=float(y_min),
                y_max=float(y_max),
                x_span=x_span,
                y_span=y_span,
                representative_x=representative_x,
                representative_y=representative_y,
                status=status,
                fingerprint=_sha256(payload),
            )
        )

    exact_count = sum(node.status == "exact" for node in node_audits)
    tolerance_count = len(node_audits) - exact_count
    max_x = max(node.x_span for node in node_audits)
    max_y = max(node.y_span for node in node_audits)
    status = "exact_registry" if tolerance_count == 0 else "within_frozen_tolerance"
    payload = {
        "schema": "eog.coordinate_registry_audit.v1",
        "policy_fingerprint": policy.fingerprint,
        "nodes": [
            {
                "node_id": node.node_id,
                "observation_count": node.observation_count,
                "x_min": node.x_min,
                "x_max": node.x_max,
                "y_min": node.y_min,
                "y_max": node.y_max,
                "x_span": node.x_span,
                "y_span": node.y_span,
                "representative_x": node.representative_x,
                "representative_y": node.representative_y,
                "status": node.status,
                "fingerprint": node.fingerprint,
            }
            for node in node_audits
        ],
        "exact_node_count": exact_count,
        "tolerance_used_node_count": tolerance_count,
        "maximum_x_span": max_x,
        "maximum_y_span": max_y,
        "status": status,
    }
    return CoordinateRegistryAudit(
        nodes=tuple(node_audits),
        policy_fingerprint=policy.fingerprint,
        exact_node_count=exact_count,
        tolerance_used_node_count=tolerance_count,
        maximum_x_span=float(max_x),
        maximum_y_span=float(max_y),
        status=status,
        fingerprint=_sha256(payload),
    )
