"""Canonical persistence contract for ordered Layer-A world-set trajectories.

Predictive endpoint certificates must not preserve only the final score.  This module
records the exact declared worlds, per-context surviving identities, elimination events,
and whether contraction occurred before the frozen calibration/heldout boundary.  It is
response-agnostic once the surviving sets have been produced by the endpoint runner.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence


def _clean_unique(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values)
    if not result or any(not value for value in result):
        raise ValueError(f"{label} must contain non-empty values")
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must contain unique values")
    return result


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class LayerATrajectoryCertificate:
    declared_world_ids: tuple[str, ...]
    context_ids: tuple[str, ...]
    surviving_world_ids: tuple[tuple[str, ...], ...]
    surviving_world_counts: tuple[int, ...]
    contraction_event_count: int
    calibration_contraction_event_count: int
    elimination_events: tuple[tuple[str, tuple[str, ...]], ...]
    final_surviving_world_ids: tuple[str, ...]
    terminal_universe_falsified: bool
    calibration_ever_contracted: bool
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "eog.layer_a_trajectory_certificate.v1",
            "declared_world_ids": list(self.declared_world_ids),
            "context_ids": list(self.context_ids),
            "surviving_world_ids": [list(values) for values in self.surviving_world_ids],
            "surviving_world_counts": list(self.surviving_world_counts),
            "contraction_event_count": self.contraction_event_count,
            "calibration_contraction_event_count": self.calibration_contraction_event_count,
            "elimination_events": [
                {"context_id": context_id, "eliminated_world_ids": list(world_ids)}
                for context_id, world_ids in self.elimination_events
            ],
            "final_surviving_world_ids": list(self.final_surviving_world_ids),
            "terminal_universe_falsified": self.terminal_universe_falsified,
            "calibration_ever_contracted": self.calibration_ever_contracted,
            "fingerprint": self.fingerprint,
        }


def certify_layer_a_trajectory(
    *,
    declared_world_ids: Sequence[str],
    context_ids: Sequence[str],
    surviving_world_ids_by_context: Sequence[Sequence[str]],
    calibration_context_count: int,
) -> LayerATrajectoryCertificate:
    """Validate and fingerprint an exact monotone Layer-A trajectory.

    ``surviving_world_ids_by_context[i]`` is the exact world set exposed for context i
    before the current-context outcome update, matching EOG's prospective forecast
    semantics. Empty sets are allowed only as a terminal state; once empty, all later
    states must remain empty. Eliminated worlds may never return.
    """

    declared = _clean_unique(declared_world_ids, "declared_world_ids")
    contexts = _clean_unique(context_ids, "context_ids")
    if len(contexts) != len(surviving_world_ids_by_context):
        raise ValueError("context_ids and surviving_world_ids_by_context must have equal length")
    calibration_n = int(calibration_context_count)
    if calibration_n <= 0 or calibration_n > len(contexts):
        raise ValueError("calibration_context_count must lie in [1, context_count]")

    declared_set = set(declared)
    states: list[tuple[str, ...]] = []
    previous = set(declared)
    eliminations: list[tuple[str, tuple[str, ...]]] = []
    contraction_count = 0
    calibration_contraction_count = 0

    for index, (context_id, raw_state) in enumerate(zip(contexts, surviving_world_ids_by_context, strict=True)):
        state = tuple(str(value).strip() for value in raw_state)
        if any(not value for value in state) or len(set(state)) != len(state):
            raise ValueError("each surviving world state must contain unique non-empty IDs")
        state_set = set(state)
        if not state_set <= declared_set:
            raise ValueError("surviving state contains world outside declared universe")
        if not state_set <= previous:
            raise ValueError("Layer-A trajectory is not monotone: an eliminated world returned")
        ordered_state = tuple(world_id for world_id in declared if world_id in state_set)
        eliminated = tuple(world_id for world_id in declared if world_id in previous and world_id not in state_set)
        if eliminated:
            contraction_count += 1
            if index < calibration_n:
                calibration_contraction_count += 1
            eliminations.append((context_id, eliminated))
        states.append(ordered_state)
        previous = state_set

    counts = tuple(len(state) for state in states)
    final_state = states[-1]
    payload = {
        "declared_world_ids": list(declared),
        "context_ids": list(contexts),
        "surviving_world_ids": [list(state) for state in states],
        "surviving_world_counts": list(counts),
        "calibration_context_count": calibration_n,
        "elimination_events": [
            [context_id, list(world_ids)] for context_id, world_ids in eliminations
        ],
    }
    return LayerATrajectoryCertificate(
        declared_world_ids=declared,
        context_ids=contexts,
        surviving_world_ids=tuple(states),
        surviving_world_counts=counts,
        contraction_event_count=contraction_count,
        calibration_contraction_event_count=calibration_contraction_count,
        elimination_events=tuple(eliminations),
        final_surviving_world_ids=final_state,
        terminal_universe_falsified=len(final_state) == 0,
        calibration_ever_contracted=calibration_contraction_count > 0,
        fingerprint=_sha256(payload),
    )
