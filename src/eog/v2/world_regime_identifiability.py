"""Response-blind identifiability audit for EOG world-survival regimes.

The one-step positive-evidence update depends on *where* positive observations occur,
not only on whole-network structure.  For a symmetric structural world and a positive
node set P, the world survives exactly when the subgraph induced by P has no isolated
positive node.

This module therefore does not forecast a realised regime.  Instead it asks which
regimes are structurally possible under alternative positive placements and records
explicit witness sets.  The pair audit is exact for positive sets of size two and gives a
minimal certificate of non-identifiability: if two possible positive pairs imply
different survival regimes, no deterministic response-blind function of the frozen
world graphs alone can identify the later regime without an additional model for where
positive evidence will occur.

This is structural diagnosis, not a probability model for positive placement.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import combinations
from typing import Literal, Mapping, Sequence

import numpy as np

from .world_survival_regime_v2 import deduplicate_structural_worlds


WorldSurvivalRegime = Literal[
    "falsified_universe",
    "contracting",
    "saturated",
]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _regime(surviving_count: int, world_count: int) -> WorldSurvivalRegime:
    if surviving_count == 0:
        return "falsified_universe"
    if surviving_count == world_count:
        return "saturated"
    return "contracting"


@dataclass(frozen=True)
class PairRegimeWitness:
    node_ids: tuple[str, str]
    surviving_world_ids: tuple[str, ...]
    surviving_world_fraction: float
    regime: WorldSurvivalRegime
    fingerprint: str


@dataclass(frozen=True)
class PairRegimeIdentifiabilityAudit:
    node_ids: tuple[str, ...]
    declared_world_count: int
    distinct_world_count: int
    distinct_world_ids: tuple[str, ...]
    pair_count: int
    regime_pair_counts: tuple[tuple[str, int], ...]
    regime_pair_fractions: tuple[tuple[str, float], ...]
    possible_pair_regimes: tuple[WorldSurvivalRegime, ...]
    pair_regime_identifiable: bool
    minimum_pair_surviving_world_fraction: float
    maximum_pair_surviving_world_fraction: float
    witness_by_regime: tuple[PairRegimeWitness, ...]
    deduplication_fingerprint: str
    fingerprint: str


def _validated_node_ids(node_ids: Sequence[str], n: int) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in node_ids)
    if len(ids) != n or any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("node_ids must contain exactly one unique non-empty ID per node")
    return ids


def _validated_symmetric_worlds(
    world_adjacencies: Mapping[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], int]:
    if not world_adjacencies:
        raise ValueError("at least one structural world is required")
    result: dict[str, np.ndarray] = {}
    n: int | None = None
    for raw_id in sorted(world_adjacencies):
        world_id = str(raw_id).strip()
        if not world_id:
            raise ValueError("world IDs must be non-empty")
        values = np.asarray(world_adjacencies[raw_id])
        if values.ndim != 2 or values.shape[0] != values.shape[1]:
            raise ValueError(f"world {world_id!r} adjacency must be square")
        if n is None:
            n = int(values.shape[0])
        elif values.shape != (n, n):
            raise ValueError("all world adjacencies must have the same shape")
        if values.dtype == bool:
            matrix = values.copy()
        else:
            numeric = np.asarray(values, dtype=float)
            if not np.isfinite(numeric).all() or np.any(numeric < 0.0):
                raise ValueError(
                    f"world {world_id!r} adjacency must be finite and non-negative"
                )
            matrix = numeric > 0.0
        np.fill_diagonal(matrix, False)
        if not np.array_equal(matrix, matrix.T):
            raise ValueError(
                "pair-regime identifiability v1 requires symmetric structural worlds"
            )
        result[world_id] = matrix
    assert n is not None
    if n < 2:
        raise ValueError("at least two nodes are required")
    return result, n


def audit_pair_regime_identifiability(
    node_ids: Sequence[str],
    world_adjacencies: Mapping[str, np.ndarray],
) -> PairRegimeIdentifiabilityAudit:
    """Enumerate exact size-two positive-set regimes after operator deduplication.

    For two positive nodes {u, v}, a symmetric one-step world survives iff u and v are
    adjacent.  The number of distinct worlds containing that pair therefore gives the
    exact survival fraction and regime for that possible positive placement.
    """

    normalized, n = _validated_symmetric_worlds(world_adjacencies)
    ids = _validated_node_ids(node_ids, n)
    dedup = deduplicate_structural_worlds(normalized)
    worlds = {
        world_id: np.asarray(matrix, dtype=bool)
        for world_id, matrix in dedup.world_adjacencies.items()
    }
    world_ids = tuple(sorted(worlds))
    m = len(world_ids)

    regime_order: tuple[WorldSurvivalRegime, ...] = (
        "falsified_universe",
        "contracting",
        "saturated",
    )
    counts = {name: 0 for name in regime_order}
    first_witness: dict[WorldSurvivalRegime, PairRegimeWitness] = {}
    fractions: list[float] = []

    for left, right in combinations(range(n), 2):
        surviving = tuple(
            world_id
            for world_id in world_ids
            if bool(worlds[world_id][left, right])
        )
        fraction = len(surviving) / m
        regime = _regime(len(surviving), m)
        counts[regime] += 1
        fractions.append(fraction)
        if regime not in first_witness:
            payload = {
                "node_ids": [ids[left], ids[right]],
                "surviving_world_ids": list(surviving),
                "surviving_world_fraction": fraction,
                "regime": regime,
            }
            first_witness[regime] = PairRegimeWitness(
                node_ids=(ids[left], ids[right]),
                surviving_world_ids=surviving,
                surviving_world_fraction=float(fraction),
                regime=regime,
                fingerprint=_canonical_sha256(payload),
            )

    pair_count = len(fractions)
    possible = tuple(name for name in regime_order if counts[name] > 0)
    payload = {
        "node_ids": list(ids),
        "declared_world_count": dedup.declared_world_count,
        "distinct_world_count": dedup.distinct_world_count,
        "distinct_world_ids": list(world_ids),
        "pair_count": pair_count,
        "regime_pair_counts": [[name, counts[name]] for name in regime_order],
        "regime_pair_fractions": [
            [name, counts[name] / pair_count] for name in regime_order
        ],
        "possible_pair_regimes": list(possible),
        "pair_regime_identifiable": len(possible) == 1,
        "minimum_pair_surviving_world_fraction": min(fractions),
        "maximum_pair_surviving_world_fraction": max(fractions),
        "witness_by_regime": [
            first_witness[name].fingerprint
            for name in regime_order
            if name in first_witness
        ],
        "deduplication_fingerprint": dedup.fingerprint,
    }
    return PairRegimeIdentifiabilityAudit(
        node_ids=ids,
        declared_world_count=dedup.declared_world_count,
        distinct_world_count=dedup.distinct_world_count,
        distinct_world_ids=world_ids,
        pair_count=pair_count,
        regime_pair_counts=tuple((name, counts[name]) for name in regime_order),
        regime_pair_fractions=tuple(
            (name, counts[name] / pair_count) for name in regime_order
        ),
        possible_pair_regimes=possible,
        pair_regime_identifiable=len(possible) == 1,
        minimum_pair_surviving_world_fraction=float(min(fractions)),
        maximum_pair_surviving_world_fraction=float(max(fractions)),
        witness_by_regime=tuple(
            first_witness[name]
            for name in regime_order
            if name in first_witness
        ),
        deduplication_fingerprint=dedup.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def positive_set_world_survival(
    positive_node_ids: Sequence[str],
    *,
    node_ids: Sequence[str],
    world_adjacencies: Mapping[str, np.ndarray],
) -> tuple[str, ...]:
    """Return distinct symmetric worlds whose positive induced subgraph has no isolates."""

    normalized, n = _validated_symmetric_worlds(world_adjacencies)
    ids = _validated_node_ids(node_ids, n)
    dedup = deduplicate_structural_worlds(normalized)
    requested = tuple(str(value).strip() for value in positive_node_ids)
    if len(requested) < 2 or any(not value for value in requested):
        raise ValueError("positive_node_ids must contain at least two non-empty IDs")
    if len(set(requested)) != len(requested):
        raise ValueError("positive_node_ids must be unique")
    index = {node_id: i for i, node_id in enumerate(ids)}
    missing = sorted(set(requested) - set(index))
    if missing:
        raise ValueError(f"positive nodes outside node universe: {missing}")
    positive_indices = np.asarray([index[node_id] for node_id in requested], dtype=int)

    surviving: list[str] = []
    for world_id in sorted(dedup.world_adjacencies):
        adjacency = np.asarray(dedup.world_adjacencies[world_id], dtype=bool)
        induced = adjacency[np.ix_(positive_indices, positive_indices)]
        degrees = np.sum(induced, axis=1)
        if bool(np.all(degrees >= 1)):
            surviving.append(world_id)
    return tuple(surviving)
