"""World-survival regime v2: one-transition structure and operator deduplication.

V1 was falsified before biological response because graph-closure horizon (n-1) made
high-LCC undirected worlds survive by construction. V2 changes no outcome-tuned cutoff.
It makes two response-blind corrections only:

1. structural horizon is exactly one admitted transition;
2. structurally identical adjacency operators count once in the survival denominator.

The v1 horizon-realization cutoff of 0.5 is retained unchanged. This module does not
open biological responses and does not alter any closed EOG-WF result.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

import numpy as np

from .world_adequacy import (
    StructuralAdequacyDeclaration,
    WorldUniverseStructuralAudit,
    WorldUniverseStructuralGate,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from .world_survival_regime import (
    RegimeForecastDeclaration,
    WorldSurvivalRegimeForecast,
    forecast_world_survival_regime,
)


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _adjacency(values: np.ndarray, world_id: str) -> np.ndarray:
    matrix = np.asarray(values)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"world {world_id!r} adjacency must be square")
    if matrix.dtype == bool:
        result = matrix.copy()
    else:
        numeric = np.asarray(matrix, dtype=float)
        if not np.isfinite(numeric).all() or np.any(numeric < 0.0):
            raise ValueError(
                f"world {world_id!r} adjacency must be finite and non-negative"
            )
        result = numeric > 0.0
    np.fill_diagonal(result, False)
    return result


@dataclass(frozen=True)
class StructuralWorldAliasGroup:
    canonical_world_id: str
    alias_world_ids: tuple[str, ...]
    adjacency_fingerprint: str


@dataclass(frozen=True)
class DeduplicatedStructuralWorlds:
    world_adjacencies: Mapping[str, np.ndarray]
    alias_groups: tuple[StructuralWorldAliasGroup, ...]
    declared_world_count: int
    distinct_world_count: int
    fingerprint: str


@dataclass(frozen=True)
class WorldSurvivalRegimeV2Preparation:
    deduplication: DeduplicatedStructuralWorlds
    audit: WorldUniverseStructuralAudit
    gate: WorldUniverseStructuralGate
    forecast: WorldSurvivalRegimeForecast
    fingerprint: str


def deduplicate_structural_worlds(
    world_adjacencies: Mapping[str, np.ndarray],
) -> DeduplicatedStructuralWorlds:
    """Collapse label-duplicated worlds with identical admitted edges.

    Canonical IDs are the lexicographically smallest IDs inside each exact adjacency
    group. Alias identities remain auditable, but each distinct operator has weight one
    in downstream survival fractions.
    """

    if not world_adjacencies:
        raise ValueError("at least one structural world is required")

    normalized: dict[str, np.ndarray] = {}
    shape: tuple[int, int] | None = None
    for raw_id in sorted(world_adjacencies):
        world_id = str(raw_id).strip()
        if not world_id:
            raise ValueError("world IDs must be non-empty")
        matrix = _adjacency(world_adjacencies[raw_id], world_id)
        if shape is None:
            shape = matrix.shape
        elif matrix.shape != shape:
            raise ValueError("all world adjacencies must have the same shape")
        normalized[world_id] = matrix

    by_fingerprint: dict[str, list[str]] = {}
    matrices: dict[str, np.ndarray] = {}
    for world_id, matrix in normalized.items():
        fp = _canonical_sha256(
            {
                "shape": list(matrix.shape),
                "adjacency": matrix.astype(int).tolist(),
            }
        )
        by_fingerprint.setdefault(fp, []).append(world_id)
        matrices.setdefault(fp, matrix)

    groups: list[StructuralWorldAliasGroup] = []
    canonical: dict[str, np.ndarray] = {}
    for fp in sorted(by_fingerprint):
        aliases = tuple(sorted(by_fingerprint[fp]))
        canonical_id = aliases[0]
        canonical[canonical_id] = matrices[fp].copy()
        groups.append(
            StructuralWorldAliasGroup(
                canonical_world_id=canonical_id,
                alias_world_ids=aliases,
                adjacency_fingerprint=fp,
            )
        )

    groups.sort(key=lambda row: row.canonical_world_id)
    canonical = {
        world_id: canonical[world_id]
        for world_id in sorted(canonical)
    }
    payload = {
        "declared_world_count": len(normalized),
        "distinct_world_count": len(canonical),
        "alias_groups": [
            {
                "canonical_world_id": row.canonical_world_id,
                "alias_world_ids": list(row.alias_world_ids),
                "adjacency_fingerprint": row.adjacency_fingerprint,
            }
            for row in groups
        ],
    }
    return DeduplicatedStructuralWorlds(
        world_adjacencies=canonical,
        alias_groups=tuple(groups),
        declared_world_count=len(normalized),
        distinct_world_count=len(canonical),
        fingerprint=_canonical_sha256(payload),
    )


def prepare_world_survival_regime_v2(
    node_ids: tuple[str, ...],
    world_adjacencies: Mapping[str, np.ndarray],
    *,
    adequacy: StructuralAdequacyDeclaration,
    horizon_realization_cutoff: float = 0.5,
) -> WorldSurvivalRegimeV2Preparation:
    """Deduplicate, audit at one transition, gate, and freeze the v2 forecast."""

    if adequacy.min_median_horizon_reachable_fraction is not None:
        raise ValueError(
            "v2 reserves one-step horizon reachability for regime forecasting, "
            "not structural adequacy gating"
        )

    dedup = deduplicate_structural_worlds(world_adjacencies)
    audit = audit_world_universe_structure(
        node_ids,
        dedup.world_adjacencies,
        horizon=1,
    )
    gate = apply_structural_adequacy_gate(audit, adequacy)
    if not gate.passed:
        raise ValueError("structural adequacy gate failed before v2 forecasting")
    forecast = forecast_world_survival_regime(
        audit,
        gate,
        RegimeForecastDeclaration(
            horizon_realization_cutoff=horizon_realization_cutoff
        ),
    )
    payload = {
        "deduplication_fingerprint": dedup.fingerprint,
        "audit_fingerprint": audit.fingerprint,
        "gate_fingerprint": gate.fingerprint,
        "forecast_fingerprint": forecast.fingerprint,
        "structural_horizon": 1,
        "horizon_realization_cutoff": float(horizon_realization_cutoff),
    }
    return WorldSurvivalRegimeV2Preparation(
        deduplication=dedup,
        audit=audit,
        gate=gate,
        forecast=forecast,
        fingerprint=_canonical_sha256(payload),
    )
