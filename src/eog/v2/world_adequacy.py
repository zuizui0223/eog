"""Response-blind structural adequacy audits for declared EOG-WF worlds.

This module is validation infrastructure, not a new ecological transition operator.
It inspects only node IDs, world adjacency matrices, a declared forecast horizon, and
prospectively chosen structural criteria. Species occurrences, heldout responses, and
predictive scores are intentionally absent from the API.

There are no universal adequacy thresholds. Callers must freeze a
``StructuralAdequacyDeclaration`` before response access when they want a pass/fail
gate. The raw audit remains useful without any declaration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fraction(value: float | None, label: str) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not np.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must lie in [0, 1] when supplied")
    return result


@dataclass(frozen=True)
class StructuralAdequacyDeclaration:
    """Prospectively declared response-blind structural eligibility criteria.

    Any criterion may be omitted. At least one criterion must be declared when this
    object is used for pass/fail gating. Threshold values are design choices that must
    be justified outside this module; they are not biological constants inferred here.
    """

    min_largest_weak_component_fraction: float | None = None
    max_isolated_node_fraction: float | None = None
    min_median_horizon_reachable_fraction: float | None = None
    require_at_least_one_world_pass: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "min_largest_weak_component_fraction",
            _fraction(
                self.min_largest_weak_component_fraction,
                "min_largest_weak_component_fraction",
            ),
        )
        object.__setattr__(
            self,
            "max_isolated_node_fraction",
            _fraction(self.max_isolated_node_fraction, "max_isolated_node_fraction"),
        )
        object.__setattr__(
            self,
            "min_median_horizon_reachable_fraction",
            _fraction(
                self.min_median_horizon_reachable_fraction,
                "min_median_horizon_reachable_fraction",
            ),
        )
        if not any(
            value is not None
            for value in (
                self.min_largest_weak_component_fraction,
                self.max_isolated_node_fraction,
                self.min_median_horizon_reachable_fraction,
            )
        ):
            raise ValueError("at least one structural adequacy criterion must be declared")


@dataclass(frozen=True)
class WorldStructuralAudit:
    world_id: str
    node_count: int
    directed_edge_count: int
    weak_component_count: int
    largest_weak_component_size: int
    largest_weak_component_fraction: float
    isolated_node_count: int
    isolated_node_fraction: float
    mean_out_degree: float
    median_out_degree: float
    max_out_degree: int
    median_horizon_reachable_fraction: float
    min_horizon_reachable_fraction: float
    max_horizon_reachable_fraction: float
    horizon: int
    fingerprint: str


@dataclass(frozen=True)
class WorldStructuralGateResult:
    world_id: str
    passed: bool
    failed_criteria: tuple[str, ...]
    audit_fingerprint: str


@dataclass(frozen=True)
class WorldUniverseStructuralAudit:
    node_ids: tuple[str, ...]
    world_audits: tuple[WorldStructuralAudit, ...]
    horizon: int
    most_spanning_world_id: str
    fingerprint: str


@dataclass(frozen=True)
class WorldUniverseStructuralGate:
    audit: WorldUniverseStructuralAudit
    declaration: StructuralAdequacyDeclaration
    world_results: tuple[WorldStructuralGateResult, ...]
    passed: bool
    passing_world_ids: tuple[str, ...]
    fingerprint: str


def _validate_adjacency(values: np.ndarray, n: int, world_id: str) -> np.ndarray:
    adjacency = np.asarray(values)
    if adjacency.shape != (n, n):
        raise ValueError(f"world {world_id!r} adjacency must have shape {(n, n)}")
    if adjacency.dtype == bool:
        result = adjacency.copy()
    else:
        numeric = np.asarray(adjacency, dtype=float)
        if not np.isfinite(numeric).all() or np.any(numeric < 0.0):
            raise ValueError(f"world {world_id!r} adjacency must be finite and non-negative")
        result = numeric > 0.0
    np.fill_diagonal(result, False)
    return result


def _weak_component_sizes(adjacency: np.ndarray) -> list[int]:
    undirected = adjacency | adjacency.T
    n = undirected.shape[0]
    seen = np.zeros(n, dtype=bool)
    sizes: list[int] = []
    for start in range(n):
        if seen[start]:
            continue
        frontier = [start]
        seen[start] = True
        size = 0
        while frontier:
            node = frontier.pop()
            size += 1
            neighbours = np.flatnonzero(undirected[node])
            for nxt in neighbours:
                nxt = int(nxt)
                if not seen[nxt]:
                    seen[nxt] = True
                    frontier.append(nxt)
        sizes.append(size)
    return sizes


def _horizon_reachable_fractions(adjacency: np.ndarray, horizon: int) -> np.ndarray:
    n = adjacency.shape[0]
    fractions = np.empty(n, dtype=float)
    for source in range(n):
        visited = np.zeros(n, dtype=bool)
        visited[source] = True
        frontier = visited.copy()
        for _ in range(horizon):
            active = np.flatnonzero(frontier)
            if active.size == 0:
                break
            reached = np.any(adjacency[active], axis=0)
            new = reached & ~visited
            if not np.any(new):
                break
            visited |= new
            frontier = new
        fractions[source] = float(np.mean(visited))
    return fractions


def audit_world_universe_structure(
    node_ids: Sequence[str],
    world_adjacencies: Mapping[str, np.ndarray],
    *,
    horizon: int,
) -> WorldUniverseStructuralAudit:
    """Audit a declared world universe without accepting any biological response.

    ``world_adjacencies`` may contain directed binary or non-negative weighted
    adjacency matrices; positive weights are treated as admitted directed edges for
    this structural audit. Reachability uses direction, while component summaries use
    weak connectivity and therefore remain interpretable for both directed and
    symmetric worlds.
    """

    ids = tuple(str(value).strip() for value in node_ids)
    if not ids or len(set(ids)) != len(ids) or any(not value for value in ids):
        raise ValueError("node_ids must contain unique non-empty IDs")
    if isinstance(horizon, bool) or not isinstance(horizon, (int, np.integer)) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if not world_adjacencies:
        raise ValueError("at least one world adjacency is required")

    audits: list[WorldStructuralAudit] = []
    for world_id in sorted(str(key) for key in world_adjacencies):
        if not world_id.strip():
            raise ValueError("world IDs must be non-empty")
        adjacency = _validate_adjacency(world_adjacencies[world_id], len(ids), world_id)
        sizes = _weak_component_sizes(adjacency)
        out_degree = np.sum(adjacency, axis=1)
        isolated = (np.sum(adjacency, axis=1) + np.sum(adjacency, axis=0)) == 0
        horizon_fraction = _horizon_reachable_fractions(adjacency, int(horizon))
        payload = {
            "world_id": world_id,
            "node_count": len(ids),
            "directed_edge_count": int(np.sum(adjacency)),
            "weak_component_count": len(sizes),
            "largest_weak_component_size": int(max(sizes)),
            "largest_weak_component_fraction": float(max(sizes) / len(ids)),
            "isolated_node_count": int(np.sum(isolated)),
            "isolated_node_fraction": float(np.mean(isolated)),
            "mean_out_degree": float(np.mean(out_degree)),
            "median_out_degree": float(np.median(out_degree)),
            "max_out_degree": int(np.max(out_degree)),
            "median_horizon_reachable_fraction": float(np.median(horizon_fraction)),
            "min_horizon_reachable_fraction": float(np.min(horizon_fraction)),
            "max_horizon_reachable_fraction": float(np.max(horizon_fraction)),
            "horizon": int(horizon),
        }
        audits.append(WorldStructuralAudit(**payload, fingerprint=_canonical_sha256(payload)))

    most_spanning = max(
        audits,
        key=lambda row: (
            row.largest_weak_component_fraction,
            row.median_horizon_reachable_fraction,
            -row.isolated_node_fraction,
            row.world_id,
        ),
    )
    payload = {
        "node_ids": list(ids),
        "worlds": [(row.world_id, row.fingerprint) for row in audits],
        "horizon": int(horizon),
        "most_spanning_world_id": most_spanning.world_id,
    }
    return WorldUniverseStructuralAudit(
        node_ids=ids,
        world_audits=tuple(audits),
        horizon=int(horizon),
        most_spanning_world_id=most_spanning.world_id,
        fingerprint=_canonical_sha256(payload),
    )


def apply_structural_adequacy_gate(
    audit: WorldUniverseStructuralAudit,
    declaration: StructuralAdequacyDeclaration,
) -> WorldUniverseStructuralGate:
    """Apply prospectively declared criteria to a response-blind structural audit."""

    results: list[WorldStructuralGateResult] = []
    passing: list[str] = []
    for row in audit.world_audits:
        failed: list[str] = []
        if (
            declaration.min_largest_weak_component_fraction is not None
            and row.largest_weak_component_fraction
            < declaration.min_largest_weak_component_fraction
        ):
            failed.append("min_largest_weak_component_fraction")
        if (
            declaration.max_isolated_node_fraction is not None
            and row.isolated_node_fraction > declaration.max_isolated_node_fraction
        ):
            failed.append("max_isolated_node_fraction")
        if (
            declaration.min_median_horizon_reachable_fraction is not None
            and row.median_horizon_reachable_fraction
            < declaration.min_median_horizon_reachable_fraction
        ):
            failed.append("min_median_horizon_reachable_fraction")
        passed = not failed
        if passed:
            passing.append(row.world_id)
        results.append(
            WorldStructuralGateResult(
                world_id=row.world_id,
                passed=passed,
                failed_criteria=tuple(failed),
                audit_fingerprint=row.fingerprint,
            )
        )

    gate_passed = bool(passing) if declaration.require_at_least_one_world_pass else all(
        row.passed for row in results
    )
    payload = {
        "audit_fingerprint": audit.fingerprint,
        "declaration": {
            "min_largest_weak_component_fraction": declaration.min_largest_weak_component_fraction,
            "max_isolated_node_fraction": declaration.max_isolated_node_fraction,
            "min_median_horizon_reachable_fraction": declaration.min_median_horizon_reachable_fraction,
            "require_at_least_one_world_pass": declaration.require_at_least_one_world_pass,
        },
        "world_results": [
            {
                "world_id": row.world_id,
                "passed": row.passed,
                "failed_criteria": list(row.failed_criteria),
                "audit_fingerprint": row.audit_fingerprint,
            }
            for row in results
        ],
        "passed": gate_passed,
        "passing_world_ids": passing,
    }
    return WorldUniverseStructuralGate(
        audit=audit,
        declaration=declaration,
        world_results=tuple(results),
        passed=gate_passed,
        passing_world_ids=tuple(passing),
        fingerprint=_canonical_sha256(payload),
    )
