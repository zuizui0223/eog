"""Identifiability boundary for one-step positive-evidence world survival.

For the EOG one-step, self-excluded peer-positive compatibility rule, a world survives
an observed positive set P exactly when every node in P has at least one neighbour in P.
Equivalently, the induced subgraph G[P] has minimum degree at least one.

This creates a hard response-blind identifiability boundary. For any undirected graph
that contains at least one edge and at least one non-edge, two positive nodes can be
placed on an adjacent pair (world survives) or on a non-adjacent pair (world fails).
The graph, its global structural summaries, and the positive-set cardinality are
identical in both cases.

Therefore no deterministic function of response-blind graph structure alone can
universally identify later world survival under this observation rule. A probabilistic
forecast requires additional assumptions about where positive nodes are likely to occur.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import combinations
from typing import Sequence

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


def _adjacency(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("adjacency must be square")
    if matrix.dtype == bool:
        result = matrix.copy()
    else:
        numeric = np.asarray(matrix, dtype=float)
        if not np.isfinite(numeric).all() or np.any(numeric < 0.0):
            raise ValueError("adjacency must be finite and non-negative")
        result = numeric > 0.0
    if not np.array_equal(result, result.T):
        raise ValueError("this identifiability theorem requires an undirected adjacency")
    np.fill_diagonal(result, False)
    return result


def one_step_positive_set_compatible(
    adjacency: np.ndarray,
    positive_indices: Sequence[int],
) -> bool:
    """Return whether every positive node has at least one positive peer neighbour."""

    graph = _adjacency(adjacency)
    indices = tuple(int(value) for value in positive_indices)
    if len(indices) < 2 or len(set(indices)) != len(indices):
        raise ValueError("positive_indices must contain at least two unique nodes")
    n = graph.shape[0]
    if any(index < 0 or index >= n for index in indices):
        raise ValueError("positive index lies outside the graph")

    selected = np.asarray(indices, dtype=int)
    induced = graph[np.ix_(selected, selected)]
    return bool(np.all(np.sum(induced, axis=1) >= 1))


@dataclass(frozen=True)
class PairWitness:
    first: int
    second: int

    @property
    def as_tuple(self) -> tuple[int, int]:
        return (self.first, self.second)


@dataclass(frozen=True)
class PairSurvivalIdentifiability:
    node_count: int
    edge_count: int
    nonedge_count: int
    compatible_pair_witness: PairWitness | None
    incompatible_pair_witness: PairWitness | None
    both_outcomes_possible_for_two_positives: bool
    structurally_identifiable_for_two_positives: bool
    structural_outcome_if_identifiable: str | None
    fingerprint: str


def audit_two_positive_survival_identifiability(
    adjacency: np.ndarray,
) -> PairSurvivalIdentifiability:
    """Audit whether graph structure determines survival for exactly two positives.

    For two positives, compatibility is exactly adjacency of the pair. Thus any graph
    with at least one edge and at least one non-edge admits both survival outcomes while
    all response-blind structural quantities remain unchanged.
    """

    graph = _adjacency(adjacency)
    n = graph.shape[0]
    if n < 2:
        raise ValueError("at least two nodes are required")

    compatible: PairWitness | None = None
    incompatible: PairWitness | None = None
    edge_count = 0
    nonedge_count = 0
    for left, right in combinations(range(n), 2):
        if bool(graph[left, right]):
            edge_count += 1
            if compatible is None:
                compatible = PairWitness(left, right)
        else:
            nonedge_count += 1
            if incompatible is None:
                incompatible = PairWitness(left, right)

    both = compatible is not None and incompatible is not None
    if both:
        outcome = None
    elif compatible is not None:
        outcome = "survives"
    else:
        outcome = "fails"

    payload = {
        "node_count": n,
        "edge_count": edge_count,
        "nonedge_count": nonedge_count,
        "compatible_pair_witness": (
            None if compatible is None else list(compatible.as_tuple)
        ),
        "incompatible_pair_witness": (
            None if incompatible is None else list(incompatible.as_tuple)
        ),
        "both_outcomes_possible_for_two_positives": both,
        "structurally_identifiable_for_two_positives": not both,
        "structural_outcome_if_identifiable": outcome,
    }
    return PairSurvivalIdentifiability(
        node_count=n,
        edge_count=edge_count,
        nonedge_count=nonedge_count,
        compatible_pair_witness=compatible,
        incompatible_pair_witness=incompatible,
        both_outcomes_possible_for_two_positives=both,
        structurally_identifiable_for_two_positives=not both,
        structural_outcome_if_identifiable=outcome,
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class PositiveSetCardinalityAudit:
    node_count: int
    positive_count: int
    compatible_configuration_count: int
    incompatible_configuration_count: int
    total_configuration_count: int
    compatible_witness: tuple[int, ...] | None
    incompatible_witness: tuple[int, ...] | None
    both_outcomes_possible: bool
    fingerprint: str


def audit_positive_set_cardinality_exhaustive(
    adjacency: np.ndarray,
    *,
    positive_count: int,
    max_combinations: int = 100_000,
) -> PositiveSetCardinalityAudit:
    """Exhaustively audit small graphs at one fixed positive-set cardinality.

    This helper is intended for synthetic proof fixtures and small demonstrations, not
    large empirical graphs. It asks whether the same graph and same positive count admit
    both a compatible and an incompatible placement.
    """

    graph = _adjacency(adjacency)
    n = graph.shape[0]
    count = int(positive_count)
    if count < 2 or count > n:
        raise ValueError("positive_count must lie in [2, node_count]")

    total = int(np.math.comb(n, count)) if hasattr(np, "math") else None
    if total is None:
        import math
        total = math.comb(n, count)
    if total > int(max_combinations):
        raise ValueError("configuration count exceeds max_combinations")

    compatible_count = 0
    incompatible_count = 0
    compatible_witness: tuple[int, ...] | None = None
    incompatible_witness: tuple[int, ...] | None = None
    for subset in combinations(range(n), count):
        if one_step_positive_set_compatible(graph, subset):
            compatible_count += 1
            if compatible_witness is None:
                compatible_witness = tuple(subset)
        else:
            incompatible_count += 1
            if incompatible_witness is None:
                incompatible_witness = tuple(subset)

    both = compatible_count > 0 and incompatible_count > 0
    payload = {
        "node_count": n,
        "positive_count": count,
        "compatible_configuration_count": compatible_count,
        "incompatible_configuration_count": incompatible_count,
        "total_configuration_count": total,
        "compatible_witness": (
            None if compatible_witness is None else list(compatible_witness)
        ),
        "incompatible_witness": (
            None if incompatible_witness is None else list(incompatible_witness)
        ),
        "both_outcomes_possible": both,
    }
    return PositiveSetCardinalityAudit(
        node_count=n,
        positive_count=count,
        compatible_configuration_count=compatible_count,
        incompatible_configuration_count=incompatible_count,
        total_configuration_count=total,
        compatible_witness=compatible_witness,
        incompatible_witness=incompatible_witness,
        both_outcomes_possible=both,
        fingerprint=_canonical_sha256(payload),
    )
