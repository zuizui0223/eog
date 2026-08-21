"""Response-blind temporal source/process closure validation.

This module is validation infrastructure, not an ecological movement operator. It asks a
necessary-condition question before outcome access:

    can at least one possible source state be propagated through every declared time
    transition under the already-frozen source, availability, and transition rules?

A STOP falsifies that declared source/process explanation without inspecting response
values. A PASS only means the explanation is structurally/temporally admissible; it does
not establish biological occupancy, dispersal, or historical truth.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

import numpy as np


TemporalSourceClosureStatus = Literal[
    "temporal_source_closure_pass",
    "stop_temporal_source_closure_gap",
]


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _clean_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _require_bool_vector(value: object, *, length: int, label: str) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype != np.bool_:
        raise TypeError(f"{label} must have boolean dtype")
    if array.shape != (length,):
        raise ValueError(f"{label} must have shape ({length},)")
    return np.ascontiguousarray(array, dtype=bool)


def _require_bool_matrix(
    value: object,
    *,
    shape: tuple[int, int],
    label: str,
) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype != np.bool_:
        raise TypeError(f"{label} must have boolean dtype")
    if array.shape != shape:
        raise ValueError(f"{label} must have shape {shape}")
    return np.ascontiguousarray(array, dtype=bool)


def _boolean_array_fingerprint(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array, dtype=np.uint8)
    return _canonical_sha256(
        {
            "shape": list(contiguous.shape),
            "sha256": hashlib.sha256(contiguous.tobytes(order="C")).hexdigest(),
        }
    )


@dataclass(frozen=True)
class TemporalSourceClosureDeclaration:
    """Prospective identity/meaning of one response-blind temporal closure audit."""

    closure_id: str
    source_semantics: str
    transition_semantics: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "closure_id", _clean_required(self.closure_id, "closure_id"))
        object.__setattr__(
            self,
            "source_semantics",
            _clean_required(self.source_semantics, "source_semantics"),
        )
        object.__setattr__(
            self,
            "transition_semantics",
            _clean_required(self.transition_semantics, "transition_semantics"),
        )

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "closure_id": self.closure_id,
                "source_semantics": self.source_semantics,
                "transition_semantics": self.transition_semantics,
            }
        )


@dataclass(frozen=True)
class TemporalSourceClosureTransition:
    transition_index: int
    possible_before_count: int
    persistence_count: int
    transition_target_count: int
    possible_after_count: int


@dataclass(frozen=True)
class TemporalSourceClosureResult:
    status: TemporalSourceClosureStatus
    passed: bool
    possible_source_counts: tuple[int, ...]
    first_empty_transition_zero_based: int | None
    final_possible_node_ids: tuple[str, ...]
    transitions: tuple[TemporalSourceClosureTransition, ...]
    declaration_fingerprint: str
    input_fingerprint: str
    reason: str
    fingerprint: str


def evaluate_temporal_source_closure(
    declaration: TemporalSourceClosureDeclaration,
    node_ids: Sequence[str],
    initial_possible_source: object,
    persistence_eligible: object,
    transition_target_eligible: object,
    transition_adjacency: object,
) -> TemporalSourceClosureResult:
    """Evaluate optimistic source continuity without opening response outcomes.

    Parameters
    ----------
    node_ids
        Frozen analysis-node order. IDs must be unique and non-empty.
    initial_possible_source
        Boolean vector of source states allowed at the first time slice.
    persistence_eligible
        Boolean ``(n_nodes, n_transitions)`` matrix. ``[i,t]`` means a source that is
        possible at node ``i`` at time ``t`` may persist at the same node at ``t+1``.
    transition_target_eligible
        Boolean ``(n_nodes, n_transitions)`` matrix. ``[j,t]`` means node ``j`` is
        eligible to become a target at transition ``t -> t+1`` under the frozen
        response-blind observation/process contract.
    transition_adjacency
        Boolean ``(n_nodes, n_nodes)`` matrix in **source-row, target-column** order.
        ``[i,j]`` permits the declared transition from current possible source ``i`` to
        target ``j``. Diagonal entries are allowed but same-node persistence is already
        represented explicitly by ``persistence_eligible``.

    Notes
    -----
    This gate is intentionally optimistic: every response-blind initial source and every
    allowed transition is admitted simultaneously. Therefore an empty possible-source
    set is a strong necessary-condition failure for the declared explanation. A non-empty
    set is not evidence that any particular source, transition, or history actually
    occurred.
    """

    if not isinstance(declaration, TemporalSourceClosureDeclaration):
        raise TypeError("declaration must be TemporalSourceClosureDeclaration")
    if isinstance(node_ids, (str, bytes)):
        raise TypeError("node_ids must be a sequence of strings")
    ids = tuple(node_ids)
    if not ids:
        raise ValueError("node_ids must contain at least one node")
    if not all(isinstance(value, str) for value in ids):
        raise TypeError("node_ids must contain only strings")
    ids = tuple(value.strip() for value in ids)
    if any(not value for value in ids):
        raise ValueError("node_ids must not contain empty values")
    if len(set(ids)) != len(ids):
        raise ValueError("node_ids must be unique")

    n_nodes = len(ids)
    initial = _require_bool_vector(
        initial_possible_source,
        length=n_nodes,
        label="initial_possible_source",
    )

    persistence_raw = np.asarray(persistence_eligible)
    target_raw = np.asarray(transition_target_eligible)
    if persistence_raw.ndim != 2:
        raise ValueError("persistence_eligible must be a 2D boolean matrix")
    if target_raw.ndim != 2:
        raise ValueError("transition_target_eligible must be a 2D boolean matrix")
    if persistence_raw.shape[0] != n_nodes:
        raise ValueError("persistence_eligible first dimension must equal len(node_ids)")
    n_transitions = int(persistence_raw.shape[1])
    if n_transitions < 1:
        raise ValueError("temporal source closure requires at least one transition")

    persistence = _require_bool_matrix(
        persistence_eligible,
        shape=(n_nodes, n_transitions),
        label="persistence_eligible",
    )
    target_eligible = _require_bool_matrix(
        transition_target_eligible,
        shape=(n_nodes, n_transitions),
        label="transition_target_eligible",
    )
    adjacency = _require_bool_matrix(
        transition_adjacency,
        shape=(n_nodes, n_nodes),
        label="transition_adjacency",
    )

    input_payload = {
        "node_ids": list(ids),
        "initial_possible_source": _boolean_array_fingerprint(initial),
        "persistence_eligible": _boolean_array_fingerprint(persistence),
        "transition_target_eligible": _boolean_array_fingerprint(target_eligible),
        "transition_adjacency": _boolean_array_fingerprint(adjacency),
    }
    input_fingerprint = _canonical_sha256(input_payload)

    current = initial.copy()
    counts = [int(np.sum(current))]
    transitions: list[TemporalSourceClosureTransition] = []
    first_empty: int | None = None

    for transition_index in range(n_transitions):
        persistent = current & persistence[:, transition_index]
        if np.any(current):
            reachable_targets = np.any(adjacency[current, :], axis=0)
        else:
            reachable_targets = np.zeros(n_nodes, dtype=bool)
        transition_targets = (
            target_eligible[:, transition_index]
            & reachable_targets
        )
        next_possible = persistent | transition_targets

        transitions.append(
            TemporalSourceClosureTransition(
                transition_index=transition_index,
                possible_before_count=int(np.sum(current)),
                persistence_count=int(np.sum(persistent)),
                transition_target_count=int(np.sum(transition_targets)),
                possible_after_count=int(np.sum(next_possible)),
            )
        )
        current = next_possible
        counts.append(int(np.sum(current)))
        if first_empty is None and not np.any(current):
            first_empty = transition_index

    passed = first_empty is None
    status: TemporalSourceClosureStatus = (
        "temporal_source_closure_pass"
        if passed
        else "stop_temporal_source_closure_gap"
    )
    if passed:
        reason = (
            "at least one response-blind possible source state remains after every "
            "declared transition; this is a necessary-condition pass, not evidence of "
            "actual occupancy, dispersal, or history"
        )
    else:
        reason = (
            "the optimistic response-blind possible-source set becomes empty under the "
            "declared source/transition contract, so that explanation is structurally "
            "incompatible before outcome access"
        )

    final_ids = tuple(ids[index] for index in np.flatnonzero(current))
    payload = {
        "status": status,
        "passed": passed,
        "possible_source_counts": counts,
        "first_empty_transition_zero_based": first_empty,
        "final_possible_node_ids": list(final_ids),
        "transitions": [
            {
                "transition_index": row.transition_index,
                "possible_before_count": row.possible_before_count,
                "persistence_count": row.persistence_count,
                "transition_target_count": row.transition_target_count,
                "possible_after_count": row.possible_after_count,
            }
            for row in transitions
        ],
        "declaration_fingerprint": declaration.fingerprint,
        "input_fingerprint": input_fingerprint,
        "reason": reason,
    }
    return TemporalSourceClosureResult(
        status=status,
        passed=passed,
        possible_source_counts=tuple(counts),
        first_empty_transition_zero_based=first_empty,
        final_possible_node_ids=final_ids,
        transitions=tuple(transitions),
        declaration_fingerprint=declaration.fingerprint,
        input_fingerprint=input_fingerprint,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
